import os
import logging
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from chat_agent import LookerChatAgent

# Set up Java environment for JDBC driver
os.environ['JAVA_HOME'] = '/nix/store/1jm9fvrqrry22z9kgqa0v55nnz0jsk09-openjdk-11.0.23+9/lib/openjdk'

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for all domains (needed for embeddable widget)
CORS(app, 
     supports_credentials=True,
     origins='*',
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'])

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///chatbot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the chatbot.'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Initialize chat agent (will be None if credentials not available)
chat_agent = None

def get_or_create_agent():
    """Get existing agent or create new one if credentials are available"""
    global chat_agent
    
    # Get credentials from current user if logged in
    if current_user.is_authenticated:
        user_creds = {
            'LOOKER_BASE_URL': current_user.looker_base_url,
            'LOOKER_CLIENT_ID': current_user.looker_client_id,
            'LOOKER_CLIENT_SECRET': current_user.looker_client_secret,
            'OPENAI_API_KEY': current_user.openai_api_key,
            'LOOKML_MODEL_NAME': current_user.lookml_model_name
        }
        
        # Check if user has all required credentials
        missing_creds = [key for key, value in user_creds.items() if not value]
        if missing_creds:
            app.logger.warning(f"User missing credentials: {missing_creds}")
            return None
        
        # Set environment variables temporarily for agent creation
        original_env = {}
        for key, value in user_creds.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        # Set JDBC driver path
        os.environ['JDBC_DRIVER_PATH'] = '/home/runner/workspace/drivers/looker-jdbc.jar'
        
        try:
            chat_agent = LookerChatAgent()
            return chat_agent
        except Exception as e:
            app.logger.warning(f"Could not initialize chat agent: {e}")
            return None
        finally:
            # Restore original environment
            for key, original_value in original_env.items():
                if original_value is not None:
                    os.environ[key] = original_value
                elif key in os.environ:
                    del os.environ[key]
    
    # Fallback to environment variables if no user is logged in
    required_vars = ['LOOKER_BASE_URL', 'LOOKER_CLIENT_ID', 'LOOKER_CLIENT_SECRET', 'OPENAI_API_KEY', 'LOOKML_MODEL_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        app.logger.warning(f"Missing required environment variables: {missing_vars}")
        return None
    
    try:
        chat_agent = LookerChatAgent()
        return chat_agent
    except Exception as e:
        app.logger.warning(f"Could not initialize chat agent: {e}")
        return None

@app.route('/')
@login_required
def index():
    """Demo page showing the chatbot widget"""
    return render_template('index.html')

@app.route('/widget')
@login_required
def widget():
    """Standalone widget template"""
    return render_template('widget.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        from models import User
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'message': 'Login successful'})
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        from models import User
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Email already exists'}), 400
            flash('Email already exists')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        if request.is_json:
            return jsonify({'success': True, 'message': 'Registration successful'})
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'username': current_user.username if current_user.is_authenticated else None
    })

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    from models import User
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """API register endpoint"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    from models import User
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already exists'}), 400
    
    # Create new user
    user = User()
    user.username = username
    user.email = email
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return jsonify({'success': True, 'message': 'Registration successful'})

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """API logout endpoint"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages and return responses from Looker agent"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Initialize chat history in session if not exists
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        # Get response from Looker agent
        try:
            agent = get_or_create_agent()
            if agent is None:
                return jsonify({
                    'error': 'Looker configuration not available. Please configure your credentials in settings.',
                    'status': 'error'
                }), 400
            
            response = agent.get_response(user_message, session['chat_history'])
            
            # Add to chat history
            session['chat_history'].append({
                'user': user_message,
                'assistant': response
            })
            
            # Keep only last 10 exchanges to prevent session bloat
            if len(session['chat_history']) > 10:
                session['chat_history'] = session['chat_history'][-10:]
            
            session.modified = True
            
            return jsonify({
                'response': response,
                'status': 'success'
            })
            
        except Exception as agent_error:
            app.logger.error(f"Looker agent error: {str(agent_error)}")
            return jsonify({
                'error': 'I apologize, but I encountered an issue accessing the data. Please check your Looker configuration or try again later.',
                'status': 'error'
            }), 500
    
    except Exception as e:
        app.logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred. Please try again.',
            'status': 'error'
        }), 500

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    try:
        session['chat_history'] = []
        session.modified = True
        return jsonify({'status': 'success', 'message': 'Chat history cleared'})
    except Exception as e:
        app.logger.error(f"Clear chat error: {str(e)}")
        return jsonify({'error': 'Failed to clear chat history'}), 500

@app.route('/api/settings', methods=['POST'])
@login_required
def save_settings():
    """Save Looker configuration settings to user profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No settings data provided'}), 400
        
        # Update user's credentials in database
        if data.get('lookerBaseUrl'):
            current_user.looker_base_url = data['lookerBaseUrl']
        if data.get('lookerClientId'):
            current_user.looker_client_id = data['lookerClientId']
        if data.get('lookerClientSecret'):
            current_user.looker_client_secret = data['lookerClientSecret']
        if data.get('openaiApiKey'):
            current_user.openai_api_key = data['openaiApiKey']
        if data.get('lookmlModelName'):
            current_user.lookml_model_name = data['lookmlModelName']
        
        # Save to database
        db.session.commit()
        
        # Reinitialize the chat agent with new settings
        global chat_agent
        try:
            chat_agent = get_or_create_agent()
            app.logger.info("Chat agent reinitialized with new user settings")
        except Exception as e:
            app.logger.warning(f"Failed to reinitialize chat agent: {e}")
            chat_agent = None
        
        return jsonify({'status': 'success', 'message': 'Settings saved successfully'})
        
    except Exception as e:
        app.logger.error(f"Settings save error: {str(e)}")
        return jsonify({'error': 'Failed to save settings'}), 500

@app.route('/api/get-settings', methods=['GET'])
@login_required
def get_settings():
    """Get current settings from user profile"""
    try:
        settings = {
            'lookerBaseUrl': current_user.looker_base_url or '',
            'lookerClientId': current_user.looker_client_id or '',
            'lookerClientSecret': '***' if current_user.looker_client_secret else '',
            'openaiApiKey': '***' if current_user.openai_api_key else '',
            'lookmlModelName': current_user.lookml_model_name or ''
        }
        return jsonify(settings)
    except Exception as e:
        app.logger.error(f"Get settings error: {str(e)}")
        return jsonify({'error': 'Failed to get settings'}), 500

@app.route('/api/test-connection', methods=['POST'])
@login_required
def test_connection():
    """Test the Looker connection"""
    try:
        agent = get_or_create_agent()
        if agent is None:
            return jsonify({'success': False, 'error': 'No agent available - check your credentials'})
        
        if agent.test_connection():
            return jsonify({'success': True, 'message': 'Connection successful'})
        else:
            return jsonify({'success': False, 'error': 'Connection failed - check your credentials'})
    except Exception as e:
        app.logger.error(f"Connection test error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'looker-chatbot'})

with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

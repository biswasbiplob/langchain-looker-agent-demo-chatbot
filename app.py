import os
import logging
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from chat_agent import LookerChatAgent

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
CORS(app, supports_credentials=True)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///chatbot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Initialize chat agent
chat_agent = LookerChatAgent()

@app.route('/')
def index():
    """Demo page showing the chatbot widget"""
    return render_template('index.html')

@app.route('/widget')
def widget():
    """Standalone widget template"""
    return render_template('widget.html')

@app.route('/api/chat', methods=['POST'])
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
            response = chat_agent.get_response(user_message, session['chat_history'])
            
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

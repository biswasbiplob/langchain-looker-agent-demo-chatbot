# Looker Data Analyst Chatbot

![Looker Data Analyst Chatbot](attached_assets/Screenshot%202025-06-01%20at%2021.33.44.png)

A conversational AI-powered data analyst chatbot that seamlessly integrates with Looker Business Intelligence platforms. Get instant insights from your data through natural language conversations that can be embedded on any website.

## 🚀 Features

### 💬 Natural Language Queries
Ask questions about your data in plain English without needing SQL knowledge. The AI understands context and provides meaningful insights.

**Example queries:**
- "What are our top 10 page titles on our website over the last 30 days?"
- "Show me sales trends by region"
- "What's our customer acquisition cost this quarter?"

### 🔗 Direct Looker BI Integration
- Real-time connection to your Looker platform
- Automatic schema discovery and query generation
- Secure authentication with your Looker credentials
- Support for complex analytical queries

### 🌐 Easy Website Embedding
- Simple JavaScript widget that works on any website
- Floating chat button with customizable positioning
- Responsive design that works on desktop and mobile
- Clean, modern interface with light/dark theme support

### 🔐 User Authentication & Settings
- Secure user registration and login system
- Per-user Looker configuration storage
- Settings panel for API key management
- Session-based chat history

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **AI/ML**: OpenAI GPT-4o, LangChain Looker Agent
- **Frontend**: Vanilla JavaScript, Bootstrap CSS
- **Authentication**: Flask-Login with secure password hashing
- **BI Integration**: Looker API with JDBC driver support

## 📋 Prerequisites

Before you begin, ensure you have:

1. **Looker BI Instance**: Access to a Looker platform with API credentials
2. **OpenAI API Key**: For natural language processing capabilities
3. **Python 3.8+**: For running the Flask backend
4. **PostgreSQL Database**: For storing user data and configurations

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/looker-data-analyst-chatbot.git
cd looker-data-analyst-chatbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/looker_chatbot

# Session Security
SESSION_SECRET=your-secure-session-secret

# Optional: Default Looker Configuration (users can override in settings)
LOOKER_BASE_URL=https://your-looker-instance.looker.com
LOOKER_CLIENT_ID=your_looker_client_id
LOOKER_CLIENT_SECRET=your_looker_client_secret
OPENAI_API_KEY=your_openai_api_key
LOOKML_MODEL_NAME=your_model_name

# JDBC Driver Path
JDBC_DRIVER_PATH=./drivers/looker-jdbc.jar
```

### 4. Initialize the Database

```bash
python -c "from app import db; db.create_all()"
```

### 5. Run the Application

```bash
python main.py
```

The application will be available at `http://localhost:5000`

## 🔧 Configuration

### Looker Setup

1. **Create API Credentials** in your Looker Admin panel:
   - Go to Admin → Users → API Keys
   - Generate a new API3 key pair
   - Note the Client ID and Client Secret

2. **Configure Permissions**:
   - Ensure your API user has access to the models you want to query
   - Grant necessary permissions for data exploration

### User Configuration

Users can configure their own Looker credentials through the settings panel:

1. Click the settings icon in the chat widget
2. Enter your Looker instance details:
   - Base URL (e.g., `https://company.looker.com`)
   - Client ID and Client Secret
   - OpenAI API Key
   - LookML Model Name
3. Test the connection to verify credentials

## 🌐 Website Integration

### Basic Integration

Add this code snippet to any webpage to embed the chatbot:

```html
<!-- CSS -->
<link rel="stylesheet" href="https://your-domain.com/static/widget.css">

<!-- JavaScript -->
<script src="https://your-domain.com/static/widget.js"></script>
<script>
  const chatWidget = new LookerChatWidget({
    apiBaseUrl: 'https://your-domain.com'
  });
</script>
```

**Important**: Replace `your-chatbot-server.replit.app` with the actual URL where your chatbot server is hosted. This should NOT be your website's domain unless you're hosting the chatbot there.

### Customization Options

```javascript
const chatWidget = new LookerChatWidget({
  apiBaseUrl: 'https://your-domain.com',
  position: 'bottom-right', // bottom-left, top-right, top-left
  theme: 'light', // light, dark
  primaryColor: '#6366F1',
  autoOpen: false
});
```

## 📝 API Endpoints

### Chat Endpoints
- `POST /api/chat` - Send message to chatbot
- `POST /api/chat/clear` - Clear chat history

### Authentication Endpoints  
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `GET /api/auth/status` - Check authentication status

### Configuration Endpoints
- `POST /api/settings` - Save user settings
- `GET /api/settings` - Get user settings  
- `POST /api/test-connection` - Test Looker connection

## 🔒 Security Features

- **Secure Password Storage**: Passwords are hashed using Werkzeug's secure methods
- **Session Management**: Flask-Login handles user sessions securely
- **API Key Encryption**: User API keys are stored securely in the database
- **CORS Configuration**: Proper CORS setup for cross-domain embedding
- **Input Validation**: All user inputs are validated and sanitized

## 🐛 Troubleshooting

### Common Issues

**404 Errors When Using Widget on External Website**
- The most common issue: Make sure the `apiBaseUrl` in your widget initialization points to your chatbot server, not your website
- Correct example: `apiBaseUrl: 'https://your-chatbot-server.replit.app'`
- Incorrect: `apiBaseUrl: 'https://your-website.com'` (unless the chatbot is hosted there)
- Check browser console for "404 Not Found" errors on `/api/chat` endpoint

**Connection Failed to Looker**
- Verify your Looker credentials in the settings panel
- Check that your Looker instance URL is correct
- Ensure your API user has proper permissions

**Chat Not Responding**
- Verify your OpenAI API key is valid and has sufficient credits
- Check the browser console for any JavaScript errors
- Ensure the backend server is running

**Widget Not Loading**
- Check that the CSS and JS files are accessible from your domain
- Verify CORS configuration allows your domain
- Check browser console for loading errors

### Debug Mode

Enable debug logging by setting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♀️ Support

For questions and support:

- Open an issue on GitHub
- Check the [Documentation](docs/)
- Review the troubleshooting section above

## 🚀 Deployment

### Replit Deployment

This project is optimized for Replit deployment:

1. Import the repository to Replit
2. Configure environment variables in the Secrets tab
3. Run the project - it will automatically start on port 5000
4. Use the generated Replit URL for widget integration

### Production Deployment

For production environments:

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Set up proper SSL/TLS certificates
3. Configure a reverse proxy (Nginx, Apache)
4. Use environment-specific configuration files
5. Set up monitoring and logging

---

**Built with ❤️ using Looker BI, LangChain, and Flask**
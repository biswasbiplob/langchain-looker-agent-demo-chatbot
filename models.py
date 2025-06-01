from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Looker credentials stored per user
    looker_base_url = db.Column(db.String(255))
    looker_client_id = db.Column(db.String(255))
    looker_client_secret = db.Column(db.Text)
    openai_api_key = db.Column(db.Text)
    lookml_model_name = db.Column(db.String(100))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class ChatSession(db.Model):
    """Model to store chat sessions for analytics"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(128), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    assistant_response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    response_time_ms = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<ChatSession {self.id}: {self.user_message[:50]}...>'


class ChatError(db.Model):
    """Model to log chat errors for monitoring"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(128), nullable=False)
    error_message = db.Column(db.Text, nullable=False)
    user_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatError {self.id}: {self.error_message[:50]}...>'

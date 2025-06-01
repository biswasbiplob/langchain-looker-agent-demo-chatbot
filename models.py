from app import db
from datetime import datetime

class ChatSession(db.Model):
    """Model to store chat sessions for analytics"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    assistant_response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    response_time_ms = db.Column(db.Integer)  # Response time in milliseconds
    
    def __repr__(self):
        return f'<ChatSession {self.id}: {self.user_message[:50]}...>'

class ChatError(db.Model):
    """Model to log chat errors for monitoring"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), nullable=False)
    error_message = db.Column(db.Text, nullable=False)
    user_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatError {self.id}: {self.error_message[:50]}...>'

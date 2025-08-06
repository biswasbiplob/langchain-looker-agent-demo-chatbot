from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSON


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


class LookerModel(db.Model):
    """Model to cache Looker models information"""
    id = db.Column(db.Integer, primary_key=True)
    looker_instance_id = db.Column(db.String(255), nullable=False)  # Hash of looker_base_url
    model_name = db.Column(db.String(255), nullable=False)
    project_name = db.Column(db.String(255))
    label = db.Column(db.String(255))
    description = db.Column(db.Text)
    model_metadata = db.Column(JSON)  # Store full model data as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint for instance + model
    __table_args__ = (db.UniqueConstraint('looker_instance_id', 'model_name'),)
    
    def __repr__(self):
        return f'<LookerModel {self.model_name}>'


class LookerExplore(db.Model):
    """Model to cache Looker explores information"""
    id = db.Column(db.Integer, primary_key=True)
    looker_instance_id = db.Column(db.String(255), nullable=False)  # Hash of looker_base_url
    model_name = db.Column(db.String(255), nullable=False)
    explore_name = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(255))
    description = db.Column(db.Text)
    dimensions = db.Column(JSON)  # Store dimensions as JSON array
    measures = db.Column(JSON)    # Store measures as JSON array
    explore_metadata = db.Column(JSON)  # Store full explore data as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint for instance + model + explore
    __table_args__ = (db.UniqueConstraint('looker_instance_id', 'model_name', 'explore_name'),)
    
    def __repr__(self):
        return f'<LookerExplore {self.model_name}.{self.explore_name}>'


class LookerDashboard(db.Model):
    """Model to cache Looker dashboard information with business context"""
    id = db.Column(db.Integer, primary_key=True)
    looker_instance_id = db.Column(db.String(255), nullable=False)  # Hash of looker_base_url
    dashboard_id = db.Column(db.String(255), nullable=False)  # Looker dashboard ID
    title = db.Column(db.String(500))  # Business-friendly dashboard title
    description = db.Column(db.Text)   # Business description (HIGH VALUE for matching)
    folder_name = db.Column(db.String(255))  # Business organization context
    tags = db.Column(JSON)             # Business categorization tags
    dashboard_elements = db.Column(JSON)  # Tiles, queries, filters
    explore_references = db.Column(JSON)  # List of model.explore pairs used in dashboard
    lookml_references = db.Column(JSON)   # Detailed LookML usage context
    user_access_count = db.Column(db.Integer, default=0)  # Popularity indicator
    last_viewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint for instance + dashboard
    __table_args__ = (db.UniqueConstraint('looker_instance_id', 'dashboard_id'),)
    
    def __repr__(self):
        return f'<LookerDashboard {self.dashboard_id}: {self.title}>'


class DashboardExploreMapping(db.Model):
    """Model to track relationships between dashboards and explores for business context"""
    id = db.Column(db.Integer, primary_key=True)
    looker_instance_id = db.Column(db.String(255), nullable=False)
    dashboard_id = db.Column(db.String(255), nullable=False)
    model_name = db.Column(db.String(255), nullable=False)
    explore_name = db.Column(db.String(255), nullable=False)
    usage_count = db.Column(db.Integer, default=1)  # How many tiles use this explore
    business_context_score = db.Column(db.Float, default=1.0)  # Calculated relevance score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('looker_instance_id', 'dashboard_id', 'model_name', 'explore_name'),)
    
    def __repr__(self):
        return f'<DashboardExploreMapping {self.dashboard_id} -> {self.model_name}.{self.explore_name}>'

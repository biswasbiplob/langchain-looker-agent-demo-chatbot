#!/usr/bin/env python3
"""
Test script to verify database table creation with new caching models
"""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
import models  # Import all models

with app.app_context():
    try:
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # List all tables
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📋 Tables created: {', '.join(tables)}")
        
        # Check if our new caching tables are there
        expected_tables = ['looker_model', 'looker_explore']
        for table in expected_tables:
            if table in tables:
                print(f"✅ {table} table created successfully")
            else:
                print(f"❌ {table} table missing")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        import traceback
        traceback.print_exc()
#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import app

# Production configuration
app.config.update(
    DEBUG=False,
    TESTING=False,
    SECRET_KEY=os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production'),
    # Add any other production-specific configurations
)

if __name__ == "__main__":
    # This will only run if the script is executed directly
    # In production, this should be served via WSGI server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
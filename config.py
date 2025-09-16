"""
Configuration management for Employee Recommendation System.
"""
import os
from typing import Dict, Any

class Config:
    """Base configuration class."""

    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']

    # Model configuration
    MODEL_PATH = os.environ.get('MODEL_PATH', 'models/sim_final.pkl')
    DATA_PATH = os.environ.get('DATA_PATH', 'Filtered01.json')

    # API configuration
    MAX_RECOMMENDATIONS = int(os.environ.get('MAX_RECOMMENDATIONS', '3'))

    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')

    # Text processing configuration
    SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', '0.1'))

    # Skills processing
    TECH_TERMS = [
        'python', 'r', 'sql', 'hadoop', 'spark', 'java', 'sas', 'tableau', 'mysql',
        'hive', 'scala', 'aws', 'c', 'c++', 'matlab', 'tensorflow', 'excel', 'angular',
        'nosql', 'linux', 'azure', 'scikit', 'machine learning', 'statistics',
        'analysis', 'computer science', 'visual', 'ai', 'artificial intelligence',
        'deep learning', 'mongodb', 'nlp', 'natural language processing',
        'neural network', 'mathematics', 'database', 'oop', 'blockchain', 'cloud',
        'bootstrap', 'unix', 'agile', 'html', 'css', 'javascript', 'jquery', 'git',
        'photoshop', 'illustrator', 'wordpress', 'seo', 'responsive design', 'php',
        'mobile', 'design', 'react', 'security', 'ruby', 'fireworks', 'json', 'node',
        'express', 'redux', 'ajax', 'api', 'ios', 'big data', 'adobe', 'assembly',
        'wireframe', 'couchdb', 'ui prototype', 'ux writing', 'interactive design',
        'iot', 'ruby on rails', 'metric', 'analytics', 'ux research', 'mockup', 'c#',
        'web development', 'prototype', 'test', 'ideate', 'usability',
        'high-fidelity design', 'karma', 'framework', 'testing', 'xml', 'oracle',
        'node.js', 'scrum', 'uml', 'database management', 'autocad', 'swift', 'xcode',
        'spatial reasoning', 'human interface', 'core data', 'grand central', 'network',
        'objective-c', 'foundation', 'uikit', 'asp.net', 'cocoatouch', 'spritekit',
        'scenekit', 'opengl', 'metal', 'data engineering', 'dreamweaver',
        'statistical analysis', 'coding', 'basic', 'logic', 'docker', 'ms access',
        'computer vision', 'html5', 'sed', 'abap'
    ]

    # Degree types for standardization
    DEGREE_TYPES = [
        'computer', 'data', 'science', 'information', 'technology', 'architecture',
        'management', 'electrical', 'business', 'administration', 'engineering',
        'analytics', 'application', 'computing', 'digital', 'marketing',
        'food', 'beverage', 'chemistry', 'health', 'statistics',
        'analysis', 'mechanical', 'accounting', 'mathematics', 'electronics',
        'telecommunication', 'property', 'marine', 'chemical', 'construction',
        'arts', 'law', 'legal', 'network', 'media', 'security',
        'education', 'project', 'system', 'anthropology', 'sociology', 'design',
        'aviation', 'state', 'economics', 'physics', 'industrial', 'human',
        'commerce', 'psychology', 'software', 'translation'
    ]

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True

# Configuration mapping
config_map: Dict[str, Any] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: str = None) -> Config:
    """Get configuration based on environment."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    return config_map.get(config_name, DevelopmentConfig)
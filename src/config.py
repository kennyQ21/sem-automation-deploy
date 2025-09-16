"""
Environment configuration for the SEM automation system.
"""
import os
from dotenv import load_dotenv

def load_config() -> dict[str, str]:
    """Load environment configuration from the .env file."""
    load_dotenv()
    
    # Required variables for the application
    required_vars = [
        'OPENAI_API_KEY',
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'GOOGLE_ADS_CONFIG_PATH'
    ]
    
    # Optional variables
    optional_vars = ['DATABASE_URL']
    
    config = {}
    missing = []
    
    # Load required variables
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            config[var.lower()] = value
    
    # Load optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            config[var.lower()] = value
        
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    # Use SQLite if no DATABASE_URL provided
    if 'database_url' not in config:
        config['database_url'] = 'sqlite:///sem_automation.db'
    
    # Add optional configuration for API optimization
    config['enable_ai_cache'] = os.getenv('ENABLE_AI_CACHE', 'true').lower() == 'true'
    config['max_keywords_per_batch'] = int(os.getenv('MAX_KEYWORDS_PER_BATCH', '10'))
    config['use_fallback_naming'] = os.getenv('USE_FALLBACK_NAMING', 'true').lower() == 'true'
        
    return config
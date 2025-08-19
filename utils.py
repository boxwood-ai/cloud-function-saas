"""
Utility functions for the Cloud Function Generator
"""

import os
import re
import subprocess
import logging
import stat
import anthropic
from typing import Tuple, List


def sanitize_secrets(text: str) -> str:
    """Remove common secrets and sensitive information from text"""
    
    # Common secret patterns to redact
    patterns = [
        # API keys and tokens
        (r'["\s=](sk-[a-zA-Z0-9]{48})', r'\1[REDACTED-API-KEY]'),
        (r'["\s=](xoxb-[a-zA-Z0-9-]{50,})', r'\1[REDACTED-SLACK-TOKEN]'),
        (r'["\s=]([A-Za-z0-9]{32,})', r'\1[REDACTED-TOKEN]'),
        # Environment variables that might contain secrets
        (r'(API_KEY[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(SECRET[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(PASSWORD[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(TOKEN[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        # JWT tokens
        (r'(eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)', r'[REDACTED-JWT]'),
        # URLs with credentials
        (r'(https?://[^:]+:)[^@]+(@)', r'\1[REDACTED]\2'),
    ]
    
    sanitized = text
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized


def setup_logging(output_dir: str, debug: bool = False) -> logging.Logger:
    """Setup logging to both console and file"""
    # Create logger
    logger = logging.getLogger('cloud_function_generator')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create log file path
    log_file = os.path.join(output_dir, 'generation.log')
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # File handler - detailed logging with restricted permissions
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Set restrictive permissions on log file (600 - owner only)
    try:
        os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR)  # 600 permissions
    except Exception:
        pass  # Continue if chmod fails
    
    # Console handler - only if debug mode
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    logger.info("=" * 60)
    logger.info("Cloud Function Generator - Session Started")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Debug mode: {debug}")
    logger.info("=" * 60)
    
    return logger


def validate_configuration() -> Tuple[List[str], List[str]]:
    """Validate required configuration and environment setup"""
    errors = []
    warnings = []
    
    # Check for required environment variables
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        errors.append("ANTHROPIC_API_KEY is required. Set it in .env or environment variables.")
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        warnings.append("GOOGLE_CLOUD_PROJECT not set in .env. You'll need to specify --project flag.")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        warnings.append(".env file not found. Using environment variables and defaults.")
    
    # Check if gcloud CLI is available
    try:
        subprocess.run(['gcloud', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        errors.append("Google Cloud SDK (gcloud) is not installed or not in PATH. Please install it first.")
    
    # Check if gcloud is authenticated
    try:
        result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE'], 
                              capture_output=True, text=True, check=True)
        if 'ACTIVE' not in result.stdout:
            errors.append("No active Google Cloud authentication found. Run 'gcloud auth login' first.")
    except subprocess.CalledProcessError:
        errors.append("Unable to check Google Cloud authentication status.")
    
    # Test Anthropic API connection if key is available
    if api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            # Test with minimal request
            client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
        except anthropic.AuthenticationError:
            errors.append("Invalid ANTHROPIC_API_KEY. Please check your API key.")
        except anthropic.PermissionDeniedError:
            errors.append("Anthropic API key doesn't have permission to use Claude models.")
        except Exception as e:
            warnings.append(f"Unable to verify Anthropic API connection: {str(e)}")
    
    return errors, warnings
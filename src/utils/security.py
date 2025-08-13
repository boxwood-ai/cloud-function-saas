"""
Security utilities for sanitizing secrets and sensitive information.
"""
import re
from typing import List, Tuple


def sanitize_secrets(text: str) -> str:
    """Remove common secrets and sensitive information from text"""
    if not text:
        return text
    
    # Common secret patterns to redact
    patterns = [
        # API keys and tokens
        (r'["\s=](sk-[a-zA-Z0-9]{48})', r'[REDACTED-API-KEY]'),
        (r'["\s=](xoxb-[a-zA-Z0-9-]{50,})', r'[REDACTED-SLACK-TOKEN]'),
        (r'["\s=]([A-Za-z0-9]{32,})', r'[REDACTED-TOKEN]'),
        
        # Environment variables that might contain secrets
        (r'(API_KEY[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(SECRET[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(PASSWORD[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(TOKEN[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        
        # JWT tokens
        (r'(eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)', r'[REDACTED-JWT]'),
        
        # URLs with credentials
        (r'(https?://[^:]+:)[^@]+(@)', r'\1[REDACTED]\2'),
        
        # Database connection strings
        (r'(postgres://[^:]+:)[^@]+(@)', r'\1[REDACTED]\2'),
        (r'(mysql://[^:]+:)[^@]+(@)', r'\1[REDACTED]\2'),
        
        # Docker registry credentials
        (r'("auth"\s*:\s*")[^"]+(")', r'\1[REDACTED]\2'),
        
        # Common cloud provider keys
        (r'(GOOGLE_APPLICATION_CREDENTIALS[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(AWS_ACCESS_KEY_ID[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(AWS_SECRET_ACCESS_KEY[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(AZURE_CLIENT_SECRET[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
    ]
    
    sanitized = text
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized


def validate_input_safety(input_string: str) -> List[str]:
    """Validate input for potential security issues"""
    issues = []
    
    # Check for path traversal
    if '../' in input_string or '..\\' in input_string:
        issues.append("Potential path traversal detected")
    
    # Check for command injection patterns
    dangerous_chars = [';', '|', '&', '$', '`', '$(', '${']
    for char in dangerous_chars:
        if char in input_string:
            issues.append(f"Potentially dangerous character '{char}' found")
            break
    
    # Check for script tags (basic XSS)
    if re.search(r'<script[^>]*>.*?</script>', input_string, re.IGNORECASE | re.DOTALL):
        issues.append("Script tag detected")
    
    return issues


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    # Remove path separators and traversal attempts
    sanitized = filename.replace('/', '_').replace('\\', '_')
    sanitized = sanitized.replace('..', '_')
    
    # Remove or replace other problematic characters
    sanitized = re.sub(r'[<>:"|?*]', '_', sanitized)
    
    # Ensure it's not empty
    if not sanitized or sanitized.isspace():
        sanitized = 'unnamed_file'
    
    return sanitized


def is_safe_project_id(project_id: str) -> bool:
    """Check if a project ID is in valid format (no injection risks)"""
    # GCP project IDs must be 6-30 characters, lowercase letters, digits, and hyphens
    pattern = r'^[a-z0-9-]{6,30}$'
    if not re.match(pattern, project_id):
        return False
    
    # Cannot start or end with hyphen
    if project_id.startswith('-') or project_id.endswith('-'):
        return False
    
    return True


def is_safe_service_name(service_name: str) -> bool:
    """Check if a service name is safe for deployment"""
    # Cloud Run service names: lowercase letters, digits, and hyphens
    pattern = r'^[a-z0-9-]+$'
    if not re.match(pattern, service_name):
        return False
    
    # Cannot start with hyphen
    if service_name.startswith('-'):
        return False
    
    # Reasonable length limits
    if len(service_name) < 1 or len(service_name) > 63:
        return False
    
    return True
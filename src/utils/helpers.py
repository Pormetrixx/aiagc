"""
Utility functions
"""

import re
from typing import Optional
from loguru import logger
import phonenumbers


def normalize_phone_number(
    phone_number: str,
    country_code: str = "DE"
) -> Optional[str]:
    """
    Normalize phone number to E.164 format
    
    Args:
        phone_number: Phone number to normalize
        country_code: Default country code
        
    Returns:
        Normalized phone number or None if invalid
    """
    try:
        parsed = phonenumbers.parse(phone_number, country_code)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
    except Exception as e:
        logger.warning(f"Invalid phone number {phone_number}: {e}")
    
    return None


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string"""
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def extract_amount(text: str) -> Optional[float]:
    """
    Extract monetary amount from German text
    
    Args:
        text: Text containing amount
        
    Returns:
        Extracted amount or None
    """
    # Patterns for German number formats
    patterns = [
        r'(\d+\.?\d*)\s*(?:euro|eur|€)',
        r'(\d+\.?\d*)\s*(?:tausend|k)',
        r'(\d+\.?\d*)\s*(?:million|mio)',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount = float(match.group(1).replace('.', '').replace(',', '.'))
            
            # Apply multipliers
            if 'tausend' in match.group(0) or 'k' in match.group(0):
                amount *= 1000
            elif 'million' in match.group(0) or 'mio' in match.group(0):
                amount *= 1000000
            
            return amount
    
    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    # Remove invalid characters
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    # Replace spaces with underscores
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.lower()


def mask_phone_number(phone_number: str) -> str:
    """Mask phone number for privacy (show only last 4 digits)"""
    if len(phone_number) <= 4:
        return phone_number
    return '*' * (len(phone_number) - 4) + phone_number[-4:]


def calculate_lead_score(
    has_investment_interest: bool,
    budget_available: bool,
    is_decision_maker: bool,
    positive_sentiment: bool,
    engagement_level: int
) -> int:
    """
    Calculate lead score based on qualification criteria
    
    Args:
        has_investment_interest: Interest in investment
        budget_available: Budget/capital available
        is_decision_maker: Is decision maker
        positive_sentiment: Positive sentiment in conversation
        engagement_level: Engagement level (0-10)
        
    Returns:
        Lead score (0-100)
    """
    score = 0
    
    # Core criteria (75 points total)
    if has_investment_interest:
        score += 30
    if budget_available:
        score += 25
    if is_decision_maker:
        score += 20
    
    # Sentiment (15 points)
    if positive_sentiment:
        score += 15
    
    # Engagement (10 points)
    score += min(10, engagement_level)
    
    return min(100, score)

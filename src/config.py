"""
AI Agent for Automated Outbound Calling (AIAGC)
Main configuration module
"""

import os
from typing import List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = "production"
    
    # Asterisk ARI
    asterisk_ari_host: str = "localhost"
    asterisk_ari_port: int = 8088
    asterisk_ari_username: str = "asterisk"
    asterisk_ari_password: str = ""
    asterisk_language: str = "de"
    
    # Legacy Asterisk AMI (for backwards compatibility)
    asterisk_host: str = "localhost"
    asterisk_port: int = 5038
    asterisk_username: str = "admin"
    asterisk_secret: str = ""
    asterisk_context: str = "outbound-calls"
    asterisk_caller_id: str = ""
    
    # Deepgram
    deepgram_api_key: str = ""
    deepgram_model: str = "nova-2"
    deepgram_language: str = "de"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    
    # Anthropic
    anthropic_api_key: str = ""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/aiagc_calls"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Call configuration
    max_call_duration: int = 600
    silence_timeout: int = 5
    speech_timeout: int = 10
    max_retries: int = 3
    
    # Lead scoring
    lead_score_threshold: int = 70
    qualification_criteria: str = "investment_interest,budget_available,decision_maker"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/aiagc.log"
    
    # Audio
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_format: str = "wav"
    
    # Security
    secret_key: str = ""
    api_token: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

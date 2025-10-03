"""
Call state model for tracking call progress
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CallState(str, Enum):
    """Call state enumeration"""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    IN_CONVERSATION = "in_conversation"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"


class IntentType(str, Enum):
    """Intent types for conversation analysis"""
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    REQUEST_INFO = "request_info"
    SCHEDULE_CALLBACK = "schedule_callback"
    TRANSFER_TO_AGENT = "transfer_to_agent"
    OBJECTION = "objection"
    QUESTION = "question"
    POSITIVE_SENTIMENT = "positive_sentiment"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    NEUTRAL = "neutral"


class LeadQualification(BaseModel):
    """Lead qualification data"""
    has_investment_interest: bool = False
    budget_available: bool = False
    is_decision_maker: bool = False
    timeline: Optional[str] = None
    investment_amount: Optional[float] = None
    preferred_product: Optional[str] = None
    contact_preference: Optional[str] = None
    notes: List[str] = Field(default_factory=list)


class CallRecord(BaseModel):
    """Call record model"""
    call_id: str
    phone_number: str
    caller_id: str
    state: CallState = CallState.INITIATED
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration: int = 0  # in seconds
    
    # Conversation data
    transcript: List[Dict[str, Any]] = Field(default_factory=list)
    detected_intents: List[IntentType] = Field(default_factory=list)
    sentiment_score: float = 0.0
    
    # Lead data
    qualification: LeadQualification = Field(default_factory=LeadQualification)
    lead_score: int = 0
    is_qualified: bool = False
    
    # Technical data
    audio_file: Optional[str] = None
    error_messages: List[str] = Field(default_factory=list)
    retry_count: int = 0
    
    class Config:
        use_enum_values = True


class ConversationTurn(BaseModel):
    """Single turn in a conversation"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker: str  # "agent" or "customer"
    text: str
    intent: Optional[IntentType] = None
    confidence: float = 0.0
    audio_duration: float = 0.0

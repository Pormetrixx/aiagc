"""
Call Flow State Machine
Manages the conversation flow and state transitions
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from loguru import logger
from datetime import datetime

from ..models.call_state import CallState, CallRecord, ConversationTurn, IntentType
from ..ai.intent_detector import IntentDetector
from .dialogue_generator import DialogueGenerator


class ConversationPhase(str, Enum):
    """Phases of the sales conversation"""
    OPENING = "opening"
    RAPPORT_BUILDING = "rapport_building"
    NEEDS_DISCOVERY = "needs_discovery"
    QUALIFICATION = "qualification"
    PRESENTATION = "presentation"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    CALLBACK_SCHEDULING = "callback_scheduling"
    ENDED = "ended"


class CallFlowManager:
    """Manages call flow logic and conversation state"""
    
    def __init__(
        self,
        intent_detector: IntentDetector,
        dialogue_generator: DialogueGenerator
    ):
        """
        Initialize call flow manager
        
        Args:
            intent_detector: Intent detection service
            dialogue_generator: Dialogue generation service
        """
        self.intent_detector = intent_detector
        self.dialogue_generator = dialogue_generator
        self.current_phase = ConversationPhase.OPENING
        self.turn_count = 0
        self.qualification_score = 0
        
    async def start_call(
        self,
        call_record: CallRecord,
        customer_name: Optional[str] = None
    ) -> str:
        """
        Start a new call
        
        Args:
            call_record: Call record to track
            customer_name: Optional customer name
            
        Returns:
            Opening statement
        """
        self.current_phase = ConversationPhase.OPENING
        self.turn_count = 0
        self.qualification_score = 0
        
        logger.info(f"Starting call {call_record.call_id}")
        
        # Generate opening
        opening = await self.dialogue_generator.generate_opening(
            customer_name=customer_name,
            campaign_type="investment"
        )
        
        # Record turn
        turn = ConversationTurn(
            speaker="agent",
            text=opening,
            intent=None,
            confidence=1.0
        )
        call_record.transcript.append(turn.dict())
        
        return opening
    
    async def process_customer_response(
        self,
        call_record: CallRecord,
        customer_text: str
    ) -> tuple[str, bool]:
        """
        Process customer response and generate agent reply
        
        Args:
            call_record: Current call record
            customer_text: What customer said
            
        Returns:
            Tuple of (agent_response, should_continue)
        """
        self.turn_count += 1
        
        # Record customer turn
        customer_turn = ConversationTurn(
            speaker="customer",
            text=customer_text,
            intent=None,
            confidence=0.0
        )
        
        # Detect intent
        conversation_history = [
            ConversationTurn(**turn) for turn in call_record.transcript
        ]
        
        intent_result = await self.intent_detector.detect_intent(
            customer_text,
            conversation_history
        )
        
        customer_turn.intent = IntentType(intent_result.get("intent", "neutral"))
        customer_turn.confidence = intent_result.get("confidence", 0.0)
        call_record.transcript.append(customer_turn.dict())
        
        # Update lead qualification
        self._update_qualification(call_record, intent_result)
        
        # Determine if call should continue
        should_continue = await self._should_continue_call(call_record, intent_result)
        
        # Generate appropriate response based on phase and intent
        agent_response = await self._generate_contextual_response(
            call_record,
            customer_text,
            intent_result,
            conversation_history
        )
        
        # Record agent turn
        agent_turn = ConversationTurn(
            speaker="agent",
            text=agent_response,
            intent=None,
            confidence=1.0
        )
        call_record.transcript.append(agent_turn.dict())
        
        # Update conversation phase
        self._update_phase(intent_result)
        
        logger.info(f"Call {call_record.call_id} - Phase: {self.current_phase}, "
                   f"Turn: {self.turn_count}, Score: {self.qualification_score}")
        
        return agent_response, should_continue
    
    def _update_qualification(
        self,
        call_record: CallRecord,
        intent_result: Dict[str, Any]
    ):
        """Update lead qualification based on intent analysis"""
        
        if intent_result.get("investment_interest"):
            call_record.qualification.has_investment_interest = True
            self.qualification_score += 30
        
        if intent_result.get("budget_mentioned"):
            call_record.qualification.budget_available = True
            self.qualification_score += 25
        
        if intent_result.get("decision_maker"):
            call_record.qualification.is_decision_maker = True
            self.qualification_score += 25
        
        # Update sentiment
        sentiment = intent_result.get("sentiment", "neutral")
        if sentiment == "positive":
            self.qualification_score += 10
        elif sentiment == "negative":
            self.qualification_score -= 10
        
        # Cap score at 100
        self.qualification_score = min(100, max(0, self.qualification_score))
        call_record.lead_score = self.qualification_score
        
        # Add notes
        key_points = intent_result.get("key_points", [])
        call_record.qualification.notes.extend(key_points)
    
    async def _should_continue_call(
        self,
        call_record: CallRecord,
        intent_result: Dict[str, Any]
    ) -> bool:
        """Determine if call should continue"""
        
        intent = intent_result.get("intent")
        
        # End call conditions
        if intent == "not_interested":
            self.current_phase = ConversationPhase.CLOSING
            return False
        
        if intent == "transfer_to_agent":
            self.current_phase = ConversationPhase.CLOSING
            return False
        
        # Maximum turns reached
        if self.turn_count >= 15:
            self.current_phase = ConversationPhase.CLOSING
            return False
        
        # Call duration check would be handled by parent system
        
        return True
    
    async def _generate_contextual_response(
        self,
        call_record: CallRecord,
        customer_text: str,
        intent_result: Dict[str, Any],
        conversation_history: List[ConversationTurn]
    ) -> str:
        """Generate response based on context and phase"""
        
        intent = intent_result.get("intent")
        
        # Handle specific intents
        if intent == "objection":
            response = await self.dialogue_generator.handle_objection(
                customer_text,
                conversation_history
            )
        elif intent == "not_interested":
            response = await self.dialogue_generator.generate_closing(
                outcome="not_interested",
                next_steps=None
            )
        elif intent == "schedule_callback":
            response = await self.dialogue_generator.generate_closing(
                outcome="callback_scheduled",
                next_steps="Rückruf vereinbaren"
            )
        elif intent == "transfer_to_agent":
            response = "Selbstverständlich. Ich verbinde Sie gleich mit einem unserer Spezialisten. Einen Moment bitte."
        else:
            # Generate contextual response
            lead_data = {
                "score": self.qualification_score,
                "phase": self.current_phase,
                "interest": call_record.qualification.has_investment_interest
            }
            
            response = await self.dialogue_generator.generate_response(
                customer_text,
                conversation_history,
                intent=intent,
                lead_data=lead_data
            )
        
        return response
    
    def _update_phase(self, intent_result: Dict[str, Any]):
        """Update conversation phase based on progress"""
        
        intent = intent_result.get("intent")
        
        # Phase transitions
        if self.current_phase == ConversationPhase.OPENING:
            if self.turn_count >= 2:
                self.current_phase = ConversationPhase.NEEDS_DISCOVERY
        
        elif self.current_phase == ConversationPhase.NEEDS_DISCOVERY:
            if intent == "interested" or intent == "request_info":
                self.current_phase = ConversationPhase.QUALIFICATION
        
        elif self.current_phase == ConversationPhase.QUALIFICATION:
            if self.qualification_score >= 50:
                self.current_phase = ConversationPhase.PRESENTATION
        
        elif self.current_phase == ConversationPhase.PRESENTATION:
            if intent == "objection":
                self.current_phase = ConversationPhase.OBJECTION_HANDLING
            elif intent == "interested":
                self.current_phase = ConversationPhase.CLOSING
        
        elif self.current_phase == ConversationPhase.OBJECTION_HANDLING:
            if intent == "interested":
                self.current_phase = ConversationPhase.PRESENTATION
            elif intent == "not_interested":
                self.current_phase = ConversationPhase.CLOSING
    
    async def end_call(
        self,
        call_record: CallRecord,
        outcome: str
    ) -> str:
        """
        End the call
        
        Args:
            call_record: Call record
            outcome: Call outcome
            
        Returns:
            Closing statement
        """
        self.current_phase = ConversationPhase.ENDED
        
        # Determine if lead is qualified
        call_record.is_qualified = self.qualification_score >= 70
        
        # Generate closing
        closing = await self.dialogue_generator.generate_closing(
            outcome=outcome,
            next_steps="Follow-up" if call_record.is_qualified else None
        )
        
        # Record closing turn
        turn = ConversationTurn(
            speaker="agent",
            text=closing,
            intent=None,
            confidence=1.0
        )
        call_record.transcript.append(turn.dict())
        
        call_record.end_time = datetime.utcnow()
        call_record.duration = int((call_record.end_time - call_record.start_time).total_seconds())
        
        logger.info(f"Call {call_record.call_id} ended. "
                   f"Duration: {call_record.duration}s, "
                   f"Score: {self.qualification_score}, "
                   f"Qualified: {call_record.is_qualified}")
        
        return closing

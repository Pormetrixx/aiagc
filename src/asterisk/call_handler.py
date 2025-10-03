"""
Main Call Handler
Orchestrates the entire call flow from initiation to completion
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional
from loguru import logger
import numpy as np

from ..models.call_state import CallRecord, CallState, ConversationTurn
from ..speech.deepgram_stt import DeepgramSTT
from ..speech.whisper_stt import WhisperSTT
from ..speech.tts import TextToSpeech
from ..ai.intent_detector import IntentDetector
from ..dialogue.dialogue_generator import DialogueGenerator
from ..dialogue.call_flow import CallFlowManager
from ..asterisk.agi_interface import AsteriskAGI
from ..config import settings


class CallHandler:
    """Main call handler orchestrating all components"""
    
    def __init__(self):
        """Initialize call handler"""
        # Initialize components
        self.deepgram_stt = DeepgramSTT()
        self.whisper_stt = WhisperSTT(model_name="base")
        self.tts = TextToSpeech()
        self.intent_detector = IntentDetector()
        self.dialogue_generator = DialogueGenerator()
        
        # AGI interface
        self.agi = AsteriskAGI()
        
        # Call state
        self.call_record: Optional[CallRecord] = None
        self.call_flow: Optional[CallFlowManager] = None
        self.current_transcript_buffer = ""
        self.is_speaking = False
        self.should_stop = False
        
    async def handle_call(
        self,
        phone_number: str,
        customer_name: Optional[str] = None
    ):
        """
        Handle complete call lifecycle
        
        Args:
            phone_number: Customer phone number
            customer_name: Optional customer name
        """
        # Create call record
        call_id = str(uuid.uuid4())
        self.call_record = CallRecord(
            call_id=call_id,
            phone_number=phone_number,
            caller_id=settings.asterisk_caller_id,
            state=CallState.INITIATED,
            start_time=datetime.utcnow()
        )
        
        # Initialize call flow manager
        self.call_flow = CallFlowManager(
            self.intent_detector,
            self.dialogue_generator
        )
        
        logger.info(f"Starting call {call_id} to {phone_number}")
        
        try:
            # Setup AGI
            self.agi.setup()
            channel_info = self.agi.get_channel_info()
            logger.info(f"Channel info: {channel_info}")
            
            # Answer the call
            if not self.agi.answer():
                logger.error("Failed to answer call")
                self.call_record.state = CallState.FAILED
                return
            
            self.call_record.state = CallState.ANSWERED
            logger.info("Call answered")
            
            # Start speech recognition
            await self._setup_speech_recognition()
            
            # Start conversation
            await self._run_conversation(customer_name)
            
            # End call
            self.call_record.state = CallState.COMPLETED
            self.agi.hangup()
            
            logger.info(f"Call {call_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error handling call {call_id}: {e}")
            self.call_record.state = CallState.FAILED
            self.call_record.error_messages.append(str(e))
            
        finally:
            # Cleanup
            if self.deepgram_stt.is_connected:
                await self.deepgram_stt.stop_stream()
            
            # Save call record (would save to database in production)
            await self._save_call_record()
    
    async def _setup_speech_recognition(self):
        """Setup Deepgram streaming STT"""
        
        async def on_transcript(text: str, confidence: float):
            """Handle transcript from Deepgram"""
            if not self.is_speaking and len(text.strip()) > 0:
                self.current_transcript_buffer += " " + text.strip()
                logger.debug(f"Transcript buffer: {self.current_transcript_buffer}")
        
        async def on_error(error: Exception):
            """Handle STT errors"""
            logger.error(f"STT error: {error}")
        
        # Start Deepgram streaming
        await self.deepgram_stt.start_stream(
            on_transcript=on_transcript,
            on_error=on_error
        )
    
    async def _run_conversation(self, customer_name: Optional[str] = None):
        """Run the conversation loop"""
        
        # Generate and speak opening
        opening = await self.call_flow.start_call(
            self.call_record,
            customer_name=customer_name
        )
        await self._speak(opening)
        
        # Conversation loop
        turn = 0
        max_turns = 15
        
        while not self.should_stop and turn < max_turns:
            turn += 1
            
            # Listen for customer response
            customer_text = await self._listen_for_response(
                timeout=settings.speech_timeout
            )
            
            if not customer_text:
                logger.warning("No response from customer")
                await self._speak("Sind Sie noch da? Können Sie mich hören?")
                
                # Try once more
                customer_text = await self._listen_for_response(
                    timeout=settings.speech_timeout
                )
                
                if not customer_text:
                    logger.warning("Still no response, ending call")
                    break
            
            # Process response and get agent reply
            agent_response, should_continue = await self.call_flow.process_customer_response(
                self.call_record,
                customer_text
            )
            
            # Speak agent response
            await self._speak(agent_response)
            
            if not should_continue:
                logger.info("Call flow indicates to end call")
                break
        
        # Generate and speak closing
        outcome = "qualified" if self.call_record.is_qualified else "not_qualified"
        closing = await self.call_flow.end_call(self.call_record, outcome)
        await self._speak(closing)
    
    async def _listen_for_response(self, timeout: int = 10) -> str:
        """
        Listen for customer response
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Transcribed text
        """
        self.current_transcript_buffer = ""
        self.is_speaking = False
        
        # Wait for speech with timeout
        start_time = asyncio.get_event_loop().time()
        silence_threshold = 2.0  # Seconds of silence to consider end of speech
        last_speech_time = start_time
        
        while True:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time
            
            # Check timeout
            if elapsed > timeout:
                logger.debug("Listen timeout reached")
                break
            
            # Check if we have speech and silence after
            if self.current_transcript_buffer:
                silence_duration = current_time - last_speech_time
                if silence_duration > silence_threshold:
                    logger.debug("End of speech detected")
                    break
                last_speech_time = current_time
            
            await asyncio.sleep(0.1)
        
        transcript = self.current_transcript_buffer.strip()
        logger.info(f"Customer said: {transcript}")
        
        return transcript
    
    async def _speak(self, text: str):
        """
        Speak text to customer
        
        Args:
            text: Text to speak
        """
        self.is_speaking = True
        logger.info(f"Agent says: {text}")
        
        try:
            # Generate audio
            audio_data = await self.tts.generate_speech(text)
            
            # In production, stream audio to Asterisk
            # For now, we'll save to file and play via AGI
            audio_file = f"/tmp/agent_speech_{uuid.uuid4()}.wav"
            with open(audio_file, "wb") as f:
                f.write(audio_data)
            
            # Play audio through Asterisk
            self.agi.stream_file(audio_file.replace('.wav', ''))
            
            # Clean up
            import os
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
        
        finally:
            self.is_speaking = False
            
            # Small pause after speaking
            await asyncio.sleep(0.5)
    
    async def _save_call_record(self):
        """Save call record to database"""
        # In production, save to PostgreSQL
        # For now, log the summary
        logger.info(f"""
Call Summary:
=============
Call ID: {self.call_record.call_id}
Phone: {self.call_record.phone_number}
Duration: {self.call_record.duration}s
State: {self.call_record.state}
Lead Score: {self.call_record.lead_score}
Qualified: {self.call_record.is_qualified}
Turns: {len(self.call_record.transcript)}
Qualification:
  - Investment Interest: {self.call_record.qualification.has_investment_interest}
  - Budget Available: {self.call_record.qualification.budget_available}
  - Decision Maker: {self.call_record.qualification.is_decision_maker}
""")
        
        # TODO: Save to database
        # await db.save_call_record(self.call_record)


async def main():
    """Main entry point for AGI script"""
    handler = CallHandler()
    
    # Get phone number from AGI environment
    # In production, this would come from the dialplan
    phone_number = handler.agi.env.get('callerid', 'unknown')
    
    await handler.handle_call(phone_number)


if __name__ == "__main__":
    # Configure logging
    logger.add(
        settings.log_file,
        rotation="500 MB",
        level=settings.log_level
    )
    
    # Run handler
    asyncio.run(main())

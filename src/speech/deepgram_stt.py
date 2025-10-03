"""
Deepgram Speech-to-Text Integration
Provides real-time speech recognition for German language
"""

import asyncio
from typing import Optional, Callable, Any
from loguru import logger
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

from ..config import settings


class DeepgramSTT:
    """Deepgram Speech-to-Text service"""
    
    def __init__(self):
        """Initialize Deepgram client"""
        self.api_key = settings.deepgram_api_key
        self.language = settings.deepgram_language
        self.model = settings.deepgram_model
        
        config = DeepgramClientOptions(
            options={"keepalive": "true"}
        )
        self.client = DeepgramClient(self.api_key, config)
        self.connection = None
        self.is_connected = False
        
    async def start_stream(
        self,
        on_transcript: Callable[[str, float], None],
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        Start streaming speech recognition
        
        Args:
            on_transcript: Callback for transcript results (text, confidence)
            on_error: Callback for errors
        """
        try:
            self.connection = self.client.listen.asynclive.v("1")
            
            # Set up event handlers
            async def on_message(self, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                if len(sentence) > 0:
                    confidence = result.channel.alternatives[0].confidence
                    logger.debug(f"Deepgram transcript: {sentence} (confidence: {confidence})")
                    if on_transcript:
                        await on_transcript(sentence, confidence)
            
            async def on_metadata(self, metadata, **kwargs):
                logger.debug(f"Deepgram metadata: {metadata}")
            
            async def on_speech_started(self, speech_started, **kwargs):
                logger.debug("Speech started")
            
            async def on_utterance_end(self, utterance_end, **kwargs):
                logger.debug("Utterance ended")
            
            async def on_error_handler(self, error, **kwargs):
                logger.error(f"Deepgram error: {error}")
                if on_error:
                    await on_error(error)
            
            # Register event handlers
            self.connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
            self.connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
            self.connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
            self.connection.on(LiveTranscriptionEvents.Error, on_error_handler)
            
            # Configure live transcription
            options = LiveOptions(
                model=self.model,
                language=self.language,
                punctuate=True,
                smart_format=True,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
                encoding="linear16",
                sample_rate=settings.audio_sample_rate,
            )
            
            # Start connection
            if await self.connection.start(options):
                self.is_connected = True
                logger.info("Deepgram connection started successfully")
            else:
                logger.error("Failed to start Deepgram connection")
                
        except Exception as e:
            logger.error(f"Error starting Deepgram stream: {e}")
            if on_error:
                await on_error(e)
            raise
    
    async def send_audio(self, audio_data: bytes):
        """
        Send audio data to Deepgram
        
        Args:
            audio_data: Raw audio bytes
        """
        if self.connection and self.is_connected:
            try:
                self.connection.send(audio_data)
            except Exception as e:
                logger.error(f"Error sending audio to Deepgram: {e}")
                raise
        else:
            logger.warning("Deepgram connection not active")
    
    async def stop_stream(self):
        """Stop the streaming connection"""
        if self.connection and self.is_connected:
            try:
                await self.connection.finish()
                self.is_connected = False
                logger.info("Deepgram connection stopped")
            except Exception as e:
                logger.error(f"Error stopping Deepgram stream: {e}")
    
    async def transcribe_file(self, audio_file: str) -> dict:
        """
        Transcribe an audio file (non-streaming)
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Transcription result
        """
        try:
            with open(audio_file, "rb") as audio:
                source = {"buffer": audio.read()}
                
                options = {
                    "model": self.model,
                    "language": self.language,
                    "punctuate": True,
                    "smart_format": True,
                }
                
                response = await self.client.listen.asyncrest.v("1").transcribe_file(
                    source, options
                )
                
                return response
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            raise

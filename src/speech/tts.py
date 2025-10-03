"""
Text-to-Speech Integration
For generating agent voice responses
"""

import asyncio
from typing import Optional
from loguru import logger
import httpx
from pathlib import Path

from ..config import settings


class TextToSpeech:
    """Text-to-Speech service using OpenAI TTS"""
    
    def __init__(self):
        """Initialize TTS service"""
        self.api_key = settings.openai_api_key
        self.voice = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
        self.model = "tts-1"  # or tts-1-hd for higher quality
        
    async def generate_speech(
        self,
        text: str,
        output_file: Optional[str] = None,
        voice: Optional[str] = None
    ) -> bytes:
        """
        Generate speech from text
        
        Args:
            text: Text to convert to speech
            output_file: Optional file path to save audio
            voice: Voice to use (default: alloy)
            
        Returns:
            Audio data as bytes
        """
        try:
            voice = voice or self.voice
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": text,
                        "voice": voice,
                        "response_format": "wav"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                audio_data = response.content
                
                # Save to file if specified
                if output_file:
                    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                    logger.info(f"Speech saved to {output_file}")
                
                return audio_data
                
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            raise


class ElevenLabsTTS:
    """Alternative TTS using ElevenLabs for more natural German voices"""
    
    def __init__(self, api_key: str):
        """
        Initialize ElevenLabs TTS
        
        Args:
            api_key: ElevenLabs API key
        """
        self.api_key = api_key
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice, can be customized
        
    async def generate_speech(
        self,
        text: str,
        output_file: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> bytes:
        """
        Generate speech using ElevenLabs
        
        Args:
            text: Text to convert to speech
            output_file: Optional file path to save audio
            voice_id: Voice ID to use
            
        Returns:
            Audio data as bytes
        """
        try:
            voice_id = voice_id or self.voice_id
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75
                        }
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                audio_data = response.content
                
                if output_file:
                    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                    logger.info(f"Speech saved to {output_file}")
                
                return audio_data
                
        except Exception as e:
            logger.error(f"Error generating speech with ElevenLabs: {e}")
            raise

"""
Whisper Speech-to-Text Integration
Fallback STT using OpenAI Whisper
"""

import whisper
import torch
from typing import Optional
from loguru import logger
import numpy as np

from ..config import settings


class WhisperSTT:
    """Whisper Speech-to-Text service"""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize Whisper model
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Whisper model '{model_name}' on {self.device}")
        
        try:
            self.model = whisper.load_model(model_name, device=self.device)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def transcribe_audio(
        self,
        audio_data: np.ndarray,
        language: str = "de"
    ) -> dict:
        """
        Transcribe audio data
        
        Args:
            audio_data: Audio as numpy array
            language: Language code (default: German)
            
        Returns:
            Transcription result with text and metadata
        """
        try:
            result = self.model.transcribe(
                audio_data,
                language=language,
                task="transcribe",
                fp16=(self.device == "cuda"),
                verbose=False
            )
            
            logger.debug(f"Whisper transcript: {result['text']}")
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing with Whisper: {e}")
            raise
    
    def transcribe_file(
        self,
        audio_file: str,
        language: str = "de"
    ) -> dict:
        """
        Transcribe audio file
        
        Args:
            audio_file: Path to audio file
            language: Language code (default: German)
            
        Returns:
            Transcription result
        """
        try:
            result = self.model.transcribe(
                audio_file,
                language=language,
                task="transcribe",
                fp16=(self.device == "cuda")
            )
            
            logger.info(f"Whisper transcribed file: {audio_file}")
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing file with Whisper: {e}")
            raise
    
    def detect_language(self, audio_data: np.ndarray) -> tuple[str, float]:
        """
        Detect language from audio
        
        Args:
            audio_data: Audio as numpy array
            
        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            # Load audio and pad/trim it to fit 30 seconds
            audio = whisper.pad_or_trim(audio_data)
            
            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            confidence = probs[detected_language]
            
            logger.debug(f"Detected language: {detected_language} (confidence: {confidence})")
            return detected_language, confidence
            
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return "de", 0.0

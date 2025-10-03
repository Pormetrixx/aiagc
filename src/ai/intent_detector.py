"""
AI Intent Detection and Analysis
Uses OpenAI GPT to detect intent and analyze conversation
"""

import json
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
from loguru import logger

from ..config import settings
from ..models.call_state import IntentType, ConversationTurn


class IntentDetector:
    """Intent detection and conversation analysis using AI"""
    
    def __init__(self):
        """Initialize intent detector"""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        
        # German intent detection prompts
        self.system_prompt = """Du bist ein KI-Assistent, der Kundenabsichten in Verkaufsgesprächen analysiert.
Analysiere die Kundenantwort und erkenne die Absicht bezüglich Finanzprodukte, Investitionen, Arbitrage und ROI-Möglichkeiten.

Mögliche Absichten:
- interested: Kunde zeigt Interesse am Produkt/Angebot
- not_interested: Kunde lehnt ab oder zeigt Desinteresse
- request_info: Kunde möchte mehr Informationen
- schedule_callback: Kunde möchte später kontaktiert werden
- transfer_to_agent: Kunde möchte mit einem menschlichen Agenten sprechen
- objection: Kunde hat Einwände oder Bedenken
- question: Kunde stellt eine Frage
- positive_sentiment: Positive Stimmung erkannt
- negative_sentiment: Negative Stimmung erkannt
- neutral: Neutrale Reaktion

Antworte im JSON-Format mit:
{
  "intent": "intent_type",
  "confidence": 0.0-1.0,
  "sentiment": "positive/negative/neutral",
  "key_points": ["wichtige Punkte"],
  "investment_interest": true/false,
  "budget_mentioned": true/false,
  "decision_maker": true/false
}"""
    
    async def detect_intent(
        self,
        customer_text: str,
        conversation_history: Optional[List[ConversationTurn]] = None
    ) -> Dict[str, Any]:
        """
        Detect intent from customer speech
        
        Args:
            customer_text: What the customer said
            conversation_history: Previous conversation turns
            
        Returns:
            Intent analysis dictionary
        """
        try:
            # Build context from conversation history
            context = ""
            if conversation_history:
                context = "Bisheriger Gesprächsverlauf:\n"
                for turn in conversation_history[-5:]:  # Last 5 turns
                    context += f"{turn.speaker}: {turn.text}\n"
            
            # Create prompt
            user_prompt = f"{context}\nKunde: {customer_text}\n\nAnalysiere die Absicht:"
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Intent detected: {result['intent']} (confidence: {result.get('confidence', 0)})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            return {
                "intent": "neutral",
                "confidence": 0.0,
                "sentiment": "neutral",
                "key_points": [],
                "investment_interest": False,
                "budget_mentioned": False,
                "decision_maker": False
            }
    
    async def analyze_conversation(
        self,
        conversation_history: List[ConversationTurn]
    ) -> Dict[str, Any]:
        """
        Analyze entire conversation for insights
        
        Args:
            conversation_history: All conversation turns
            
        Returns:
            Conversation analysis
        """
        try:
            # Build full transcript
            transcript = "\n".join([
                f"{turn.speaker}: {turn.text}" 
                for turn in conversation_history
            ])
            
            analysis_prompt = """Analysiere das gesamte Verkaufsgespräch und bewerte:
1. Lead-Qualität (Score 0-100)
2. Investitionsinteresse vorhanden?
3. Budget/Kapital verfügbar?
4. Ist der Kontakt ein Entscheidungsträger?
5. Beste nächste Schritte
6. Zusammenfassung der wichtigsten Punkte

Antworte im JSON-Format."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{transcript}\n\n{analysis_prompt}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Conversation analyzed: Lead score {result.get('lead_score', 0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return {
                "lead_score": 0,
                "investment_interest": False,
                "budget_available": False,
                "decision_maker": False,
                "next_steps": [],
                "summary": ""
            }
    
    async def extract_entities(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Extract entities like amounts, dates, preferences
        
        Args:
            text: Text to analyze
            
        Returns:
            Extracted entities
        """
        try:
            entity_prompt = """Extrahiere folgende Informationen aus dem Text:
- Investitionsbeträge/Budgets
- Zeitrahmen/Termine
- Produktpräferenzen
- Kontaktinformationen
- Wichtige Zahlen oder Fakten

Antworte im JSON-Format."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für Informationsextraktion."},
                    {"role": "user", "content": f"Text: {text}\n\n{entity_prompt}"}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}

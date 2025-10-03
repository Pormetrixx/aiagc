"""
Dynamic Dialogue Generator
Generates natural, context-aware responses in German
"""

from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from loguru import logger

from ..config import settings
from ..models.call_state import ConversationTurn, IntentType


class DialogueGenerator:
    """AI-powered dialogue generation for natural conversations"""
    
    def __init__(self):
        """Initialize dialogue generator"""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        
        # German sales agent persona
        self.system_prompt = """Du bist ein professioneller Vertriebsagent für Finanzprodukte und Investitionsmöglichkeiten.
Deine Aufgabe ist es, qualifizierte Leads für Investitionsmöglichkeiten, Arbitrage-Strategien und ROI-Produkte zu generieren.

Persönlichkeit und Stil:
- Freundlich, professionell und vertrauenswürdig
- Sprich natürlich wie in einem echten Telefongespräch
- Verwende keine Emojis oder Sonderzeichen
- Halte Antworten kurz und prägnant (1-3 Sätze)
- Stelle gezielte Fragen zur Qualifizierung
- Gehe auf Einwände professionell ein
- Zeige Empathie und Verständnis

Gesprächsziele:
1. Interesse am Investmentprodukt wecken
2. Qualifizieren: Budget, Zeitrahmen, Entscheidungsbefugnis
3. Termin für detailliertes Gespräch vereinbaren
4. Bei Desinteresse: höflich verabschieden

Produkte (Beispiele):
- Arbitrage-Möglichkeiten mit garantierten Renditen
- ROI-optimierte Investmentportfolios
- Exklusive Finanzprodukte für qualifizierte Investoren

Wichtig: 
- Bleibe im Rahmen der Compliance
- Mache keine unrealistischen Versprechen
- Respektiere Kundenwünsche
- Bei Ablehnung: höflich beenden"""
    
    async def generate_response(
        self,
        customer_text: str,
        conversation_history: List[ConversationTurn],
        intent: Optional[str] = None,
        lead_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate contextual response to customer
        
        Args:
            customer_text: What the customer just said
            conversation_history: Previous conversation
            intent: Detected intent
            lead_data: Current lead qualification data
            
        Returns:
            Agent's response text
        """
        try:
            # Build conversation context
            context = ""
            if conversation_history:
                for turn in conversation_history[-6:]:  # Last 6 turns
                    context += f"{turn.speaker}: {turn.text}\n"
            
            # Add intent and lead data context
            meta_context = ""
            if intent:
                meta_context += f"Erkannte Absicht: {intent}\n"
            if lead_data:
                meta_context += f"Lead-Daten: {lead_data}\n"
            
            # Create prompt
            user_prompt = f"""Bisheriger Gesprächsverlauf:
{context}
Kunde: {customer_text}

{meta_context}

Generiere eine natürliche, passende Antwort des Vertriebsagenten:"""
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            agent_response = response.choices[0].message.content.strip()
            logger.info(f"Generated response: {agent_response}")
            
            return agent_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback response
            return "Entschuldigung, könnten Sie das bitte wiederholen?"
    
    async def generate_opening(
        self,
        customer_name: Optional[str] = None,
        campaign_type: str = "investment"
    ) -> str:
        """
        Generate opening statement for call
        
        Args:
            customer_name: Customer's name if available
            campaign_type: Type of campaign (investment, arbitrage, roi)
            
        Returns:
            Opening statement
        """
        try:
            prompt = f"""Generiere eine professionelle Eröffnung für ein Verkaufsgespräch.
Typ: {campaign_type}
Kundenname: {customer_name or 'unbekannt'}

Die Eröffnung sollte:
- Freundlich und professionell sein
- Den Grund des Anrufs klar machen
- Interesse wecken
- Nach 2-3 Sätzen eine Frage stellen

Generiere nur die Eröffnung ohne zusätzlichen Text:"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=100
            )
            
            opening = response.choices[0].message.content.strip()
            logger.info(f"Generated opening: {opening}")
            
            return opening
            
        except Exception as e:
            logger.error(f"Error generating opening: {e}")
            greeting = f"Guten Tag{' ' + customer_name if customer_name else ''}"
            return f"{greeting}! Mein Name ist von der Investmentberatung. Haben Sie einen kurzen Moment Zeit?"
    
    async def generate_closing(
        self,
        outcome: str,
        next_steps: Optional[str] = None
    ) -> str:
        """
        Generate appropriate closing statement
        
        Args:
            outcome: Call outcome (qualified, not_interested, callback, etc.)
            next_steps: Any agreed next steps
            
        Returns:
            Closing statement
        """
        try:
            prompt = f"""Generiere eine passende Verabschiedung für ein Verkaufsgespräch.
Ergebnis: {outcome}
Nächste Schritte: {next_steps or 'keine'}

Die Verabschiedung sollte:
- Professionell und höflich sein
- Kurz und prägnant sein
- Zum Ergebnis passen

Generiere nur die Verabschiedung:"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=80
            )
            
            closing = response.choices[0].message.content.strip()
            logger.info(f"Generated closing: {closing}")
            
            return closing
            
        except Exception as e:
            logger.error(f"Error generating closing: {e}")
            return "Vielen Dank für Ihre Zeit. Ich wünsche Ihnen noch einen schönen Tag!"
    
    async def handle_objection(
        self,
        objection: str,
        conversation_history: List[ConversationTurn]
    ) -> str:
        """
        Generate response to handle customer objections
        
        Args:
            objection: Customer's objection
            conversation_history: Conversation context
            
        Returns:
            Objection handling response
        """
        try:
            context = "\n".join([
                f"{turn.speaker}: {turn.text}" 
                for turn in conversation_history[-4:]
            ])
            
            prompt = f"""Der Kunde hat einen Einwand geäußert: "{objection}"

Gesprächskontext:
{context}

Generiere eine professionelle, empathische Antwort die:
- Den Einwand ernst nimmt
- Verständnis zeigt
- Eine konstruktive Lösung anbietet
- Das Gespräch positiv weiterbringt

Antwort:"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            handling = response.choices[0].message.content.strip()
            logger.info(f"Generated objection handling: {handling}")
            
            return handling
            
        except Exception as e:
            logger.error(f"Error handling objection: {e}")
            return "Ich verstehe Ihre Bedenken völlig. Darf ich Ihnen dazu mehr Informationen geben?"

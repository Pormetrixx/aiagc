# API Reference

## Core Components

### 1. Call Handler

The main orchestrator for call lifecycle management.

```python
from src.asterisk.call_handler import CallHandler

handler = CallHandler()
await handler.handle_call(
    phone_number="+491234567890",
    customer_name="Max Mustermann"
)
```

### 2. Asterisk AMI

For call origination and monitoring.

```python
from src.asterisk.agi_interface import AsteriskAMI

ami = AsteriskAMI()
ami.connect()

# Originate call
ami.originate_call(
    phone_number="+491234567890",
    context="outbound-calls",
    extension="s",
    caller_id="+4987654321",
    variables={"CAMPAIGN": "investment"}
)

ami.disconnect()
```

### 3. Speech Recognition

#### Deepgram STT (Primary)

```python
from src.speech.deepgram_stt import DeepgramSTT

stt = DeepgramSTT()

async def on_transcript(text: str, confidence: float):
    print(f"Transcript: {text} ({confidence})")

await stt.start_stream(on_transcript=on_transcript)
await stt.send_audio(audio_bytes)
await stt.stop_stream()
```

#### Whisper STT (Fallback)

```python
from src.speech.whisper_stt import WhisperSTT
import numpy as np

stt = WhisperSTT(model_name="base")

# Transcribe audio
result = stt.transcribe_audio(audio_array, language="de")
print(result['text'])

# Detect language
lang, confidence = stt.detect_language(audio_array)
```

### 4. Text-to-Speech

```python
from src.speech.tts import TextToSpeech

tts = TextToSpeech()

# Generate speech
audio_data = await tts.generate_speech(
    text="Guten Tag! Wie kann ich Ihnen helfen?",
    output_file="output.wav",
    voice="alloy"
)
```

### 5. Intent Detection

```python
from src.ai.intent_detector import IntentDetector

detector = IntentDetector()

# Detect intent
result = await detector.detect_intent(
    customer_text="Ich bin interessiert, aber ich muss darüber nachdenken",
    conversation_history=history
)

print(result['intent'])  # e.g., "interested"
print(result['confidence'])  # e.g., 0.85
```

### 6. Dialogue Generation

```python
from src.dialogue.dialogue_generator import DialogueGenerator

generator = DialogueGenerator()

# Generate opening
opening = await generator.generate_opening(
    customer_name="Max",
    campaign_type="investment"
)

# Generate response
response = await generator.generate_response(
    customer_text="Das klingt interessant",
    conversation_history=history,
    intent="interested"
)

# Handle objection
response = await generator.handle_objection(
    objection="Das ist mir zu teuer",
    conversation_history=history
)
```

### 7. Call Flow Management

```python
from src.dialogue.call_flow import CallFlowManager
from src.ai.intent_detector import IntentDetector
from src.dialogue.dialogue_generator import DialogueGenerator

flow = CallFlowManager(
    intent_detector=IntentDetector(),
    dialogue_generator=DialogueGenerator()
)

# Start call
opening = await flow.start_call(call_record, customer_name="Max")

# Process customer response
response, should_continue = await flow.process_customer_response(
    call_record,
    "Ja, das interessiert mich"
)

# End call
closing = await flow.end_call(call_record, outcome="qualified")
```

## Data Models

### CallRecord

```python
from src.models.call_state import CallRecord, CallState

record = CallRecord(
    call_id="unique-id",
    phone_number="+491234567890",
    caller_id="+4987654321",
    state=CallState.INITIATED
)

# Update state
record.state = CallState.ANSWERED

# Add to transcript
record.transcript.append({
    "timestamp": datetime.utcnow(),
    "speaker": "agent",
    "text": "Guten Tag!"
})

# Update qualification
record.qualification.has_investment_interest = True
record.lead_score = 85
```

### ConversationTurn

```python
from src.models.call_state import ConversationTurn, IntentType

turn = ConversationTurn(
    speaker="customer",
    text="Ich interessiere mich dafür",
    intent=IntentType.INTERESTED,
    confidence=0.92,
    audio_duration=2.5
)
```

## Utility Functions

### Phone Number Normalization

```python
from src.utils.helpers import normalize_phone_number

normalized = normalize_phone_number(
    phone_number="0123 456789",
    country_code="DE"
)
# Returns: "+491234567890"
```

### Lead Scoring

```python
from src.utils.helpers import calculate_lead_score

score = calculate_lead_score(
    has_investment_interest=True,
    budget_available=True,
    is_decision_maker=True,
    positive_sentiment=True,
    engagement_level=8
)
# Returns: 98
```

### Amount Extraction

```python
from src.utils.helpers import extract_amount

amount = extract_amount("Ich habe 50 tausend Euro verfügbar")
# Returns: 50000.0
```

## Configuration

### Settings

```python
from src.config import settings

# Access configuration
print(settings.deepgram_api_key)
print(settings.openai_model)
print(settings.max_call_duration)

# Update at runtime
settings.log_level = "DEBUG"
```

## Custom Extensions

### Adding New Intent Types

1. Update `src/models/call_state.py`:

```python
class IntentType(str, Enum):
    # Existing intents...
    CUSTOM_INTENT = "custom_intent"
```

2. Update intent detection prompt in `src/ai/intent_detector.py`

3. Handle new intent in `src/dialogue/call_flow.py`

### Custom Dialogue Templates

Create custom response generator:

```python
from src.dialogue.dialogue_generator import DialogueGenerator

class CustomDialogueGenerator(DialogueGenerator):
    async def generate_custom_response(self, context):
        # Your custom logic
        return "Custom response"
```

### Adding New Languages

1. Update language in `.env`:
```bash
DEEPGRAM_LANGUAGE=en  # or fr, es, etc.
```

2. Update system prompts in:
   - `src/ai/intent_detector.py`
   - `src/dialogue/dialogue_generator.py`

3. Add language-specific scripts in `docs/conversation_scripts.md`

### Custom Lead Qualification

Extend the qualification model:

```python
from src.models.call_state import LeadQualification
from pydantic import Field

class CustomQualification(LeadQualification):
    industry: str = ""
    company_size: int = 0
    annual_revenue: float = 0.0
    custom_field: str = Field(default="")
```

## Event Handlers

### Custom Call Events

```python
class CustomCallHandler(CallHandler):
    async def on_call_start(self, call_record):
        # Custom logic when call starts
        print(f"Call {call_record.call_id} starting")
    
    async def on_call_end(self, call_record):
        # Custom logic when call ends
        await self.send_webhook(call_record)
    
    async def on_qualified_lead(self, call_record):
        # Custom logic for qualified leads
        await self.notify_sales_team(call_record)
```

## Integration Examples

### CRM Integration

```python
async def save_to_crm(call_record):
    """Save call record to CRM"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://your-crm.com/api/leads",
            json={
                "phone": call_record.phone_number,
                "score": call_record.lead_score,
                "notes": call_record.qualification.notes,
                "transcript": call_record.transcript
            }
        )
```

### Webhook Notifications

```python
async def send_webhook(event_type, data):
    """Send webhook for events"""
    import httpx
    
    webhook_url = "https://your-service.com/webhook"
    
    async with httpx.AsyncClient() as client:
        await client.post(
            webhook_url,
            json={
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
        )
```

### Email Notifications

```python
async def send_email_notification(call_record):
    """Send email for qualified leads"""
    import smtplib
    from email.mime.text import MIMEText
    
    msg = MIMEText(f"""
    Qualified lead:
    Phone: {call_record.phone_number}
    Score: {call_record.lead_score}
    Notes: {call_record.qualification.notes}
    """)
    
    msg['Subject'] = 'New Qualified Lead'
    msg['From'] = 'noreply@yourcompany.com'
    msg['To'] = 'sales@yourcompany.com'
    
    # Send email (configure SMTP)
    # ...
```

## Testing

### Unit Tests

```python
import pytest
from src.ai.intent_detector import IntentDetector

@pytest.mark.asyncio
async def test_intent_detection():
    detector = IntentDetector()
    result = await detector.detect_intent("Ich bin interessiert")
    
    assert result['intent'] == 'interested'
    assert result['confidence'] > 0.7
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_call_flow():
    handler = CallHandler()
    # Mock components and test full flow
    # ...
```

## Best Practices

1. **Error Handling**: Always use try-except blocks
2. **Logging**: Use loguru for comprehensive logging
3. **Async/Await**: Use async functions for I/O operations
4. **Type Hints**: Use type hints for better code clarity
5. **Configuration**: Use environment variables for secrets
6. **Testing**: Write tests for critical components
7. **Documentation**: Document custom extensions

## Performance Tips

1. **Connection Pooling**: Use connection pools for databases
2. **Caching**: Cache common responses in Redis
3. **Batch Processing**: Process multiple calls in parallel
4. **Resource Limits**: Set appropriate limits in Docker
5. **Monitoring**: Monitor API latency and usage

## Troubleshooting API

Common issues and solutions:

```python
# Issue: Timeout errors
# Solution: Increase timeout
import httpx
client = httpx.AsyncClient(timeout=30.0)

# Issue: Rate limits
# Solution: Implement exponential backoff
import asyncio
await asyncio.sleep(2 ** retry_count)

# Issue: Memory leaks
# Solution: Properly close connections
async with httpx.AsyncClient() as client:
    # Use client
    pass  # Automatically closed
```

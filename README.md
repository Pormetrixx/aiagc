# AIAGC - AI Agent for Automated Outbound Calling

Professional AI-powered agent for automated outbound calling using Asterisk and Deepgram/Whisper. Designed for German-speaking markets to generate qualified leads for investment opportunities, arbitrage, ROI products, and financial offers.

## 🌟 Features

### Core Capabilities
- **Natural Voice Conversations**: Human-like dialogue in German using advanced AI
- **Real-time Speech Recognition**: Deepgram for low-latency STT with Whisper fallback
- **Dynamic Dialogue Generation**: Context-aware responses using GPT-4
- **Intent Detection**: Real-time analysis of customer intent and sentiment
- **Lead Qualification**: Automated scoring based on investment interest, budget, and decision-maker status
- **Call Flow Management**: Intelligent state machine handling conversation phases
- **Asterisk Integration**: Full telephony control via AGI and AMI interfaces

### Technical Features
- Asynchronous call handling with asyncio
- PostgreSQL for call records and lead data
- Redis for real-time state management
- Comprehensive logging and monitoring
- Docker containerization for easy deployment
- Modular architecture for easy customization

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Asterisk PBX                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Dialplan   │  │     AGI      │  │     AMI      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Core                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Call Handler                             │  │
│  │  - Orchestrates entire call lifecycle               │  │
│  │  - Manages audio streaming                          │  │
│  │  - Coordinates all components                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│         ┌──────────────────┼──────────────────┐            │
│         ▼                  ▼                  ▼            │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐      │
│  │   Speech   │    │     AI     │    │  Dialogue  │      │
│  │ Recognition│    │   Intent   │    │ Generator  │      │
│  │            │    │  Detector  │    │            │      │
│  │ Deepgram   │    │   GPT-4    │    │   GPT-4    │      │
│  │ Whisper    │    │            │    │            │      │
│  └────────────┘    └────────────┘    └────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  ┌──────────────┐              ┌──────────────┐           │
│  │  PostgreSQL  │              │    Redis     │           │
│  │ Call Records │              │  Call State  │           │
│  │  Lead Data   │              │   Caching    │           │
│  └──────────────┘              └──────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Asterisk PBX (included in Docker setup)
- SIP trunk provider account
- API Keys:
  - Deepgram API key
  - OpenAI API key (for GPT-4 and Whisper)
  - Optional: Anthropic API key

## 🚀 Quick Start

### Option A: Complete Installation on Ubuntu 22.04 (Recommended for Testing)

For a complete installation on a fresh Ubuntu 22.04 server with Asterisk and internal testing extensions:

```bash
git clone https://github.com/Pormetrixx/aiagc.git
cd aiagc
sudo ./install.sh
```

This will:
- Install all system dependencies
- Compile and install Asterisk from source
- Configure internal SIP extensions (1000, 1001) for testing
- Set up the AI agent application
- Create all necessary directories and configurations

After installation, you can test the AI agent by:
1. Registering a SIP client (extension 1000, password: test1000)
2. Calling extension 1001 to hear the AI agent
3. See `TESTING_GUIDE.md` for detailed testing instructions

### Option B: Docker-Based Setup (Production)

### 1. Clone the Repository

```bash
git clone https://github.com/Pormetrixx/aiagc.git
cd aiagc
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Deepgram
DEEPGRAM_API_KEY=your_deepgram_api_key

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Asterisk
ASTERISK_HOST=localhost
ASTERISK_USERNAME=admin
ASTERISK_SECRET=your_asterisk_secret
ASTERISK_CALLER_ID=+4912345678

# Database
DATABASE_URL=postgresql://aiagc:password@localhost:5432/aiagc_calls

# Redis
REDIS_HOST=localhost
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Start with Docker

```bash
docker-compose up -d
```

This starts:
- Asterisk PBX
- PostgreSQL database
- Redis cache
- AIAGC application

### 5. Configure Asterisk

Edit `config/asterisk/pjsip.conf` with your SIP trunk credentials:

```ini
[trunk-auth]
type=auth
auth_type=userpass
username=YOUR_SIP_USERNAME
password=YOUR_SIP_PASSWORD
```

### 6. Test Internal Extensions (After install.sh)

If you used `install.sh`, you can test the AI agent with internal extensions:

```bash
# Check system status
./test_system.sh

# View testing guide
cat TESTING_GUIDE.md
```

**To test the AI agent:**
1. Install a SIP client (Zoiper, Linphone, MicroSIP, etc.)
2. Configure with:
   - Server: Your server IP
   - Extension: 1000
   - Password: test1000
   - Port: 5060
3. Call extension **1001** to hear the AI agent
4. Monitor logs: `tail -f /opt/aiagc/logs/aiagc.log`
5. View Asterisk console: `asterisk -rvvv`

### 7. Initiate Outbound Test Call (Production)

Using Asterisk AMI:

```python
from src.asterisk.agi_interface import AsteriskAMI

ami = AsteriskAMI()
ami.connect()
ami.originate_call(
    phone_number="+491234567890",
    context="outbound-calls",
    extension="s"
)
ami.disconnect()
```

## 📁 Project Structure

```
aiagc/
├── src/
│   ├── asterisk/          # Asterisk integration
│   │   ├── agi_interface.py    # AGI and AMI interfaces
│   │   └── call_handler.py     # Main call orchestration
│   ├── speech/            # Speech recognition and synthesis
│   │   ├── deepgram_stt.py     # Deepgram STT
│   │   ├── whisper_stt.py      # Whisper STT fallback
│   │   └── tts.py              # Text-to-speech
│   ├── ai/                # AI and NLP
│   │   └── intent_detector.py  # Intent detection
│   ├── dialogue/          # Conversation management
│   │   ├── dialogue_generator.py  # Response generation
│   │   └── call_flow.py        # Call flow state machine
│   ├── models/            # Data models
│   │   └── call_state.py       # Call and lead models
│   ├── utils/             # Utilities
│   │   ├── helpers.py          # Helper functions
│   │   └── logging_config.py   # Logging setup
│   └── config.py          # Configuration
├── config/
│   └── asterisk/          # Asterisk configuration files
│       ├── extensions.conf     # Dialplan
│       ├── manager.conf        # AMI config
│       └── pjsip.conf          # SIP trunk config
├── logs/                  # Application logs
├── recordings/            # Call recordings
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker setup
├── Dockerfile            # Docker image
├── .env.example          # Environment template
└── README.md             # This file
```

## 🎯 Use Cases

### Investment Products
The AI agent engages potential investors with:
- Personalized investment opportunity presentations
- ROI calculations and projections
- Risk assessment discussions
- Portfolio diversification advice

### Arbitrage Opportunities
- Explains arbitrage strategies
- Identifies qualified investors
- Schedules detailed consultations
- Handles objections professionally

### Lead Qualification
Automatically qualifies leads based on:
- Investment interest level
- Available budget/capital
- Decision-making authority
- Timeline for investment
- Risk tolerance

## 🔧 Configuration

### Call Flow Customization

Edit `src/dialogue/call_flow.py` to customize:
- Conversation phases
- Qualification criteria
- Lead scoring algorithm
- Phase transitions

### Dialogue Templates

Modify `src/dialogue/dialogue_generator.py` to adjust:
- Opening statements
- Product presentations
- Objection handling
- Closing strategies

### Intent Detection

Customize `src/ai/intent_detector.py` for:
- Additional intent types
- Industry-specific terminology
- Custom entity extraction

## 📊 Lead Scoring

The system scores leads (0-100) based on:

| Criterion | Points |
|-----------|--------|
| Investment Interest | 30 |
| Budget Available | 25 |
| Decision Maker | 20 |
| Positive Sentiment | 15 |
| Engagement Level | 10 |

Leads scoring 70+ are marked as qualified.

## 🔒 Security & Compliance

- All call data encrypted in transit and at rest
- GDPR-compliant data handling
- Call recording with consent
- PII masking in logs
- Secure API key management
- Financial services compliance ready

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Test individual components:

```bash
# Test speech recognition
python -m src.speech.deepgram_stt

# Test dialogue generation
python -m src.dialogue.dialogue_generator

# Test intent detection
python -m src.ai.intent_detector
```

## 📝 Logging

Logs are stored in:
- Console: Real-time output
- File: `logs/aiagc.log`
- Rotation: 500 MB
- Retention: 30 days

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🐛 Troubleshooting

### Asterisk Connection Issues
```bash
# Check Asterisk status
docker exec aiagc-asterisk asterisk -rx "core show version"

# Test AMI connection
docker exec aiagc-asterisk asterisk -rx "manager show connected"
```

### Speech Recognition Issues
- Verify Deepgram API key is valid
- Check internet connectivity
- Ensure audio sample rate is 16000 Hz
- Check Whisper model is downloaded

### Database Issues
```bash
# Check PostgreSQL status
docker exec aiagc-postgres pg_isready

# View logs
docker logs aiagc-postgres
```

## 🚀 Production Deployment

### Scaling Considerations

1. **Concurrent Calls**: Adjust Asterisk channel limits
2. **Database**: Use connection pooling
3. **Redis**: Consider Redis Cluster for high availability
4. **API Rate Limits**: Implement backoff strategies
5. **Load Balancing**: Use multiple AI agent instances

### Monitoring

Integrate with:
- Prometheus for metrics
- Grafana for dashboards
- Sentry for error tracking
- ELK stack for log aggregation

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Asterisk for telephony infrastructure
- Deepgram for real-time speech recognition
- OpenAI for GPT-4 and Whisper
- The open-source community

## 📧 Contact

For support or questions:
- GitHub Issues: [github.com/Pormetrixx/aiagc/issues](https://github.com/Pormetrixx/aiagc/issues)
- Email: [your-email@example.com]

## 🗺️ Roadmap

- [ ] Multi-language support (English, French, Spanish)
- [ ] Advanced analytics dashboard
- [ ] CRM integrations (Salesforce, HubSpot)
- [ ] Voice cloning for brand consistency
- [ ] A/B testing framework for dialogue optimization
- [ ] Real-time coaching for human agent takeover
- [ ] Mobile app for call monitoring
- [ ] WebRTC support for browser-based calling

---

**Built with ❤️ for professional outbound calling automation**
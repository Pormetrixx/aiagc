# Quick Start Guide

Get your AI calling agent up and running in 10 minutes!

## Prerequisites Checklist

- [ ] Linux server (Ubuntu 20.04+ recommended)
- [ ] Python 3.11+
- [ ] Docker and Docker Compose installed
- [ ] Deepgram API key ([Get it here](https://deepgram.com))
- [ ] OpenAI API key ([Get it here](https://platform.openai.com))
- [ ] SIP trunk account (Twilio, Vonage, or other provider)

## Installation Steps

### 1. Clone and Setup (2 minutes)

```bash
git clone https://github.com/Pormetrixx/aiagc.git
cd aiagc
./setup.sh
```

### 2. Configure API Keys (3 minutes)

```bash
cp .env.example .env
nano .env
```

Update these essential values:
```bash
DEEPGRAM_API_KEY=your_deepgram_key_here
OPENAI_API_KEY=your_openai_key_here
ASTERISK_CALLER_ID=+4912345678
```

### 3. Configure SIP Trunk (3 minutes)

Edit `config/asterisk/pjsip.conf`:

```bash
nano config/asterisk/pjsip.conf
```

Replace placeholders:
- `YOUR_SIP_USERNAME` → Your SIP account username
- `YOUR_SIP_PASSWORD` → Your SIP account password
- `YOUR_SIP_PROVIDER` → Your provider's SIP server

**Example for Twilio:**
```ini
username=your_twilio_account_sid
password=your_twilio_auth_token
contact=sip:your_number@pstn.twilio.com
```

### 4. Start Services (2 minutes)

```bash
docker-compose up -d
```

Verify everything is running:
```bash
docker-compose ps
```

You should see 4 services running:
- aiagc-asterisk
- aiagc-postgres
- aiagc-redis
- aiagc-app

## Making Your First Call

### Test Call

Edit `examples/make_calls.py`:

```python
phone_number = "+49123456789"  # Replace with your test number
```

Activate environment and run:

```bash
source venv/bin/activate
python examples/make_calls.py
```

### Expected Call Flow

1. **Call connects** (1-2 seconds)
2. **AI greets in German** (e.g., "Guten Tag! Mein Name ist...")
3. **Customer responds**
4. **AI detects intent and responds naturally**
5. **Conversation continues** for qualification
6. **Call ends** with appropriate closing

## Viewing Results

### Check Logs

```bash
# Application logs
tail -f logs/aiagc.log

# Docker logs
docker-compose logs -f aiagc-app
```

### Call Records

Call data is stored in PostgreSQL. Access:

```bash
docker exec -it aiagc-postgres psql -U aiagc aiagc_calls
```

Then query:
```sql
SELECT * FROM calls ORDER BY start_time DESC LIMIT 10;
```

## Common Issues & Quick Fixes

### "Connection refused" to Asterisk
```bash
docker restart aiagc-asterisk
docker logs aiagc-asterisk
```

### "API key invalid" errors
- Double-check your API keys in `.env`
- Ensure no extra spaces or quotes
- Restart: `docker-compose restart aiagc-app`

### No audio in calls
```bash
# Check firewall allows RTP ports
sudo ufw allow 10000:10100/udp
docker restart aiagc-asterisk
```

### Speech recognition not working
- Verify Deepgram API key
- Check internet connectivity
- View logs: `docker-compose logs aiagc-app | grep -i deepgram`

## Next Steps

### Customize Dialogue

Edit `src/dialogue/dialogue_generator.py` to customize:
- Opening statements
- Sales pitch
- Objection handling
- Closing strategies

### Adjust Lead Scoring

Edit `src/dialogue/call_flow.py` to modify:
- Qualification criteria
- Lead scoring algorithm
- Phase transitions

### Scale Up

For production:
1. Review `docs/DEPLOYMENT.md`
2. Implement monitoring
3. Setup backups
4. Configure SSL/TLS
5. Add load balancing

## Testing Checklist

Before going live, test:

- [ ] Can initiate outbound calls
- [ ] Speech recognition works in German
- [ ] AI responds naturally
- [ ] Intent detection is accurate
- [ ] Lead scoring works correctly
- [ ] Call records are saved
- [ ] Logs are being written
- [ ] Can transfer to human agent
- [ ] Callback scheduling works

## Support

Having issues? Check:

1. **Logs**: `docker-compose logs -f`
2. **Documentation**: See `docs/` folder
3. **GitHub Issues**: Report bugs or ask questions

## Production Deployment

Ready for production? Follow the full deployment guide:

```bash
cat docs/DEPLOYMENT.md
```

Key production steps:
1. Use strong passwords
2. Enable SSL/TLS
3. Configure firewall
4. Setup monitoring
5. Implement backups
6. Test thoroughly

## Performance Benchmarks

Expected performance on recommended hardware:

| Metric | Value |
|--------|-------|
| Concurrent calls | 10-50 (depends on server) |
| Speech recognition latency | <500ms |
| AI response time | 1-3 seconds |
| Call success rate | >90% |
| Lead qualification rate | 15-30% |

## Costs Estimation

Monthly costs (approximate):

- **Deepgram**: $0.0043/min → ~$26 for 100 hours
- **OpenAI GPT-4**: $0.03/1K tokens → ~$100 for 1000 calls
- **SIP Trunk**: Varies by provider → ~$0.01-0.10/minute
- **Server**: $20-100/month (DigitalOcean, AWS, etc.)

**Total for 1000 calls/month**: ~$200-400

## Quick Reference Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart aiagc-app

# Check Asterisk
docker exec aiagc-asterisk asterisk -rx "core show version"

# Access database
docker exec -it aiagc-postgres psql -U aiagc aiagc_calls

# Make test call
python examples/make_calls.py

# View call recordings
ls -lh recordings/
```

## Need Help?

- 📖 **Full Documentation**: See `README.md`
- 🚀 **Deployment Guide**: See `docs/DEPLOYMENT.md`
- 💬 **Conversation Scripts**: See `docs/conversation_scripts.md`
- 🐛 **Report Issues**: GitHub Issues
- 📧 **Contact**: [Add your contact]

---

**You're ready to go! 🎉**

Make your first call and start generating qualified leads!

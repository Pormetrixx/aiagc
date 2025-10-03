# Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Python 3.11+
- Docker and Docker Compose
- SIP trunk provider account
- Domain name (optional but recommended)
- SSL certificates (for production)

## API Keys Required

1. **Deepgram** - https://deepgram.com
   - Sign up for account
   - Get API key from console
   - Recommended: Pay-as-you-go plan

2. **OpenAI** - https://platform.openai.com
   - Create account
   - Generate API key
   - Ensure billing is set up for GPT-4 access

3. **Optional: Anthropic** - https://www.anthropic.com
   - For Claude AI as alternative/backup

## Step-by-Step Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3 python3-pip python3-venv docker.io docker-compose

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clone Repository

```bash
# Clone the repository
git clone https://github.com/Pormetrixx/aiagc.git
cd aiagc

# Run setup script
chmod +x setup.sh
./setup.sh
```

### 3. Configure Environment

Edit `.env` file:

```bash
nano .env
```

Key configurations:

```bash
# Deepgram (required)
DEEPGRAM_API_KEY=your_actual_deepgram_key

# OpenAI (required)
OPENAI_API_KEY=your_actual_openai_key

# Asterisk
ASTERISK_HOST=asterisk
ASTERISK_USERNAME=admin
ASTERISK_SECRET=change_this_strong_password
ASTERISK_CALLER_ID=+49123456789  # Your caller ID

# Database
DATABASE_URL=postgresql://aiagc:strong_password_here@postgres:5432/aiagc_calls

# Redis
REDIS_HOST=redis
REDIS_PASSWORD=optional_redis_password
```

### 4. Configure Asterisk

#### a. Edit SIP Trunk Configuration

```bash
nano config/asterisk/pjsip.conf
```

Update with your SIP provider details:

```ini
[trunk-auth]
type=auth
auth_type=userpass
username=YOUR_ACTUAL_SIP_USERNAME
password=YOUR_ACTUAL_SIP_PASSWORD

[trunk-aor]
type=aor
contact=sip:YOUR_PROVIDER_HOST:5060

[trunk-identify]
type=identify
endpoint=trunk
match=YOUR_PROVIDER_IP
```

#### b. Common SIP Providers

**Twilio**:
```ini
username=your_twilio_sid
password=your_twilio_auth_token
contact=sip:your_number@pstn.twilio.com
```

**Vonage (Nexmo)**:
```ini
username=your_nexmo_key
password=your_nexmo_secret
contact=sip:sip.nexmo.com
```

### 5. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 6. Verify Installation

```bash
# Check Asterisk
docker exec aiagc-asterisk asterisk -rx "core show version"

# Check database connection
docker exec aiagc-postgres pg_isready

# Check Redis
docker exec aiagc-redis redis-cli ping
```

### 7. Test Call

Edit `examples/make_calls.py` with a test number:

```python
phone_number = "+49123456789"  # Your test number
```

Run test:

```bash
source venv/bin/activate
python examples/make_calls.py
```

## Production Configuration

### Security Hardening

1. **Firewall Configuration**

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5060/udp  # SIP
sudo ufw allow 5038/tcp  # AMI (only from trusted IPs)
sudo ufw allow 10000:10100/udp  # RTP
sudo ufw enable
```

2. **Secure Asterisk AMI**

Edit `config/asterisk/manager.conf`:

```ini
[admin]
secret = very_strong_random_password_here
permit = 172.18.0.0/255.255.0.0  # Docker network only
deny = 0.0.0.0/0.0.0.0
```

3. **Database Security**

```bash
# Use strong passwords in docker-compose.yml
# Enable SSL for PostgreSQL connections
# Restrict database access to Docker network only
```

4. **API Key Security**

```bash
# Never commit .env to git
# Use secrets management (HashiCorp Vault, AWS Secrets Manager)
# Rotate keys regularly
```

### SSL/TLS Configuration

For SIP over TLS (SIPS):

1. Obtain SSL certificates (Let's Encrypt)
2. Configure in `pjsip.conf`:

```ini
[transport-tls]
type=transport
protocol=tls
bind=0.0.0.0:5061
cert_file=/path/to/cert.pem
priv_key_file=/path/to/privkey.pem
ca_list_file=/path/to/chain.pem
```

### Monitoring Setup

1. **Prometheus + Grafana**

```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

2. **Logging**

```bash
# Configure log rotation
sudo nano /etc/logrotate.d/aiagc
```

```
/path/to/aiagc/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 user group
    sharedscripts
}
```

### Scaling for Production

1. **Multiple AI Agent Instances**

```yaml
# In docker-compose.yml
aiagc-app:
  # ... existing config
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

2. **Database Connection Pooling**

Add to your code:

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

3. **Redis Cluster**

For high availability, use Redis Cluster:

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes
```

### Backup Strategy

1. **Database Backups**

```bash
# Daily backup script
docker exec aiagc-postgres pg_dump -U aiagc aiagc_calls > backup_$(date +%Y%m%d).sql

# Automated backups
crontab -e
# Add: 0 2 * * * /path/to/backup_script.sh
```

2. **Configuration Backups**

```bash
# Backup config directory
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
```

### Performance Optimization

1. **Asterisk Tuning**

Edit `/etc/asterisk/asterisk.conf`:

```ini
[options]
maxcalls=100
maxload=2.0
```

2. **PostgreSQL Tuning**

Edit database configuration:

```sql
shared_buffers = 256MB
work_mem = 16MB
maintenance_work_mem = 128MB
effective_cache_size = 1GB
```

3. **Python Process Manager**

Use Gunicorn for production:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Troubleshooting

### Common Issues

1. **No Audio in Calls**

```bash
# Check RTP ports
docker logs aiagc-asterisk | grep RTP

# Verify firewall allows RTP range
sudo ufw status
```

2. **API Rate Limits**

- Implement exponential backoff
- Use multiple API keys in rotation
- Cache common responses

3. **Database Connection Errors**

```bash
# Check PostgreSQL logs
docker logs aiagc-postgres

# Verify connection from app
docker exec aiagc-app python -c "from src.config import settings; print(settings.database_url)"
```

4. **Speech Recognition Issues**

- Check Deepgram API key validity
- Verify internet connectivity
- Ensure audio format is correct (16kHz, mono)
- Check Whisper model download

### Health Checks

Create monitoring script:

```bash
#!/bin/bash
# health_check.sh

# Check services
docker-compose ps | grep "Up" || exit 1

# Check Asterisk
docker exec aiagc-asterisk asterisk -rx "core show uptime" || exit 1

# Check database
docker exec aiagc-postgres pg_isready || exit 1

# Check Redis
docker exec aiagc-redis redis-cli ping || exit 1

echo "All services healthy"
```

## Support & Maintenance

### Regular Maintenance

1. Update dependencies monthly
2. Rotate API keys quarterly
3. Review and optimize database
4. Monitor logs for errors
5. Test call quality regularly

### Monitoring Metrics

Track these KPIs:

- Call success rate
- Average call duration
- Lead qualification rate
- API latency
- System resource usage
- Error rates

## Rollback Procedure

If issues occur:

```bash
# Stop services
docker-compose down

# Restore from backup
git checkout <previous-commit>

# Restore database
docker exec -i aiagc-postgres psql -U aiagc aiagc_calls < backup.sql

# Restart
docker-compose up -d
```

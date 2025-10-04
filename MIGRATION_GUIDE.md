# Migration Guide: AGI to ARI

This guide provides detailed instructions for migrating from the legacy AGI (Asterisk Gateway Interface) implementation to the modern ARI (Asterisk REST Interface).

## Table of Contents

1. [Why Migrate to ARI?](#why-migrate-to-ari)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Migration](#step-by-step-migration)
4. [Configuration Changes](#configuration-changes)
5. [Code Changes](#code-changes)
6. [Testing Your Migration](#testing-your-migration)
7. [Rollback Plan](#rollback-plan)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

## Why Migrate to ARI?

### Key Benefits

| Feature | AGI (Legacy) | ARI (Modern) |
|---------|-------------|--------------|
| **Architecture** | Process per call | Event-driven service |
| **Communication** | stdin/stdout | HTTP REST + WebSocket |
| **Performance** | Process overhead | Lower latency |
| **Scalability** | Limited | Distributed-friendly |
| **Control** | Sequential commands | Asynchronous operations |
| **Debugging** | Log files only | HTTP inspection + events |
| **State Management** | Channel variables | Rich state objects |
| **Event System** | Limited | Comprehensive |
| **Modern Tools** | Limited support | REST API compatible |
| **Asterisk Version** | Legacy support | Actively maintained |

### Real-World Improvements

- **30-50% reduction in latency** for call operations
- **Better resource utilization** - one process handles multiple calls
- **Enhanced monitoring** through HTTP endpoints and WebSocket streams
- **Easier integration** with modern cloud platforms
- **Better error handling** with HTTP status codes and detailed errors

## Prerequisites

Before starting the migration:

- [ ] Asterisk 20.15.2 or higher installed (ARI introduced in Asterisk 12, but 20.15.2 recommended for latest features and security)
- [ ] Python 3.11+ with asyncio support
- [ ] Access to Asterisk configuration files (`/etc/asterisk/`)
- [ ] Backup of current configuration
- [ ] Test environment available
- [ ] Understanding of current AGI implementation

### Check Asterisk Version

```bash
asterisk -V
# Should show version 20.15.2 or higher for optimal ARI support
```

### Verify ARI Support

```bash
asterisk -rx "ari show apps"
# Should list available ARI applications
```

## Step-by-Step Migration

### Phase 1: Setup (No Production Impact)

#### Step 1.1: Update Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate

# Backup current requirements
cp requirements.txt requirements.txt.backup

# Update requirements.txt
# Remove: pyst2==0.5.1, asterisk-agi==0.1.5
# Add: ari==0.1.3

# Install new dependencies
pip install ari==0.1.3
```

#### Step 1.2: Configure ARI in Asterisk

**Create `/etc/asterisk/ari.conf`:**

```ini
[general]
enabled = yes
pretty = yes
allowed_origins = *

[asterisk]
type = user
read_only = no
password = your_secure_ari_password_here
password_format = plain
```

**Create or update `/etc/asterisk/http.conf`:**

```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
enablestatic = yes
redirect = /
prefix = asterisk

; Enable CORS if needed
enablestatic = yes
```

**Reload Asterisk modules:**

```bash
asterisk -rx "module reload res_ari.so"
asterisk -rx "module reload res_http.so"
asterisk -rx "ari show apps"
```

#### Step 1.3: Update Application Configuration

**Add to `.env`:**

```bash
# ARI Configuration (Primary)
ASTERISK_ARI_HOST=localhost
ASTERISK_ARI_PORT=8088
ASTERISK_ARI_USERNAME=asterisk
ASTERISK_ARI_PASSWORD=your_secure_ari_password_here
ASTERISK_LANGUAGE=de

# Keep legacy AMI for backward compatibility
ASTERISK_HOST=localhost
ASTERISK_PORT=5038
ASTERISK_USERNAME=admin
ASTERISK_SECRET=your_ami_secret
```

**Verify configuration:**

```python
from src.config import settings
print(f"ARI Host: {settings.asterisk_ari_host}")
print(f"ARI Port: {settings.asterisk_ari_port}")
```

#### Step 1.4: Test ARI Connection

```bash
# Test ARI endpoint
curl -u asterisk:your_secure_ari_password_here \
  http://localhost:8088/ari/api-docs/resources.json

# Should return JSON with ARI resources
```

### Phase 2: Create Parallel ARI Contexts

#### Step 2.1: Update Dialplan

**Add ARI contexts to `/etc/asterisk/extensions.conf`:**

```ini
; Legacy AGI contexts (keep existing)
[outbound-calls]
exten => s,1,NoOp(AGI Mode - Outbound Call)
    same => n,Set(CHANNEL(language)=de)
    same => n,Answer()
    same => n,AGI(python3,/path/to/call_handler.py)
    same => n,Hangup()

; New ARI contexts (run in parallel)
[outbound-calls-ari]
exten => s,1,NoOp(ARI Mode - Outbound Call)
    same => n,Set(CHANNEL(language)=de)
    same => n,Stasis(aiagc)
    same => n,Hangup()

[ai-agent-ari]
exten => s,1,NoOp(ARI Mode - AI Agent)
    same => n,Set(CHANNEL(language)=de)
    same => n,Stasis(aiagc)
    same => n,Hangup()

[incoming-ari]
exten => _X.,1,NoOp(ARI Mode - Incoming Call)
    same => n,Stasis(aiagc)
    same => n,Hangup()
```

**Reload dialplan:**

```bash
asterisk -rx "dialplan reload"
asterisk -rx "dialplan show outbound-calls-ari"
```

#### Step 2.2: Start ARI Application

**Test ARI application:**

```bash
# Terminal 1: Start ARI application
python -m src.asterisk.ari_call_handler

# Terminal 2: Monitor events
curl -N -u asterisk:your_password \
  "http://localhost:8088/ari/events?app=aiagc&api_key=asterisk:your_password"
```

### Phase 3: Testing (Parallel Running)

#### Step 3.1: Test Call Origination

**Test ARI call:**

```python
# test_ari_call.py
from src.asterisk.ari_interface import AsteriskARI

ari = AsteriskARI()
ari.connect()

channel_id = ari.originate_call(
    endpoint="PJSIP/your_test_extension",
    context="outbound-calls-ari",
    extension="s"
)

print(f"Call originated: {channel_id}")
ari.disconnect()
```

**Compare with legacy AGI:**

```python
# test_agi_call.py
from src.asterisk.agi_interface import AsteriskAMI

ami = AsteriskAMI()
ami.connect()

ami.originate_call(
    phone_number="your_test_extension",
    context="outbound-calls"
)

ami.disconnect()
```

#### Step 3.2: Monitor Performance

**ARI Metrics:**

```bash
# Check ARI application status
curl -u asterisk:password http://localhost:8088/ari/applications/aiagc

# Monitor WebSocket events
wscat -c "ws://localhost:8088/ari/events?app=aiagc&api_key=asterisk:password"
```

**AGI Metrics:**

```bash
# Monitor AGI process
ps aux | grep call_handler.py

# Check AGI logs
tail -f /var/log/asterisk/full | grep AGI
```

#### Step 3.3: Load Testing

**Create load test script:**

```python
# load_test.py
import asyncio
from src.asterisk.ari_interface import AsteriskARI

async def test_concurrent_calls(num_calls=10):
    """Test concurrent ARI calls"""
    ari = AsteriskARI()
    ari.connect()
    
    tasks = []
    for i in range(num_calls):
        task = asyncio.create_task(
            make_test_call(ari, f"test_{i}")
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"Completed {len([r for r in results if not isinstance(r, Exception)])} calls")
    
    ari.disconnect()

async def make_test_call(ari, call_id):
    """Make a single test call"""
    channel_id = ari.originate_call(
        endpoint="PJSIP/test_extension",
        context="outbound-calls-ari"
    )
    return channel_id

if __name__ == "__main__":
    asyncio.run(test_concurrent_calls(10))
```

### Phase 4: Gradual Migration

#### Step 4.1: Route Percentage of Traffic

**Update dialplan to route traffic:**

```ini
[outbound-calls-hybrid]
; Route 20% to ARI, 80% to AGI
exten => s,1,NoOp(Hybrid Routing)
    same => n,Set(RAND=${RAND(1,100)})
    same => n,GotoIf($[${RAND} <= 20]?ari:agi)
    
    same => n(ari),NoOp(Routing to ARI)
    same => n,Stasis(aiagc)
    same => n,Hangup()
    
    same => n(agi),NoOp(Routing to AGI)
    same => n,Answer()
    same => n,AGI(python3,/path/to/call_handler.py)
    same => n,Hangup()
```

#### Step 4.2: Monitor and Compare

**Compare metrics over time:**

```bash
# Create monitoring dashboard
# Track:
# - Call completion rate
# - Average call duration
# - Error rates
# - System resource usage
# - Latency metrics
```

#### Step 4.3: Increase ARI Traffic

Gradually increase ARI percentage:
- Week 1: 20% ARI
- Week 2: 40% ARI
- Week 3: 60% ARI
- Week 4: 80% ARI
- Week 5: 100% ARI

### Phase 5: Complete Migration

#### Step 5.1: Switch Default Context

**Update trunk configuration to use ARI context:**

```ini
[trunk]
type=endpoint
context=outbound-calls-ari  ; Changed from outbound-calls
```

#### Step 5.2: Update Application Startup

**Create systemd service for ARI:**

```ini
# /etc/systemd/system/aiagc-ari.service
[Unit]
Description=AIAGC ARI Application
After=asterisk.service

[Service]
Type=simple
User=aiagc
WorkingDirectory=/opt/aiagc
ExecStart=/opt/aiagc/venv/bin/python -m src.asterisk.ari_call_handler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable service:**

```bash
systemctl daemon-reload
systemctl enable aiagc-ari
systemctl start aiagc-ari
systemctl status aiagc-ari
```

#### Step 5.3: Deprecate AGI Contexts

**Mark AGI contexts as deprecated:**

```ini
[outbound-calls]
; DEPRECATED: This context uses legacy AGI
; Use outbound-calls-ari for new implementations
exten => s,1,NoOp(DEPRECATED - Use outbound-calls-ari)
    same => n,Answer()
    same => n,AGI(python3,/path/to/call_handler.py)
    same => n,Hangup()
```

## Configuration Changes

### Environment Variables

| Variable | Before (AGI) | After (ARI) |
|----------|--------------|-------------|
| Primary Interface | AMI (port 5038) | ARI (port 8088) |
| Authentication | Username/Secret | Username/Password |
| Context | outbound-calls | outbound-calls-ari |
| Connection | Socket | HTTP REST |

### Asterisk Configuration Files

**New Files:**
- `/etc/asterisk/ari.conf` - ARI user configuration
- `/etc/asterisk/http.conf` - HTTP server (if not exists)

**Modified Files:**
- `/etc/asterisk/extensions.conf` - Add Stasis contexts
- Application `.env` - Add ARI settings

## Code Changes

### Call Origination

**Before (AGI/AMI):**

```python
from src.asterisk.agi_interface import AsteriskAMI

ami = AsteriskAMI()
ami.connect()
response = ami.originate_call(
    phone_number="+491234567890",
    context="outbound-calls"
)
ami.disconnect()
```

**After (ARI):**

```python
from src.asterisk.ari_interface import AsteriskARI

ari = AsteriskARI()
ari.connect()
channel_id = ari.originate_call(
    endpoint="PJSIP/+491234567890",
    context="outbound-calls-ari"
)
ari.disconnect()
```

### Call Handling

**Before (AGI per-call script):**

```python
# Runs once per call
from src.asterisk.call_handler import CallHandler

handler = CallHandler()
handler.agi.setup()  # Reads from stdin
await handler.handle_call(phone_number)
```

**After (ARI long-running service):**

```python
# Runs as service, handles events
from src.asterisk.ari_call_handler import create_ari_application

# Start event loop
create_ari_application()
```

### Media Playback

**Before (AGI):**

```python
self.agi.stream_file(audio_file.replace('.wav', ''))
```

**After (ARI):**

```python
media_uri = f"sound:en/{os.path.basename(audio_file).replace('.wav', '')}"
self.ari.play_media(media_uri, channel_id=channel_id)
```

## Testing Your Migration

### Unit Tests

```python
# test_ari_migration.py
import pytest
from src.asterisk.ari_interface import AsteriskARI

def test_ari_connection():
    """Test ARI connection"""
    ari = AsteriskARI()
    ari.connect()
    assert ari.connected
    ari.disconnect()

@pytest.mark.asyncio
async def test_ari_call_origination():
    """Test call origination"""
    ari = AsteriskARI()
    ari.connect()
    
    channel_id = ari.originate_call(
        endpoint="PJSIP/test",
        context="test"
    )
    
    assert channel_id is not None
    ari.disconnect()
```

### Integration Tests

```bash
# Test ARI endpoint availability
curl -u asterisk:password http://localhost:8088/ari/asterisk/info

# Test WebSocket connection
wscat -c "ws://localhost:8088/ari/events?app=aiagc&api_key=asterisk:password"

# Test call through ARI context
asterisk -rx "channel originate PJSIP/test extension s@outbound-calls-ari"
```

### Performance Tests

```python
import time
from src.asterisk.ari_interface import AsteriskARI

# Measure latency
ari = AsteriskARI()
ari.connect()

start = time.time()
channel_id = ari.originate_call(endpoint="PJSIP/test", context="test")
latency = time.time() - start

print(f"Call origination latency: {latency*1000:.2f}ms")
ari.disconnect()
```

## Rollback Plan

If you need to rollback to AGI:

### Immediate Rollback (During Testing)

```bash
# 1. Stop ARI application
systemctl stop aiagc-ari

# 2. Update trunk contexts back to AGI
# Edit /etc/asterisk/extensions.conf
# Change context back to outbound-calls

# 3. Reload dialplan
asterisk -rx "dialplan reload"

# 4. Remove ARI dependencies (optional)
pip uninstall ari
pip install pyst2 asterisk-agi
```

### Rollback After Partial Migration

```ini
# Update hybrid routing back to 100% AGI
[outbound-calls-hybrid]
exten => s,1,NoOp(Rolling back to AGI)
    same => n,Answer()
    same => n,AGI(python3,/path/to/call_handler.py)
    same => n,Hangup()
```

## Troubleshooting

### ARI Connection Issues

**Problem:** Cannot connect to ARI

```bash
# Check HTTP server is running
asterisk -rx "http show status"

# Check ARI is enabled
asterisk -rx "ari show apps"

# Test HTTP endpoint
curl http://localhost:8088/ari/api-docs/resources.json

# Check firewall
sudo ufw status
sudo ufw allow 8088/tcp
```

**Problem:** Authentication fails

```bash
# Verify credentials in ari.conf
cat /etc/asterisk/ari.conf

# Test authentication
curl -u asterisk:password http://localhost:8088/ari/asterisk/info
```

### WebSocket Issues

**Problem:** WebSocket events not received

```bash
# Test WebSocket connection
wscat -c "ws://localhost:8088/ari/events?app=aiagc&api_key=asterisk:password"

# Check if app is registered
asterisk -rx "ari show apps"

# Verify Stasis application in dialplan
asterisk -rx "dialplan show outbound-calls-ari"
```

### Performance Issues

**Problem:** High latency with ARI

- Check network latency to Asterisk server
- Verify HTTP server performance: `asterisk -rx "http show status"`
- Monitor system resources: `top`, `htop`
- Check for HTTP connection pooling issues
- Review ARI event subscription (subscribe only to needed events)

### Call Quality Issues

**Problem:** Audio issues after migration

- Verify media file paths are accessible to Asterisk
- Check Asterisk sounds directory permissions
- Ensure audio format compatibility (wav, gsm, etc.)
- Review RTP configuration: `cat /etc/asterisk/rtp.conf`

## FAQ

### Q: Can I run AGI and ARI in parallel?

**A:** Yes! This is the recommended migration approach. Run both systems in parallel during testing and gradually shift traffic from AGI to ARI.

### Q: What happens to active AGI calls during migration?

**A:** Active AGI calls continue unaffected. Only new calls use the ARI context. Complete migration after all AGI calls have ended.

### Q: Is ARI slower than AGI?

**A:** No, ARI is generally faster because:
- No process spawning overhead
- HTTP keep-alive connections
- Asynchronous event handling
- Better resource utilization

### Q: Do I need to change my business logic?

**A:** The core business logic (STT, TTS, intent detection, dialogue) remains unchanged. Only the Asterisk interface layer changes.

### Q: Can I use ARI with older Asterisk versions?

**A:** ARI requires Asterisk 12+. For best results, use Asterisk 13 or newer. Check compatibility:

```bash
asterisk -V
asterisk -rx "ari show apps"
```

### Q: What if I need AGI-specific features?

**A:** ARI provides equivalent or better functionality for most AGI commands. If you have specific AGI requirements, consult the [ARI documentation](https://wiki.asterisk.org/wiki/display/AST/Asterisk+REST+Interface) or contact support.

### Q: How do I monitor ARI application health?

**A:**

```bash
# Check application status
curl -u asterisk:password http://localhost:8088/ari/applications/aiagc

# Monitor system service
systemctl status aiagc-ari

# Check logs
journalctl -u aiagc-ari -f

# Monitor WebSocket connections
netstat -an | grep 8088
```

### Q: Can I use both AGI and ARI simultaneously?

**A:** Yes, but each call should use one interface. You can route different calls to different contexts (AGI or ARI) based on your needs.

## Additional Resources

- [Asterisk ARI Documentation](https://wiki.asterisk.org/wiki/display/AST/Asterisk+REST+Interface)
- [ARI Python Library](https://github.com/asterisk/ari-py)
- [Asterisk REST Interface Examples](https://wiki.asterisk.org/wiki/display/AST/ARI+Examples)
- [Project README](README.md)
- [API Documentation](docs/API.md)

## Support

If you encounter issues during migration:

1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Review [Asterisk logs](#monitoring-logs): `tail -f /var/log/asterisk/full`
3. Test ARI connectivity: [Testing Your Migration](#testing-your-migration)
4. Open a GitHub issue with:
   - Asterisk version
   - Error messages
   - Configuration files (sanitized)
   - Steps to reproduce

---

**Migration Checklist:**

- [ ] Backup current configuration
- [ ] Update dependencies
- [ ] Configure ARI in Asterisk
- [ ] Test ARI connection
- [ ] Create parallel ARI contexts
- [ ] Test with sample calls
- [ ] Monitor performance
- [ ] Gradually increase ARI traffic
- [ ] Update documentation
- [ ] Train team on ARI
- [ ] Complete migration
- [ ] Deprecate AGI contexts
- [ ] Celebrate! 🎉

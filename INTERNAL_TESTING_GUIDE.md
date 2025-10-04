# Internal Testing Guide - Step-by-Step Configuration

This guide provides detailed step-by-step instructions for configuring and testing the AIAGC system internally with extension calls before connecting to external trunk providers.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration Files Explained](#configuration-files-explained)
4. [Step-by-Step Internal Testing Setup](#step-by-step-internal-testing-setup)
5. [Testing Procedures](#testing-procedures)
6. [Troubleshooting](#troubleshooting)
7. [Adding External Trunk (Production)](#adding-external-trunk-production)

---

## Prerequisites

- Fresh Ubuntu 22.04 LTS installation
- Root/sudo access
- Network connectivity
- At least 4GB RAM
- 20GB free disk space

---

## Installation

### Step 1: Run the Installation Script

```bash
# Clone the repository
git clone https://github.com/Pormetrixx/aiagc.git
cd aiagc

# Run installation script (uses Asterisk 20.10.2)
sudo ./install.sh
```

The script will:
- Install system dependencies
- Download and compile Asterisk 20.10.2
- Configure internal test extensions (1000, 1001)
- Set up the AI agent application
- Create all necessary directories

**Installation time:** Approximately 15-20 minutes

---

## Configuration Files Explained

After installation, the following Asterisk configuration files are created in `/etc/asterisk/`:

### 1. `/etc/asterisk/pjsip.conf` - SIP Configuration

**Purpose:** Defines SIP endpoints, authentication, and transport settings.

**Key sections:**

```ini
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

[1000]                      # Internal test extension
type=endpoint
context=internal            # Where calls from this extension go
disallow=all
allow=ulaw                  # Audio codec
allow=alaw
allow=g722
auth=1000                   # Links to auth section
aors=1000                   # Links to address-of-record

[1000]
type=auth
auth_type=userpass
username=1000
password=test1000           # SIP password

[1000]
type=aor
max_contacts=1
remove_existing=yes

[1001]                      # AI Agent extension
type=endpoint
context=ai-agent            # Calls here go to AI agent
# ... similar structure
```

**What it does:**
- Extension 1000: Test caller (you call FROM here)
- Extension 1001: AI Agent (you call TO here)
- Both use UDP port 5060 for SIP signaling
- Audio codecs: ulaw, alaw, g722

### 2. `/etc/asterisk/extensions.conf` - Dialplan

**Purpose:** Defines call routing logic and what happens when extensions are dialed.

**Key contexts:**

```ini
[internal]
; When extension 1000 calls extension 1001
exten => 1001,1,NoOp(Calling AI Agent from internal extension)
    same => n,Set(CHANNEL(language)=de)
    same => n,Dial(PJSIP/1001,30)
    same => n,Hangup()

[ai-agent]
; What happens when a call reaches extension 1001 (AGI mode)
exten => s,1,NoOp(AI Agent Context - Call Received - AGI Mode)
    same => n,Set(CHANNEL(language)=de)
    same => n,Answer()
    same => n,Wait(1)
    same => n,AGI(python3,/opt/aiagc/src/asterisk/call_handler.py)
    same => n,Hangup()

[ai-agent-ari]
; What happens when a call reaches extension 1001 (ARI mode - recommended)
exten => s,1,NoOp(AI Agent Context - Call Received - ARI Mode)
    same => n,Set(CHANNEL(language)=de)
    same => n,Stasis(aiagc)
    same => n,Hangup()
```

**What it does:**
- `internal` context: Routes calls between internal extensions
- `ai-agent` context: Handles calls using legacy AGI
- `ai-agent-ari` context: Handles calls using modern ARI

### 3. `/etc/asterisk/manager.conf` - AMI Configuration

**Purpose:** Asterisk Manager Interface for call control and monitoring.

```ini
[general]
enabled = yes
port = 5038
bindaddr = 0.0.0.0

[admin]
secret = aiagc_admin_password_change_me
permit = 127.0.0.1/255.255.255.0
read = all
write = all
```

**What it does:**
- Enables AMI on port 5038
- Used for call origination (legacy AGI mode)
- Provides monitoring and control capabilities

### 4. `/etc/asterisk/ari.conf` - ARI Configuration

**Purpose:** Asterisk REST Interface configuration (modern API).

```ini
[general]
enabled = yes
pretty = yes
allowed_origins = *

[asterisk]
type = user
read_only = no
password = aiagc_ari_password_change_me
password_format = plain
```

**What it does:**
- Enables ARI on port 8088
- REST API + WebSocket for call control
- Modern replacement for AGI

### 5. `/etc/asterisk/http.conf` - HTTP Server

**Purpose:** Enables HTTP server required for ARI.

```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
enablestatic = yes
```

**What it does:**
- HTTP server on port 8088
- Required for ARI to work
- Provides REST API endpoints

### 6. `/etc/asterisk/rtp.conf` - RTP/Audio Configuration

**Purpose:** Defines RTP port range for audio streams.

```ini
[general]
rtpstart=10000
rtpend=10100
```

**What it does:**
- Allocates UDP ports 10000-10100 for audio
- Each active call uses 2 ports (RTP and RTCP)
- Can support ~50 concurrent calls

---

## Step-by-Step Internal Testing Setup

### Phase 1: Verify Asterisk Installation

#### Step 1.1: Check Asterisk Version

```bash
asterisk -V
# Expected output: Asterisk 20.10.2
```

#### Step 1.2: Check Asterisk Status

```bash
systemctl status asterisk
# Should show "active (running)"
```

#### Step 1.3: Connect to Asterisk Console

```bash
asterisk -rvvv
```

You should see:
```
Asterisk 20.10.2, Copyright (C) 1999 - 2024 Sangoma Technologies Corporation
*CLI>
```

Useful commands:
```bash
pjsip show endpoints     # Show SIP endpoints
dialplan show            # Show dialplan contexts
core show version        # Show Asterisk version
exit                     # Exit console
```

#### Step 1.4: Verify Configurations

```bash
# Check PJSIP configuration
asterisk -rx "pjsip show endpoints"
# Should show: 1000 and 1001

# Check dialplan
asterisk -rx "dialplan show"
# Should show contexts: internal, ai-agent, ai-agent-ari

# Check ARI
asterisk -rx "ari show apps"
# Should list available ARI applications

# Check HTTP status
asterisk -rx "http show status"
# Should show HTTP server enabled on port 8088
```

### Phase 2: Configure SIP Client

#### Step 2.1: Choose a SIP Client

**Desktop Options:**
- **Zoiper** (Recommended - Windows/Mac/Linux)
- **Linphone** (Open source)
- **MicroSIP** (Windows)
- **Bria** (Commercial)

**Mobile Options:**
- **Zoiper** (iOS/Android)
- **Linphone** (iOS/Android)

#### Step 2.2: Get Server IP Address

```bash
hostname -I | awk '{print $1}'
# Example: 192.168.1.100
```

#### Step 2.3: Configure Extension 1000 in SIP Client

**Account Settings:**
```
Account Name: Extension 1000
Username: 1000
Password: test1000
Domain: 192.168.1.100 (your server IP)
Port: 5060
Transport: UDP
```

**Zoiper Configuration:**
1. Open Zoiper
2. Settings → Accounts → Add Account
3. Choose "SIP"
4. Fill in:
   - Username: 1000
   - Password: test1000
   - Domain: 192.168.1.100
5. Advanced Settings:
   - Port: 5060
   - Transport: UDP
6. Save

#### Step 2.4: Verify Registration

In Asterisk console:
```bash
asterisk -rx "pjsip show endpoints"
```

You should see:
```
Endpoint:  1000/1000                                         Avail        1 of 1
```

If it shows "Unavail", check:
- Firewall settings (port 5060 UDP)
- Correct IP address
- SIP client configuration

### Phase 3: Configure Application

#### Step 3.1: Set Up Environment Variables

```bash
cd /opt/aiagc
nano .env
```

**For Internal Testing (Minimal Setup):**
```bash
# Environment
ENVIRONMENT=development

# Asterisk ARI (Primary - for modern interface)
ASTERISK_ARI_HOST=localhost
ASTERISK_ARI_PORT=8088
ASTERISK_ARI_USERNAME=asterisk
ASTERISK_ARI_PASSWORD=aiagc_ari_password_change_me
ASTERISK_LANGUAGE=de

# Asterisk AMI (Legacy - for AGI)
ASTERISK_HOST=localhost
ASTERISK_PORT=5038
ASTERISK_USERNAME=admin
ASTERISK_SECRET=aiagc_admin_password_change_me
ASTERISK_CONTEXT=ai-agent-ari
ASTERISK_CALLER_ID=+4912345678

# Speech Services (Optional for internal testing)
# DEEPGRAM_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here

# Call Configuration
MAX_CALL_DURATION=300
SILENCE_TIMEOUT=5
SPEECH_TIMEOUT=10

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/aiagc.log
```

**Note:** For basic testing, you don't need API keys. The system will log errors but continue.

#### Step 3.2: Activate Virtual Environment

```bash
cd /opt/aiagc
source venv/bin/activate
```

#### Step 3.3: Verify Installation

```bash
# Check Python packages
pip list | grep ari
# Should show: ari (0.1.3)

# Test imports
python3 -c "from src.asterisk.ari_interface import AsteriskARI; print('ARI import OK')"
python3 -c "from src.asterisk.agi_interface import AsteriskAGI; print('AGI import OK')"
```

### Phase 4: Testing - AGI Mode (Legacy)

#### Step 4.1: Update Extension 1001 for AGI

Make sure `/etc/asterisk/pjsip.conf` has:
```ini
[1001]
type=endpoint
context=ai-agent    # Uses AGI mode
```

Reload configuration:
```bash
asterisk -rx "pjsip reload"
asterisk -rx "dialplan reload"
```

#### Step 4.2: Test Simple AGI Script

Create a test script to verify AGI works:

```bash
cat > /tmp/test_agi.py << 'EOF'
#!/usr/bin/env python3
import sys

# Read AGI environment
env = {}
while True:
    line = sys.stdin.readline().strip()
    if not line:
        break
    key, value = line.split(': ', 1)
    env[key.replace('agi_', '')] = value

# Answer the call
sys.stdout.write("ANSWER\n")
sys.stdout.flush()
response = sys.stdin.readline().strip()

# Play a message
sys.stdout.write('VERBOSE "Test AGI script executed" 1\n')
sys.stdout.flush()
response = sys.stdin.readline().strip()

# Wait 2 seconds
sys.stdout.write("EXEC Wait 2\n")
sys.stdout.flush()
response = sys.stdin.readline().strip()

# Hangup
sys.stdout.write("HANGUP\n")
sys.stdout.flush()
EOF

chmod +x /tmp/test_agi.py
```

Update dialplan temporarily:
```bash
# Add to /etc/asterisk/extensions.conf in [ai-agent] context:
exten => s,1,NoOp(Testing AGI)
    same => n,Answer()
    same => n,AGI(/tmp/test_agi.py)
    same => n,Hangup()
```

```bash
asterisk -rx "dialplan reload"
```

#### Step 4.3: Make Test Call

1. From SIP client (extension 1000), dial: **1001**
2. Watch Asterisk console:
   ```bash
   asterisk -rvvv
   ```
3. You should see:
   - Call setup messages
   - AGI script execution
   - Call completion

#### Step 4.4: Check Logs

```bash
# Asterisk logs
tail -f /var/log/asterisk/full

# Application logs
tail -f /opt/aiagc/logs/aiagc.log
```

### Phase 5: Testing - ARI Mode (Modern/Recommended)

#### Step 5.1: Update Extension 1001 for ARI

Edit `/etc/asterisk/pjsip.conf`:
```ini
[1001]
type=endpoint
context=ai-agent-ari    # Uses ARI mode with Stasis
```

Reload:
```bash
asterisk -rx "pjsip reload"
asterisk -rx "dialplan reload"
```

#### Step 5.2: Test ARI Connectivity

```bash
# Test ARI HTTP endpoint
curl -u asterisk:aiagc_ari_password_change_me \
  http://localhost:8088/ari/asterisk/info

# Should return JSON with Asterisk info
```

#### Step 5.3: Start ARI Application

**Terminal 1 - Start ARI Application:**
```bash
cd /opt/aiagc
source venv/bin/activate
python -m src.asterisk.ari_call_handler
```

You should see:
```
Connected to Asterisk ARI at localhost:8088
ARI application started
```

#### Step 5.4: Monitor ARI Events

**Terminal 2 - Watch Events:**
```bash
curl -N -u asterisk:aiagc_ari_password_change_me \
  "http://localhost:8088/ari/events?app=aiagc&api_key=asterisk:aiagc_ari_password_change_me"
```

#### Step 5.5: Make Test Call

1. From SIP client (extension 1000), dial: **1001**
2. Watch Terminal 1 (ARI app) for:
   - "StasisStart: Channel entered application"
   - Call handling messages
3. Watch Terminal 2 for ARI events in JSON format

#### Step 5.6: Test Call Origination via ARI

Create a test script:

```bash
cat > /tmp/test_ari_call.py << 'EOF'
#!/usr/bin/env python3
from src.asterisk.ari_interface import AsteriskARI

ari = AsteriskARI()
ari.connect()

print("Originating call to extension 1000...")
channel_id = ari.originate_call(
    endpoint="PJSIP/1000",
    context="ai-agent-ari",
    extension="s"
)

print(f"Call originated: {channel_id}")
ari.disconnect()
EOF

cd /opt/aiagc
source venv/bin/activate
python /tmp/test_ari_call.py
```

Your SIP client should ring!

---

## Testing Procedures

### Test Suite 1: Basic Call Flow

**Test 1.1: Simple Internal Call**
```
Caller: Extension 1000
Callee: Extension 1001
Expected: Call connects, AI agent answers (or test script runs)
```

**Test 1.2: Call Duration**
```
Make a call and keep it active for 30 seconds
Expected: Call remains stable, no dropouts
```

**Test 1.3: Call Termination**
```
Hang up from caller side
Expected: Clean disconnect, no orphaned channels
```

**Test 1.4: Missed Call**
```
Call extension 1001, let it ring without answering (if possible)
Expected: Call eventually times out and disconnects
```

### Test Suite 2: Audio Quality

**Test 2.1: Audio Playback**
```
Modify dialplan to play a sound file:
exten => 1001,1,Answer()
    same => n,Playback(hello-world)
    same => n,Hangup()

Call 1001, listen for audio
Expected: Clear audio playback
```

**Test 2.2: Echo Test**
```
Use Asterisk's echo test:
exten => 600,1,Answer()
    same => n,Echo()
    same => n,Hangup()

Call 600, speak into microphone
Expected: Hear your voice echoed back with minimal delay
```

### Test Suite 3: ARI Features

**Test 3.1: Channel Information**
```python
from src.asterisk.ari_interface import AsteriskARI

ari = AsteriskARI()
ari.connect()

# During an active call, get channel info
channels = ari.client.channels.list()
for channel in channels:
    print(f"Channel: {channel.id}")
    print(f"State: {channel.json['state']}")
    print(f"Caller: {channel.json['caller']}")
```

**Test 3.2: Bridge Two Channels**
```python
# Originate two calls and bridge them
channel1 = ari.originate_call(endpoint="PJSIP/1000", app="aiagc")
channel2 = ari.originate_call(endpoint="PJSIP/1001", app="aiagc")

bridge_id = ari.create_bridge()
ari.add_channel_to_bridge(channel1, bridge_id)
ari.add_channel_to_bridge(channel2, bridge_id)

# Both extensions should be connected
```

### Test Suite 4: Monitoring

**Test 4.1: Active Channels**
```bash
asterisk -rx "core show channels"
# Shows all active calls
```

**Test 4.2: Endpoint Status**
```bash
asterisk -rx "pjsip show endpoints"
# Shows registration status of all endpoints
```

**Test 4.3: Call Statistics**
```bash
asterisk -rx "core show calls"
# Shows active call count and duration
```

**Test 4.4: RTP Statistics**
```bash
# During a call:
asterisk -rx "rtp show stats"
# Shows packet loss, jitter, etc.
```

---

## Troubleshooting

### Issue 1: SIP Client Won't Register

**Symptoms:** Endpoint shows "Unavail"

**Solutions:**

1. **Check firewall:**
   ```bash
   sudo ufw allow 5060/udp
   sudo ufw allow 10000:10100/udp
   ```

2. **Verify credentials:**
   ```bash
   asterisk -rx "pjsip show endpoint 1000"
   # Check auth configuration
   ```

3. **Check network:**
   ```bash
   netstat -ln | grep 5060
   # Should show Asterisk listening
   ```

4. **Test connectivity:**
   ```bash
   # From SIP client machine
   nc -u -v SERVER_IP 5060
   ```

### Issue 2: No Audio

**Symptoms:** Call connects but no audio

**Solutions:**

1. **Check RTP ports:**
   ```bash
   sudo ufw allow 10000:10100/udp
   ```

2. **Verify codec compatibility:**
   ```bash
   asterisk -rx "pjsip show endpoint 1000"
   # Check allowed codecs
   ```

3. **Check NAT settings:**
   If SIP client is behind NAT, may need STUN/TURN

4. **Test echo:**
   Call extension 600 (echo test) to verify bidirectional audio

### Issue 3: AGI Script Fails

**Symptoms:** Call connects but AGI doesn't execute

**Solutions:**

1. **Check script permissions:**
   ```bash
   ls -l /opt/aiagc/src/asterisk/call_handler.py
   chmod +x /opt/aiagc/src/asterisk/call_handler.py
   ```

2. **Verify Python path:**
   ```bash
   which python3
   # Use full path in dialplan
   ```

3. **Check logs:**
   ```bash
   tail -f /var/log/asterisk/full | grep AGI
   ```

4. **Test script manually:**
   ```bash
   echo -e "agi_network: no\nagi_request: test\n" | python3 /opt/aiagc/src/asterisk/call_handler.py
   ```

### Issue 4: ARI Connection Fails

**Symptoms:** Cannot connect to ARI

**Solutions:**

1. **Check HTTP server:**
   ```bash
   asterisk -rx "http show status"
   # Should show "Enabled"
   ```

2. **Verify port:**
   ```bash
   netstat -ln | grep 8088
   # Should show Asterisk listening
   ```

3. **Test endpoint:**
   ```bash
   curl -u asterisk:aiagc_ari_password_change_me \
     http://localhost:8088/ari/api-docs/resources.json
   ```

4. **Check credentials:**
   Verify `/etc/asterisk/ari.conf` password matches .env

### Issue 5: Call Drops After Few Seconds

**Symptoms:** Call disconnects unexpectedly

**Solutions:**

1. **Check RTP timeout:**
   ```bash
   # Add to /etc/asterisk/rtp.conf
   rtptimeout=60
   rtpholdtimeout=300
   ```

2. **Verify session timers:**
   ```bash
   # In pjsip.conf endpoint
   timers=no
   ```

3. **Check network stability:**
   ```bash
   ping -c 100 SERVER_IP
   # Check for packet loss
   ```

### Issue 6: Python Dependencies Missing

**Symptoms:** Import errors

**Solutions:**

```bash
cd /opt/aiagc
source venv/bin/activate
pip install -r requirements.txt

# Verify
pip list | grep -E "(ari|deepgram|openai)"
```

---

## Adding External Trunk (Production)

Once internal testing is successful, add external trunk provider:

### Step 1: Get Trunk Credentials

From your SIP trunk provider, you'll need:
- SIP server address (e.g., sip.provider.com)
- Username
- Password
- Authentication method
- Codecs supported

### Step 2: Configure Trunk in pjsip.conf

Edit `/etc/asterisk/pjsip.conf`, update the `[trunk]` section:

```ini
[trunk]
type=endpoint
context=incoming-ari           # For incoming calls
disallow=all
allow=ulaw
allow=alaw
outbound_auth=trunk-auth
aors=trunk-aor
from_domain=sip.provider.com   # Your provider's domain

[trunk-auth]
type=auth
auth_type=userpass
username=YOUR_ACTUAL_USERNAME   # From provider
password=YOUR_ACTUAL_PASSWORD   # From provider

[trunk-aor]
type=aor
contact=sip:sip.provider.com    # Provider's SIP server

[trunk-identify]
type=identify
endpoint=trunk
match=PROVIDER_IP_ADDRESS       # Provider's IP
```

### Step 3: Configure Outbound Routing

Edit `/etc/asterisk/extensions.conf`:

```ini
[outbound-calls-ari]
; Outbound calls via trunk
exten => _X.,1,NoOp(Outbound call to ${EXTEN})
    same => n,Set(CALLERID(num)=YOUR_CALLER_ID)
    same => n,Dial(PJSIP/${EXTEN}@trunk,60)
    same => n,Hangup()
```

### Step 4: Test Trunk

```bash
# Reload configs
asterisk -rx "pjsip reload"
asterisk -rx "dialplan reload"

# Check trunk registration
asterisk -rx "pjsip show endpoint trunk"

# Test outbound call via ARI
python /tmp/test_outbound_call.py
```

### Step 5: Production Checklist

- [ ] Secure passwords in all config files
- [ ] Configure firewall for external SIP
- [ ] Set up fail2ban for security
- [ ] Configure SRTP for encrypted audio
- [ ] Set up monitoring and alerting
- [ ] Test emergency numbers
- [ ] Configure call recording (if needed)
- [ ] Set up CDR (Call Detail Records)
- [ ] Configure voicemail (optional)
- [ ] Load test with multiple concurrent calls

---

## Summary

### Configuration Files Reference

| File | Purpose | Port | Key Settings |
|------|---------|------|--------------|
| pjsip.conf | SIP endpoints | 5060 | Extensions, auth, codecs |
| extensions.conf | Call routing | - | Dialplan logic |
| manager.conf | AMI | 5038 | Legacy call control |
| ari.conf | ARI | 8088 | Modern REST API |
| http.conf | HTTP server | 8088 | Enables ARI |
| rtp.conf | Audio | 10000-10100 | RTP port range |

### Testing Phases

1. ✅ **Installation** - Run install.sh
2. ✅ **Verification** - Check Asterisk status and configs
3. ✅ **SIP Client** - Register extension 1000
4. ✅ **AGI Testing** - Test legacy mode
5. ✅ **ARI Testing** - Test modern mode
6. ✅ **Audio Quality** - Echo tests
7. ✅ **Production** - Add external trunk

### Quick Reference Commands

```bash
# Status checks
systemctl status asterisk
asterisk -rx "pjsip show endpoints"
asterisk -rx "core show channels"

# Reload configs
asterisk -rx "pjsip reload"
asterisk -rx "dialplan reload"

# Logs
tail -f /var/log/asterisk/full
tail -f /opt/aiagc/logs/aiagc.log

# ARI
curl -u asterisk:PASSWORD http://localhost:8088/ari/asterisk/info

# Start ARI app
cd /opt/aiagc && source venv/bin/activate
python -m src.asterisk.ari_call_handler
```

---

## Next Steps

1. Complete all internal testing phases
2. Document any issues encountered
3. Review and optimize configuration
4. Plan external trunk integration
5. Set up production monitoring
6. Configure backup and disaster recovery

For additional help, see:
- `MIGRATION_GUIDE.md` - Full ARI migration guide
- `README.md` - Project overview and setup
- `docs/API.md` - API reference

---

**Internal Testing Status:** Ready for deployment  
**External Trunk Status:** Configuration template provided  
**Asterisk Version:** 20.10.2  
**Last Updated:** 2024

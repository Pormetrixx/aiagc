#!/bin/bash
# Complete installation script for AIAGC on Ubuntu 22.04
# This script installs all dependencies, Asterisk, and configures internal testing extensions

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ASTERISK_VERSION="20.10.2"
INSTALL_DIR="/opt/aiagc"
ASTERISK_USER="asterisk"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                    ║${NC}"
echo -e "${BLUE}║       AIAGC - AI Agent Complete Installation Script               ║${NC}"
echo -e "${BLUE}║       Ubuntu 22.04 LTS                                             ║${NC}"
echo -e "${BLUE}║                                                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}" 
   exit 1
fi

# Get the actual user who ran sudo
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo -e "${GREEN}[1/12] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

echo ""
echo -e "${GREEN}[2/12] Installing system dependencies...${NC}"
apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    subversion \
    libncurses5-dev \
    libssl-dev \
    libxml2-dev \
    libsqlite3-dev \
    uuid-dev \
    libjansson-dev \
    libedit-dev \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    sox \
    libsox-dev \
    unixodbc \
    unixodbc-dev \
    libasound2-dev \
    libjack-dev

echo ""
echo -e "${GREEN}[3/12] Installing Docker and Docker Compose...${NC}"
# Install Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    usermod -aG docker $ACTUAL_USER
    echo -e "${YELLOW}Docker installed. You may need to log out and back in for group changes to take effect.${NC}"
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed${NC}"
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi

echo ""
echo -e "${GREEN}[4/12] Creating Asterisk user...${NC}"
if ! id "$ASTERISK_USER" &>/dev/null; then
    useradd -r -s /bin/false $ASTERISK_USER
    echo -e "${GREEN}Asterisk user created${NC}"
else
    echo -e "${YELLOW}Asterisk user already exists${NC}"
fi

echo ""
echo -e "${GREEN}[5/12] Downloading Asterisk ${ASTERISK_VERSION}...${NC}"
cd /usr/src
if [ ! -d "asterisk-${ASTERISK_VERSION}" ]; then
    wget https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-${ASTERISK_VERSION}.tar.gz
    tar -xzf asterisk-${ASTERISK_VERSION}.tar.gz
    echo -e "${GREEN}Asterisk downloaded and extracted${NC}"
else
    echo -e "${YELLOW}Asterisk source already exists${NC}"
fi

echo ""
echo -e "${GREEN}[6/12] Installing Asterisk dependencies...${NC}"
cd asterisk-${ASTERISK_VERSION}
contrib/scripts/install_prereq install

echo ""
echo -e "${GREEN}[7/12] Configuring and compiling Asterisk (this may take 10-15 minutes)...${NC}"
./configure --with-jansson-bundled --with-pjproject-bundled

# Select necessary modules
make menuselect.makeopts
menuselect/menuselect \
    --enable app_dial \
    --enable app_stack \
    --enable app_playback \
    --enable app_voicemail \
    --enable chan_pjsip \
    --enable res_pjsip \
    --enable res_pjsip_session \
    --enable res_agi \
    --enable res_rtp_asterisk \
    --enable codec_ulaw \
    --enable codec_alaw \
    --enable codec_g722 \
    --enable format_wav \
    --enable format_pcm \
    menuselect.makeopts

# Compile Asterisk
make -j$(nproc)
make install
make samples
make config

echo ""
echo -e "${GREEN}[8/12] Setting up Asterisk directories and permissions...${NC}"
mkdir -p /var/lib/asterisk/sounds/custom
mkdir -p /var/spool/asterisk/monitor
mkdir -p /var/log/asterisk
chown -R $ASTERISK_USER:$ASTERISK_USER /var/lib/asterisk
chown -R $ASTERISK_USER:$ASTERISK_USER /var/spool/asterisk
chown -R $ASTERISK_USER:$ASTERISK_USER /var/log/asterisk
chown -R $ASTERISK_USER:$ASTERISK_USER /etc/asterisk

echo ""
echo -e "${GREEN}[9/12] Installing AIAGC Python application...${NC}"
# Clone or copy the application
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p $INSTALL_DIR
    # Copy current directory contents if we're in the repo
    if [ -f "$(pwd)/requirements.txt" ]; then
        cp -r . $INSTALL_DIR/
    fi
fi

cd $INSTALL_DIR

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p recordings
mkdir -p config/asterisk
mkdir -p /tmp/audio_cache

echo ""
echo -e "${GREEN}[10/12] Configuring Asterisk for internal testing...${NC}"

# Create pjsip.conf for internal extensions
cat > /etc/asterisk/pjsip.conf << 'EOF'
; PJSIP Configuration for Internal Testing and External Trunk

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

[transport-tcp]
type=transport
protocol=tcp
bind=0.0.0.0:5060

; Internal Extension 1000 (Test caller)
[1000]
type=endpoint
context=internal
disallow=all
allow=ulaw
allow=alaw
allow=g722
auth=1000
aors=1000

[1000]
type=auth
auth_type=userpass
username=1000
password=test1000

[1000]
type=aor
max_contacts=1
remove_existing=yes

; Internal Extension 1001 (AI Agent answers here)
[1001]
type=endpoint
context=ai-agent
disallow=all
allow=ulaw
allow=alaw
allow=g722
auth=1001
aors=1001

[1001]
type=auth
auth_type=userpass
username=1001
password=test1001

[1001]
type=aor
max_contacts=1
remove_existing=yes

; External SIP Trunk (for production use)
[trunk]
type=endpoint
context=outbound-calls
disallow=all
allow=ulaw
allow=alaw
allow=g722
outbound_auth=trunk-auth
aors=trunk-aor
from_domain=YOUR_DOMAIN

[trunk-auth]
type=auth
auth_type=userpass
username=YOUR_SIP_USERNAME
password=YOUR_SIP_PASSWORD

[trunk-aor]
type=aor
contact=sip:YOUR_SIP_PROVIDER

[trunk-identify]
type=identify
endpoint=trunk
match=YOUR_SIP_PROVIDER_IP
EOF

# Create extensions.conf with internal testing support
cat > /etc/asterisk/extensions.conf << EOF
; Asterisk Extensions Configuration with Internal Testing

[globals]
AIAGC_PATH=$INSTALL_DIR

[general]
static=yes
writeprotect=no
clearglobalvars=no

[internal]
; Context for internal test extensions
; Call from extension 1000 to 1001 to test the AI agent

; Dial extension 1001 to reach AI agent
exten => 1001,1,NoOp(Calling AI Agent from internal extension)
    same => n,Set(CHANNEL(language)=de)
    same => n,Dial(PJSIP/1001,30)
    same => n,Hangup()

; Dial extension 1000 (echo back)
exten => 1000,1,NoOp(Call to extension 1000)
    same => n,Answer()
    same => n,Playback(hello-world)
    same => n,Hangup()

; Test echo service
exten => 600,1,NoOp(Echo Test)
    same => n,Answer()
    same => n,Playback(demo-echotest)
    same => n,Echo()
    same => n,Hangup()

[ai-agent]
; Context where AI agent answers (extension 1001)
; Legacy AGI mode (deprecated but still functional)
exten => s,1,NoOp(AI Agent Context - Call Received - AGI Mode)
    same => n,Set(CHANNEL(language)=de)
    same => n,Answer()
    same => n,Wait(1)
    same => n,AGI(python3,$INSTALL_DIR/src/asterisk/call_handler.py)
    same => n,Hangup()

[ai-agent-ari]
; Context where AI agent answers using ARI (recommended)
exten => s,1,NoOp(AI Agent Context - Call Received - ARI Mode)
    same => n,Set(CHANNEL(language)=de)
    same => n,Stasis(aiagc)
    same => n,Hangup()

[outbound-calls]
; Main outbound calling context for production AI agent calls
; Legacy AGI mode (deprecated but still functional)

; Extension 's' - Start extension for outbound calls
exten => s,1,NoOp(AI Agent Outbound Call Starting - AGI Mode)
    same => n,Set(CHANNEL(language)=de)
    same => n,Answer()
    same => n,Wait(1)
    same => n,AGI(python3,$INSTALL_DIR/src/asterisk/call_handler.py)
    same => n,Hangup()

; Extension for manual testing
exten => 100,1,NoOp(Test Call - AGI Mode)
    same => n,Answer()
    same => n,AGI(python3,$INSTALL_DIR/src/asterisk/call_handler.py)
    same => n,Hangup()

; Transfer to human agent
exten => 200,1,NoOp(Transfer to Human Agent)
    same => n,Dial(SIP/agent@trunk,60)
    same => n,Voicemail(200@default,u)
    same => n,Hangup()

[outbound-calls-ari]
; Main outbound calling context using ARI (recommended)

; Extension 's' - Start extension for outbound calls
exten => s,1,NoOp(AI Agent Outbound Call Starting - ARI Mode)
    same => n,Set(CHANNEL(language)=de)
    same => n,Stasis(aiagc)
    same => n,Hangup()

; Extension for manual testing
exten => 100,1,NoOp(Test Call - ARI Mode)
    same => n,Stasis(aiagc)
    same => n,Hangup()

[incoming]
; Handle incoming external calls
; Default to legacy AGI for backward compatibility
exten => _X.,1,NoOp(Incoming Call from \${CALLERID(num)})
    same => n,Answer()
    same => n,Wait(1)
    same => n,AGI(python3,$INSTALL_DIR/src/asterisk/call_handler.py)
    same => n,Hangup()

[incoming-ari]
; Handle incoming external calls with ARI (recommended)
exten => _X.,1,NoOp(Incoming Call from \${CALLERID(num)} - ARI Mode)
    same => n,Stasis(aiagc)
    same => n,Hangup()
EOF

# Create manager.conf for AMI access
cat > /etc/asterisk/manager.conf << 'EOF'
; Asterisk Manager Interface Configuration

[general]
enabled = yes
port = 5038
bindaddr = 0.0.0.0
displayconnects = yes

[admin]
secret = aiagc_admin_password_change_me
deny = 0.0.0.0/0.0.0.0
permit = 127.0.0.1/255.255.255.0
permit = 172.16.0.0/255.255.0.0
read = system,call,log,verbose,command,agent,user,config,dtmf,reporting,cdr,dialplan,originate
write = system,call,log,verbose,command,agent,user,config,dtmf,reporting,cdr,dialplan,originate
EOF

# Create ari.conf for ARI access (modern REST interface)
cat > /etc/asterisk/ari.conf << 'EOF'
; Asterisk REST Interface Configuration

[general]
enabled = yes
pretty = yes
allowed_origins = *

[asterisk]
type = user
read_only = no
password = aiagc_ari_password_change_me
password_format = plain
EOF

# Create http.conf for ARI HTTP server
cat > /etc/asterisk/http.conf << 'EOF'
; HTTP Server Configuration (required for ARI)

[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
enablestatic = yes
redirect = /
prefix = asterisk
EOF

# Create rtp.conf for audio
cat > /etc/asterisk/rtp.conf << 'EOF'
[general]
rtpstart=10000
rtpend=10100
EOF

# Set proper permissions
chown -R $ASTERISK_USER:$ASTERISK_USER /etc/asterisk

echo ""
echo -e "${GREEN}[11/12] Creating systemd service for Asterisk...${NC}"
cat > /etc/systemd/system/asterisk.service << 'EOF'
[Unit]
Description=Asterisk PBX
After=network.target

[Service]
Type=simple
User=asterisk
Group=asterisk
ExecStart=/usr/sbin/asterisk -f -C /etc/asterisk/asterisk.conf
ExecReload=/usr/sbin/asterisk -rx 'core reload'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable asterisk
systemctl start asterisk

echo ""
echo -e "${GREEN}[12/12] Creating environment configuration...${NC}"
cd $INSTALL_DIR

if [ ! -f ".env" ]; then
    cp .env.example .env
    # Update with system-specific defaults
    sed -i "s|ASTERISK_HOST=localhost|ASTERISK_HOST=127.0.0.1|g" .env
    sed -i "s|ASTERISK_SECRET=your_asterisk_secret|ASTERISK_SECRET=aiagc_admin_password_change_me|g" .env
    echo -e "${GREEN}.env file created${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Create a test script
cat > $INSTALL_DIR/test_internal_call.sh << 'EOF'
#!/bin/bash
# Test script for internal extension calling

echo "Testing internal extension setup..."
echo ""
echo "To test the AI agent:"
echo "1. Register a SIP client (like Zoiper, Linphone, or softphone) with:"
echo "   - Server: $(hostname -I | awk '{print $1}')"
echo "   - Extension: 1000"
echo "   - Password: test1000"
echo "   - Port: 5060"
echo ""
echo "2. Call extension 1001 from your SIP client"
echo "3. The AI agent should answer and start conversation"
echo ""
echo "Asterisk status:"
asterisk -rx "core show version"
echo ""
echo "Registered endpoints:"
asterisk -rx "pjsip show endpoints"
echo ""
echo "To view Asterisk console: asterisk -rvvv"
echo "To restart Asterisk: systemctl restart asterisk"
echo "To view logs: tail -f /var/log/asterisk/full"
EOF

chmod +x $INSTALL_DIR/test_internal_call.sh
chown -R $ACTUAL_USER:$ACTUAL_USER $INSTALL_DIR

# Create a README for testing
cat > $INSTALL_DIR/TESTING_GUIDE.md << 'EOF'
# Internal Testing Guide

## Quick Start Testing

### 1. Configure Your SIP Client

Install a SIP client (softphone) on your computer or mobile:
- **Windows/Mac/Linux**: Zoiper, MicroSIP, or Linphone
- **Android**: Linphone, Zoiper
- **iOS**: Linphone, Zoiper

Configure the SIP client with:
```
Server/Domain: <YOUR_SERVER_IP>
Username: 1000
Password: test1000
Port: 5060
Transport: UDP
```

### 2. Test the AI Agent

1. Open your SIP client and ensure it shows "Registered"
2. Dial extension: **1001**
3. The AI agent will answer and begin conversation in German
4. Test the conversation flow:
   - Listen to the opening
   - Respond to questions
   - Test objection handling
   - End the call naturally

### 3. Monitor the Call

Open a terminal and run:
```bash
# View Asterisk console
asterisk -rvvv

# View application logs
tail -f /opt/aiagc/logs/aiagc.log

# View Asterisk logs
tail -f /var/log/asterisk/full
```

### 4. Test Extensions

- **1001**: AI Agent (test here)
- **600**: Echo test (test audio quality)
- **1000**: Hello world playback

## Troubleshooting

### SIP Client Won't Register
```bash
# Check Asterisk is running
systemctl status asterisk

# Check PJSIP endpoints
asterisk -rx "pjsip show endpoints"

# Check for errors
asterisk -rx "pjsip show endpoint 1000"
```

### No Audio in Call
```bash
# Check RTP ports
asterisk -rx "rtp show settings"

# Ensure firewall allows RTP
ufw allow 10000:10100/udp
```

### AI Agent Not Responding
```bash
# Check Python environment
source /opt/aiagc/venv/bin/activate
python -c "import src.config; print('OK')"

# Check API keys in .env
nano /opt/aiagc/.env

# Check logs
tail -f /opt/aiagc/logs/aiagc.log
```

### View Call Details
```bash
# Show active calls
asterisk -rx "core show channels"

# Show call history
asterisk -rx "cdr show all"
```

## Next Steps

Once internal testing is successful:

1. **Configure External SIP Trunk**: Edit `/etc/asterisk/pjsip.conf` with your provider details
2. **Update API Keys**: Edit `/opt/aiagc/.env` with Deepgram and OpenAI keys
3. **Test Production Calls**: Use `examples/make_calls.py` for outbound calling
4. **Monitor Performance**: Check logs and call records
5. **Scale Up**: Adjust concurrent call limits in configuration

## Support

- View logs: `/opt/aiagc/logs/aiagc.log`
- Asterisk console: `asterisk -rvvv`
- Documentation: `/opt/aiagc/README.md`
EOF

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                    ║${NC}"
echo -e "${BLUE}║                    Installation Complete!                         ║${NC}"
echo -e "${BLUE}║                                                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ System packages installed${NC}"
echo -e "${GREEN}✓ Docker and Docker Compose installed${NC}"
echo -e "${GREEN}✓ Asterisk ${ASTERISK_VERSION} compiled and installed${NC}"
echo -e "${GREEN}✓ Internal test extensions configured (1000, 1001)${NC}"
echo -e "${GREEN}✓ AIAGC application installed at: $INSTALL_DIR${NC}"
echo -e "${GREEN}✓ Systemd service created and started${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}IMPORTANT: Next Steps${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}1. Configure API Keys:${NC}"
echo -e "   nano $INSTALL_DIR/.env"
echo -e "   ${YELLOW}(Add your DEEPGRAM_API_KEY and OPENAI_API_KEY)${NC}"
echo ""
echo -e "${BLUE}2. Test Internal Calling:${NC}"
echo -e "   - Install a SIP client (Zoiper, Linphone, etc.)"
echo -e "   - Configure with:"
echo -e "     Server: $(hostname -I | awk '{print $1}')"
echo -e "     Extension: 1000"
echo -e "     Password: test1000"
echo -e "   - Call extension 1001 to hear the AI agent"
echo ""
echo -e "${BLUE}3. View Testing Guide:${NC}"
echo -e "   cat $INSTALL_DIR/TESTING_GUIDE.md"
echo ""
echo -e "${BLUE}4. Monitor System:${NC}"
echo -e "   Asterisk console: ${GREEN}asterisk -rvvv${NC}"
echo -e "   Application logs: ${GREEN}tail -f $INSTALL_DIR/logs/aiagc.log${NC}"
echo -e "   Asterisk status:  ${GREEN}systemctl status asterisk${NC}"
echo ""
echo -e "${BLUE}5. Test Script:${NC}"
echo -e "   $INSTALL_DIR/test_internal_call.sh"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Server IP: ${GREEN}$(hostname -I | awk '{print $1}')${NC}"
echo -e "${BLUE}SIP Port: ${GREEN}5060${NC}"
echo -e "${BLUE}Test Extension: ${GREEN}1000 (password: test1000)${NC}"
echo -e "${BLUE}AI Agent Extension: ${GREEN}1001${NC}"
echo ""
echo -e "${YELLOW}If you logged in via sudo, you may need to log out and back in${NC}"
echo -e "${YELLOW}for Docker group permissions to take effect.${NC}"
echo ""
echo -e "${GREEN}Happy testing! 🎉${NC}"
echo ""

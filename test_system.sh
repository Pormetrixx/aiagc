#!/bin/bash
# Quick test script to verify Asterisk and extensions are working

echo "═══════════════════════════════════════════════════"
echo "  AIAGC - System Test Script"
echo "═══════════════════════════════════════════════════"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -eq 0 ]; then 
    echo "✓ Running with root privileges"
else
    echo "⚠ Note: Some commands may require sudo"
fi

echo ""
echo "1. Checking Asterisk Service..."
if systemctl is-active --quiet asterisk; then
    echo "   ✓ Asterisk is running"
    asterisk -rx "core show version" 2>/dev/null | head -1
else
    echo "   ✗ Asterisk is not running"
    echo "   Try: sudo systemctl start asterisk"
fi

echo ""
echo "2. Checking SIP Endpoints..."
asterisk -rx "pjsip show endpoints" 2>/dev/null | grep -E "1000|1001|Endpoint|=====" || echo "   ⚠ Unable to query endpoints"

echo ""
echo "3. Checking Registration Status..."
asterisk -rx "pjsip show registrations" 2>/dev/null || echo "   ⚠ Unable to query registrations"

echo ""
echo "4. Checking Network Configuration..."
IP=$(hostname -I | awk '{print $1}')
echo "   Server IP: $IP"
echo "   SIP Port: 5060"
echo "   RTP Ports: 10000-10100"

echo ""
echo "5. Checking Firewall Status..."
if command -v ufw &> /dev/null; then
    ufw status | grep -E "Status|5060|10000:10100" || echo "   UFW not active"
else
    echo "   UFW not installed"
fi

echo ""
echo "6. Checking Python Environment..."
if [ -f "/opt/aiagc/venv/bin/python" ]; then
    echo "   ✓ Python virtual environment exists"
    /opt/aiagc/venv/bin/python --version
else
    echo "   ⚠ Python virtual environment not found at /opt/aiagc/venv"
fi

echo ""
echo "7. Checking Configuration Files..."
if [ -f "/opt/aiagc/.env" ]; then
    echo "   ✓ .env configuration file exists"
    if grep -q "your_deepgram_api_key\|your_openai_api_key" /opt/aiagc/.env 2>/dev/null; then
        echo "   ⚠ API keys not configured yet"
        echo "   Edit: nano /opt/aiagc/.env"
    else
        echo "   ✓ API keys appear to be configured"
    fi
else
    echo "   ⚠ .env file not found"
fi

echo ""
echo "8. Checking Log Files..."
if [ -f "/var/log/asterisk/full" ]; then
    echo "   ✓ Asterisk logs available"
    echo "   View with: tail -f /var/log/asterisk/full"
else
    echo "   ⚠ Asterisk log file not found"
fi

if [ -d "/opt/aiagc/logs" ]; then
    echo "   ✓ AIAGC logs directory exists"
    echo "   View with: tail -f /opt/aiagc/logs/aiagc.log"
else
    echo "   ⚠ AIAGC logs directory not found"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Test Your Setup"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Configure a SIP client with:"
echo "  • Server: $IP"
echo "  • Username: 1000"
echo "  • Password: test1000"
echo "  • Port: 5060"
echo ""
echo "Then dial extension 1001 to test the AI agent"
echo ""
echo "Useful Commands:"
echo "  • Asterisk console:    asterisk -rvvv"
echo "  • Restart Asterisk:    sudo systemctl restart asterisk"
echo "  • View full guide:     cat /opt/aiagc/TESTING_GUIDE.md"
echo ""

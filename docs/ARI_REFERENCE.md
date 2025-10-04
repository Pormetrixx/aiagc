# Complete ARI Reference - Asterisk 20.15.2

This document provides comprehensive documentation for all ARI (Asterisk REST Interface) features implemented in AIAGC with Asterisk 20.15.2.

## Table of Contents

1. [Overview](#overview)
2. [Connection Management](#connection-management)
3. [Channel Operations](#channel-operations)
4. [Media Operations](#media-operations)
5. [Bridge Operations](#bridge-operations)
6. [Advanced Features](#advanced-features)
7. [System Information](#system-information)
8. [Event Handling](#event-handling)
9. [Complete API Reference](#complete-api-reference)
10. [Examples](#examples)

## Overview

ARI (Asterisk REST Interface) is a modern REST and WebSocket-based interface for controlling Asterisk. It provides:

- **RESTful API**: HTTP-based control of Asterisk resources
- **WebSocket Events**: Real-time event streaming
- **Full Call Control**: Complete control over channels, bridges, and media
- **Modern Architecture**: Event-driven, scalable design

### Key Benefits with Asterisk 20.15.2

- Latest security patches and stability improvements
- Enhanced performance for high-volume scenarios
- Better memory management
- Improved WebSocket reliability
- Full PJSIP integration

## Connection Management

### Connect to ARI

```python
from src.asterisk.ari_interface import AsteriskARI

ari = AsteriskARI(
    host="localhost",
    port=8088,
    username="asterisk",
    password="your_password",
    app_name="aiagc"
)

ari.connect()
```

### Disconnect

```python
ari.disconnect()
```

### Get Asterisk Info

```python
info = ari.get_asterisk_info()
print(f"Asterisk Version: {info['version']}")
print(f"System: {info['system_info']}")
```

## Channel Operations

### Basic Channel Control

#### Answer Channel

```python
# Answer an incoming call
ari.answer_channel(channel_id)
```

#### Hangup Channel

```python
# Terminate a call
ari.hangup_channel(channel_id)
```

#### Originate Call

```python
# Create an outbound call
channel_id = ari.originate_call(
    endpoint="PJSIP/1234567890",
    context="outbound-calls",
    extension="s",
    caller_id="Company <+15551234567>",
    variables={
        "CAMPAIGN_TYPE": "sales",
        "CUSTOMER_ID": "12345"
    }
)
```

### Channel State Control

#### Ring Indication

```python
# Start ringing indication
ari.ring_channel(channel_id)

# Stop ringing indication
ari.stop_ringing_channel(channel_id)
```

#### Hold/Unhold

```python
# Put channel on hold
ari.hold_channel(channel_id)

# Remove from hold
ari.unhold_channel(channel_id)
```

#### Mute/Unmute

```python
# Mute channel (both directions)
ari.mute_channel("both", channel_id)

# Mute only incoming audio
ari.mute_channel("in", channel_id)

# Mute only outgoing audio
ari.mute_channel("out", channel_id)

# Unmute
ari.unmute_channel("both", channel_id)
```

### DTMF Operations

```python
# Send DTMF tones
ari.send_dtmf("12345", channel_id, duration=100)

# Send special characters
ari.send_dtmf("#*", channel_id)
```

### Channel Variables

```python
# Set channel variable
ari.set_channel_variable("CUSTOM_VAR", "value", channel_id)

# Get channel variable
value = ari.get_channel_variable("CUSTOM_VAR", channel_id)
```

### Channel Information

```python
# Get comprehensive channel info
info = ari.get_channel_info(channel_id)
print(f"State: {info['state']}")
print(f"Caller: {info['caller']['number']}")
print(f"Connected: {info['connected']['number']}")
print(f"Language: {info['language']}")
```

## Media Operations

### Playback

#### Play Sound File

```python
# Play a sound file
playback_id = ari.play_media("sound:hello-world", channel_id, language="en")
```

#### Play Recording

```python
# Play a stored recording
playback_id = ari.play_recording("my_recording", channel_id)
```

### Recording

#### Record Channel

```python
# Start recording
recording_name = ari.record_channel(
    name="customer_call_20240101",
    format="wav",
    max_duration_seconds=300,  # 5 minutes max
    max_silence_seconds=5,      # Stop after 5 seconds of silence
    channel_id=channel_id
)
```

#### Manage Recordings

```python
# Get recording information
info = ari.get_recording("customer_call_20240101")
print(f"Format: {info['format']}")
print(f"State: {info['state']}")

# Delete recording
ari.delete_recording("customer_call_20240101")
```

## Bridge Operations

Bridges enable multi-party calls and conference scenarios.

### Create Bridge

```python
# Create a mixing bridge for conferences
bridge_id = ari.create_bridge("mixing")

# Create a holding bridge
bridge_id = ari.create_bridge("holding")
```

### Manage Bridge Channels

```python
# Add channel to bridge
ari.add_channel_to_bridge(channel_id, bridge_id)

# Remove channel from bridge
ari.remove_channel_from_bridge(channel_id, bridge_id)

# Destroy bridge
ari.destroy_bridge(bridge_id)
```

### Example: Conference Call

```python
# Create conference bridge
bridge_id = ari.create_bridge("mixing")

# Add multiple channels
for channel_id in channel_ids:
    ari.add_channel_to_bridge(channel_id, bridge_id)

# All channels can now communicate
```

## Advanced Features

### Silence Detection

```python
# Start silence detection
ari.start_silence_detection(channel_id)

# Stop silence detection
ari.stop_silence_detection(channel_id)
```

### Channel Monitoring (Snoop)

```python
# Create snoop channel for monitoring
snoop_id = ari.snoop_channel(
    channel_id=target_channel_id,
    spy="both",      # Monitor both directions
    whisper="none",  # No whispering
    app="aiagc",
    app_args="monitoring"
)

# Create snoop for supervisor whispering
snoop_id = ari.snoop_channel(
    channel_id=agent_channel_id,
    spy="none",
    whisper="in"     # Whisper to agent only
)
```

### Channel Redirection

```python
# Redirect channel to new endpoint
ari.redirect_channel("PJSIP/new_endpoint", channel_id)
```

### Event Subscriptions

```python
# Subscribe to channel events
ari.subscribe_to_events(f"channel:{channel_id}")

# Subscribe to bridge events
ari.subscribe_to_events(f"bridge:{bridge_id}")

# Unsubscribe
ari.unsubscribe_from_events(f"channel:{channel_id}")
```

## System Information

### List Active Resources

```python
# List all active channels
channels = ari.list_channels()
for channel in channels:
    print(f"Channel: {channel['id']} - State: {channel['state']}")

# List all active bridges
bridges = ari.list_bridges()
for bridge in bridges:
    print(f"Bridge: {bridge['id']} - Type: {bridge['type']}")
```

## Event Handling

### Event-Driven Application

```python
def on_stasis_start(channel_obj, event):
    """Handle new channel entering application"""
    print(f"New channel: {channel_obj.id}")
    channel_obj.answer()
    channel_obj.play(media="sound:welcome")

def on_stasis_end(channel_obj, event):
    """Handle channel leaving application"""
    print(f"Channel ended: {channel_obj.id}")

# Start event loop
ari.start_event_loop(
    on_stasis_start=on_stasis_start,
    on_stasis_end=on_stasis_end
)
```

## Complete API Reference

### AsteriskARI Class

#### Constructor

```python
AsteriskARI(
    host: str = None,
    port: int = None,
    username: str = None,
    password: str = None,
    app_name: str = "aiagc"
)
```

#### Connection Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `connect()` | - | None | Connect to ARI |
| `disconnect()` | - | None | Disconnect from ARI |

#### Channel Control Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `answer_channel(channel_id)` | channel_id: str | bool | Answer a channel |
| `hangup_channel(channel_id)` | channel_id: str | bool | Hang up a channel |
| `ring_channel(channel_id)` | channel_id: str | bool | Start ringing indication |
| `stop_ringing_channel(channel_id)` | channel_id: str | bool | Stop ringing indication |
| `hold_channel(channel_id)` | channel_id: str | bool | Put channel on hold |
| `unhold_channel(channel_id)` | channel_id: str | bool | Remove from hold |
| `mute_channel(direction, channel_id)` | direction: str, channel_id: str | bool | Mute channel |
| `unmute_channel(direction, channel_id)` | direction: str, channel_id: str | bool | Unmute channel |
| `send_dtmf(dtmf, channel_id, duration)` | dtmf: str, channel_id: str, duration: int | bool | Send DTMF tones |

#### Channel Information Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get_channel_info(channel_id)` | channel_id: str | dict | Get channel information |
| `set_channel_variable(var, val, ch_id)` | variable: str, value: str, channel_id: str | bool | Set channel variable |
| `get_channel_variable(var, ch_id)` | variable: str, channel_id: str | str | Get channel variable |
| `list_channels()` | - | list | List all channels |

#### Media Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `play_media(media, ch_id, lang)` | media: str, channel_id: str, language: str | str | Play media file |
| `play_recording(name, ch_id)` | recording_name: str, channel_id: str | str | Play recording |
| `record_channel(name, fmt, ...)` | name: str, format: str, ... | str | Start recording |
| `get_recording(name)` | recording_name: str | dict | Get recording info |
| `delete_recording(name)` | recording_name: str | bool | Delete recording |

#### Bridge Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `create_bridge(type)` | bridge_type: str | str | Create a bridge |
| `destroy_bridge(bridge_id)` | bridge_id: str | bool | Destroy bridge |
| `add_channel_to_bridge(ch, br)` | channel_id: str, bridge_id: str | bool | Add channel to bridge |
| `remove_channel_from_bridge(ch, br)` | channel_id: str, bridge_id: str | bool | Remove from bridge |
| `list_bridges()` | - | list | List all bridges |

#### Call Origination

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `originate_call(endpoint, ...)` | endpoint: str, context: str, ... | str | Originate call |

#### Advanced Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `snoop_channel(ch_id, spy, whisper, ...)` | channel_id: str, spy: str, whisper: str, ... | str | Create snoop channel |
| `redirect_channel(endpoint, ch_id)` | endpoint: str, channel_id: str | bool | Redirect channel |
| `start_silence_detection(ch_id)` | channel_id: str | bool | Start silence detection |
| `stop_silence_detection(ch_id)` | channel_id: str | bool | Stop silence detection |
| `subscribe_to_events(source)` | event_source: str | bool | Subscribe to events |
| `unsubscribe_from_events(source)` | event_source: str | bool | Unsubscribe from events |

#### System Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get_asterisk_info()` | - | dict | Get Asterisk info |
| `start_event_loop(start_cb, end_cb)` | on_stasis_start: Callable, on_stasis_end: Callable | None | Start event loop |

## Examples

### Example 1: Simple Outbound Call

```python
from src.asterisk.ari_interface import AsteriskARI

ari = AsteriskARI()
ari.connect()

# Originate call
channel_id = ari.originate_call(
    endpoint="PJSIP/customer@trunk",
    context="outbound-calls",
    extension="s"
)

if channel_id:
    print(f"Call started: {channel_id}")
else:
    print("Call failed")

ari.disconnect()
```

### Example 2: Conference Call

```python
from src.asterisk.ari_interface import AsteriskARI
import time

ari = AsteriskARI()
ari.connect()

# Create conference bridge
bridge_id = ari.create_bridge("mixing")

# Originate calls to participants
participants = ["PJSIP/user1", "PJSIP/user2", "PJSIP/user3"]
channel_ids = []

for endpoint in participants:
    ch_id = ari.originate_call(endpoint=endpoint, context="conference")
    if ch_id:
        ari.answer_channel(ch_id)
        ari.add_channel_to_bridge(ch_id, bridge_id)
        channel_ids.append(ch_id)

print(f"Conference started with {len(channel_ids)} participants")

# Let conference run for 5 minutes
time.sleep(300)

# End conference
for ch_id in channel_ids:
    ari.remove_channel_from_bridge(ch_id, bridge_id)
    ari.hangup_channel(ch_id)

ari.destroy_bridge(bridge_id)
ari.disconnect()
```

### Example 3: Call Recording

```python
from src.asterisk.ari_interface import AsteriskARI
import time

ari = AsteriskARI()
ari.connect()

# Originate call
channel_id = ari.originate_call(
    endpoint="PJSIP/customer@trunk",
    context="outbound-calls",
    extension="s"
)

if channel_id:
    ari.answer_channel(channel_id)
    
    # Play greeting
    ari.play_media("sound:custom/greeting", channel_id)
    time.sleep(3)
    
    # Start recording
    recording_name = ari.record_channel(
        name=f"call_{channel_id}",
        format="wav",
        max_duration_seconds=600,
        channel_id=channel_id
    )
    
    print(f"Recording: {recording_name}")
    
    # Let call proceed
    time.sleep(60)
    
    # End call
    ari.hangup_channel(channel_id)
    
    # Get recording info
    info = ari.get_recording(recording_name)
    print(f"Recording saved: {info}")

ari.disconnect()
```

### Example 4: Supervisor Monitoring

```python
from src.asterisk.ari_interface import AsteriskARI

ari = AsteriskARI()
ari.connect()

# Agent is on a call
agent_channel_id = "existing-agent-channel"

# Create snoop channel for supervisor
snoop_id = ari.snoop_channel(
    channel_id=agent_channel_id,
    spy="both",      # Supervisor can hear both sides
    whisper="in"     # Supervisor can speak to agent only
)

print(f"Supervisor monitoring channel: {snoop_id}")

# Supervisor's channel can now be connected to a phone
supervisor_channel = ari.originate_call(
    endpoint="PJSIP/supervisor@phones",
    context="monitoring"
)

ari.disconnect()
```

### Example 5: Event-Driven Application

```python
from src.asterisk.ari_interface import AsteriskARI
from loguru import logger

def handle_new_call(channel_obj, event):
    """Handle incoming calls"""
    logger.info(f"New call from: {channel_obj.json.get('caller', {}).get('number')}")
    
    # Answer the call
    channel_obj.answer()
    
    # Play welcome message
    channel_obj.play(media="sound:custom/welcome")
    
    # Start recording
    channel_obj.record(
        name=f"call_{channel_obj.id}",
        format="wav",
        maxDurationSeconds=600
    )

def handle_call_end(channel_obj, event):
    """Handle call completion"""
    logger.info(f"Call ended: {channel_obj.id}")
    # Perform cleanup, save records, etc.

# Start ARI application
ari = AsteriskARI()
ari.connect()

logger.info("Starting ARI application...")
ari.start_event_loop(
    on_stasis_start=handle_new_call,
    on_stasis_end=handle_call_end
)
```

## Best Practices

### 1. Connection Management

- Always use try/finally to ensure disconnection
- Handle connection failures gracefully
- Implement reconnection logic for long-running applications

### 2. Error Handling

```python
try:
    ari.connect()
    # Your code here
except Exception as e:
    logger.error(f"Error: {e}")
finally:
    ari.disconnect()
```

### 3. Resource Cleanup

- Always hang up channels when done
- Destroy bridges after use
- Delete recordings when no longer needed

### 4. Event-Driven Design

- Use event handlers for long-running applications
- Subscribe only to needed events
- Unsubscribe when done

### 5. Performance

- Reuse ARI connections
- Use bridges for multi-party scenarios
- Implement proper timeout handling

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify Asterisk is running
   - Check ARI is enabled in `ari.conf`
   - Verify HTTP server in `http.conf`

2. **Authentication Failed**
   - Check username/password in `ari.conf`
   - Verify credentials match your code

3. **Channel Not Found**
   - Channel may have already hung up
   - Always check return values

4. **Events Not Received**
   - Verify Stasis dialplan configuration
   - Check application name matches

### Debugging

```python
# Enable debug logging
from loguru import logger
logger.enable("src.asterisk")

# Check Asterisk logs
# tail -f /var/log/asterisk/full

# Test ARI endpoint
# curl -u asterisk:password http://localhost:8088/ari/asterisk/info
```

## Version Compatibility

This implementation is tested and compatible with:

- **Asterisk**: 20.15.2 (recommended), 13.0.0+
- **Python**: 3.11+ (3.12 recommended)
- **ARI Library**: 0.1.3

## Additional Resources

- [Asterisk ARI Wiki](https://wiki.asterisk.org/wiki/display/AST/Asterisk+REST+Interface)
- [ARI Python Library](https://github.com/asterisk/ari-py)
- [Asterisk 20 Documentation](https://docs.asterisk.org/Asterisk_20_Documentation/)
- [Project README](../README.md)
- [Migration Guide](../MIGRATION_GUIDE.md)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Asterisk logs
3. Consult the examples
4. See the test suite for usage patterns

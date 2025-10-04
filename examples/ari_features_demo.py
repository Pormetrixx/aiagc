#!/usr/bin/env python3
"""
Comprehensive ARI Features Demonstration
Shows all available ARI functionality with Asterisk 20.15.2
"""

import asyncio
import time
from loguru import logger

from src.asterisk.ari_interface import AsteriskARI
from src.config import settings
from src.utils.logging_config import setup_logging


def demo_basic_operations():
    """Demonstrate basic ARI operations"""
    logger.info("=== Basic ARI Operations Demo ===")
    
    ari = AsteriskARI()
    
    try:
        # Connect to ARI
        ari.connect()
        logger.info("✓ Connected to ARI")
        
        # Get Asterisk info
        info = ari.get_asterisk_info()
        logger.info(f"✓ Asterisk Version: {info.get('version', 'Unknown')}")
        
        # List active channels
        channels = ari.list_channels()
        logger.info(f"✓ Active channels: {len(channels)}")
        
        # List active bridges
        bridges = ari.list_bridges()
        logger.info(f"✓ Active bridges: {len(bridges)}")
        
    except Exception as e:
        logger.error(f"Error in basic operations: {e}")
    finally:
        ari.disconnect()
        logger.info("✓ Disconnected from ARI")


def demo_call_origination():
    """Demonstrate call origination"""
    logger.info("=== Call Origination Demo ===")
    
    ari = AsteriskARI()
    
    try:
        ari.connect()
        
        # Originate a call
        channel_id = ari.originate_call(
            endpoint="PJSIP/1000",
            context="outbound-calls-ari",
            extension="s",
            caller_id="Test System <1234567890>",
            variables={
                "CAMPAIGN_TYPE": "demo",
                "CALL_SOURCE": "ari_demo"
            }
        )
        
        if channel_id:
            logger.info(f"✓ Call originated: {channel_id}")
            
            # Get channel info
            info = ari.get_channel_info(channel_id)
            logger.info(f"✓ Channel state: {info.get('state')}")
            
        else:
            logger.warning("Call origination failed")
            
    except Exception as e:
        logger.error(f"Error in call origination: {e}")
    finally:
        ari.disconnect()


def demo_channel_control():
    """Demonstrate channel control operations"""
    logger.info("=== Channel Control Demo ===")
    
    ari = AsteriskARI()
    
    try:
        ari.connect()
        
        # Originate a test call
        channel_id = ari.originate_call(
            endpoint="PJSIP/1000",
            context="test",
            extension="echo"
        )
        
        if not channel_id:
            logger.warning("Cannot demo channel control without active channel")
            return
        
        logger.info(f"✓ Working with channel: {channel_id}")
        
        # Answer the channel
        if ari.answer_channel(channel_id):
            logger.info("✓ Channel answered")
        
        time.sleep(1)
        
        # Ring indication
        if ari.ring_channel(channel_id):
            logger.info("✓ Ringing channel")
        
        time.sleep(2)
        
        if ari.stop_ringing_channel(channel_id):
            logger.info("✓ Stopped ringing")
        
        # Mute operations
        if ari.mute_channel("both", channel_id):
            logger.info("✓ Channel muted (both directions)")
        
        time.sleep(1)
        
        if ari.unmute_channel("both", channel_id):
            logger.info("✓ Channel unmuted")
        
        # Hold operations
        if ari.hold_channel(channel_id):
            logger.info("✓ Channel on hold")
        
        time.sleep(1)
        
        if ari.unhold_channel(channel_id):
            logger.info("✓ Channel off hold")
        
        # DTMF
        if ari.send_dtmf("12345", channel_id):
            logger.info("✓ Sent DTMF tones: 12345")
        
        # Channel variables
        if ari.set_channel_variable("TEST_VAR", "test_value", channel_id):
            logger.info("✓ Set channel variable")
        
        value = ari.get_channel_variable("TEST_VAR", channel_id)
        logger.info(f"✓ Got channel variable: {value}")
        
        # Hangup
        time.sleep(1)
        if ari.hangup_channel(channel_id):
            logger.info("✓ Channel hung up")
        
    except Exception as e:
        logger.error(f"Error in channel control: {e}")
    finally:
        ari.disconnect()


def demo_media_operations():
    """Demonstrate media playback and recording"""
    logger.info("=== Media Operations Demo ===")
    
    ari = AsteriskARI()
    
    try:
        ari.connect()
        
        # Originate a test call
        channel_id = ari.originate_call(
            endpoint="PJSIP/1000",
            context="test",
            extension="echo"
        )
        
        if not channel_id:
            logger.warning("Cannot demo media operations without active channel")
            return
        
        logger.info(f"✓ Working with channel: {channel_id}")
        
        # Answer the channel
        ari.answer_channel(channel_id)
        time.sleep(1)
        
        # Play a sound file
        playback_id = ari.play_media("sound:hello-world", channel_id)
        if playback_id:
            logger.info(f"✓ Playing sound: {playback_id}")
        
        time.sleep(3)
        
        # Start recording
        recording_name = ari.record_channel(
            name=f"demo_recording_{int(time.time())}",
            format="wav",
            max_duration_seconds=10,
            max_silence_seconds=3,
            channel_id=channel_id
        )
        
        if recording_name:
            logger.info(f"✓ Recording started: {recording_name}")
        
        time.sleep(5)
        
        # Get recording info
        recording_info = ari.get_recording(recording_name)
        if recording_info:
            logger.info(f"✓ Recording info: {recording_info}")
        
        # Hangup
        time.sleep(1)
        ari.hangup_channel(channel_id)
        
    except Exception as e:
        logger.error(f"Error in media operations: {e}")
    finally:
        ari.disconnect()


def demo_bridge_operations():
    """Demonstrate bridge operations for multi-party calls"""
    logger.info("=== Bridge Operations Demo ===")
    
    ari = AsteriskARI()
    
    try:
        ari.connect()
        
        # Create a bridge
        bridge_id = ari.create_bridge("mixing")
        if bridge_id:
            logger.info(f"✓ Bridge created: {bridge_id}")
        
        # Originate first call
        channel1_id = ari.originate_call(
            endpoint="PJSIP/1000",
            context="test",
            extension="echo"
        )
        
        if channel1_id:
            logger.info(f"✓ First channel created: {channel1_id}")
            ari.answer_channel(channel1_id)
            
            # Add to bridge
            if ari.add_channel_to_bridge(channel1_id, bridge_id):
                logger.info("✓ First channel added to bridge")
        
        time.sleep(1)
        
        # Originate second call
        channel2_id = ari.originate_call(
            endpoint="PJSIP/1001",
            context="test",
            extension="echo"
        )
        
        if channel2_id:
            logger.info(f"✓ Second channel created: {channel2_id}")
            ari.answer_channel(channel2_id)
            
            # Add to bridge
            if ari.add_channel_to_bridge(channel2_id, bridge_id):
                logger.info("✓ Second channel added to bridge")
        
        logger.info("✓ Both channels in bridge - can communicate")
        time.sleep(5)
        
        # Remove channels from bridge
        if channel1_id:
            ari.remove_channel_from_bridge(channel1_id, bridge_id)
            ari.hangup_channel(channel1_id)
            logger.info("✓ First channel removed and hung up")
        
        if channel2_id:
            ari.remove_channel_from_bridge(channel2_id, bridge_id)
            ari.hangup_channel(channel2_id)
            logger.info("✓ Second channel removed and hung up")
        
        # Destroy bridge
        if ari.destroy_bridge(bridge_id):
            logger.info("✓ Bridge destroyed")
        
    except Exception as e:
        logger.error(f"Error in bridge operations: {e}")
    finally:
        ari.disconnect()


def demo_advanced_features():
    """Demonstrate advanced ARI features"""
    logger.info("=== Advanced Features Demo ===")
    
    ari = AsteriskARI()
    
    try:
        ari.connect()
        
        # Originate a test call
        channel_id = ari.originate_call(
            endpoint="PJSIP/1000",
            context="test",
            extension="echo"
        )
        
        if not channel_id:
            logger.warning("Cannot demo advanced features without active channel")
            return
        
        logger.info(f"✓ Working with channel: {channel_id}")
        ari.answer_channel(channel_id)
        
        # Subscribe to channel events
        if ari.subscribe_to_events(f"channel:{channel_id}"):
            logger.info("✓ Subscribed to channel events")
        
        time.sleep(1)
        
        # Silence detection
        if ari.start_silence_detection(channel_id):
            logger.info("✓ Silence detection started")
        
        time.sleep(2)
        
        if ari.stop_silence_detection(channel_id):
            logger.info("✓ Silence detection stopped")
        
        # Create snoop channel for monitoring
        snoop_id = ari.snoop_channel(
            channel_id=channel_id,
            spy="both",
            whisper="none"
        )
        
        if snoop_id:
            logger.info(f"✓ Snoop channel created: {snoop_id}")
            time.sleep(2)
            ari.hangup_channel(snoop_id)
            logger.info("✓ Snoop channel hung up")
        
        # Unsubscribe from events
        if ari.unsubscribe_from_events(f"channel:{channel_id}"):
            logger.info("✓ Unsubscribed from channel events")
        
        # Hangup main channel
        time.sleep(1)
        ari.hangup_channel(channel_id)
        logger.info("✓ Main channel hung up")
        
    except Exception as e:
        logger.error(f"Error in advanced features: {e}")
    finally:
        ari.disconnect()


async def demo_event_driven_application():
    """Demonstrate event-driven ARI application"""
    logger.info("=== Event-Driven Application Demo ===")
    logger.info("This would start a long-running ARI application")
    logger.info("See src/asterisk/ari_call_handler.py for full implementation")
    
    # This is a simplified example
    # For a full implementation, see ari_call_handler.py
    
    def on_stasis_start(channel_obj, event):
        logger.info(f"Channel entered application: {channel_obj.id}")
        # Handle the call here
        channel_obj.answer()
        channel_obj.play(media="sound:hello-world")
    
    def on_stasis_end(channel_obj, event):
        logger.info(f"Channel left application: {channel_obj.id}")
    
    logger.info("✓ Event handlers defined")
    logger.info("To run: ari.start_event_loop(on_stasis_start, on_stasis_end)")


def main():
    """Run all demos"""
    setup_logging()
    
    logger.info("╔════════════════════════════════════════════════════════════════╗")
    logger.info("║                                                                ║")
    logger.info("║         ARI Features Demonstration                            ║")
    logger.info("║         Asterisk 20.15.2                                      ║")
    logger.info("║                                                                ║")
    logger.info("╚════════════════════════════════════════════════════════════════╝")
    logger.info("")
    
    demos = [
        ("Basic Operations", demo_basic_operations),
        ("Call Origination", demo_call_origination),
        ("Channel Control", demo_channel_control),
        ("Media Operations", demo_media_operations),
        ("Bridge Operations", demo_bridge_operations),
        ("Advanced Features", demo_advanced_features),
        ("Event-Driven App", lambda: asyncio.run(demo_event_driven_application())),
    ]
    
    for name, demo_func in demos:
        logger.info(f"\n{'='*70}")
        try:
            demo_func()
        except Exception as e:
            logger.error(f"Error in {name} demo: {e}")
        
        logger.info(f"{'='*70}\n")
        time.sleep(2)
    
    logger.info("\n✓ All demos completed!")
    logger.info("\nNote: Some demos require active Asterisk with configured endpoints")
    logger.info("Adjust PJSIP endpoints in the demos to match your configuration")


if __name__ == "__main__":
    main()

"""
Asterisk ARI (Asterisk REST Interface) Integration
Handles telephony operations with Asterisk PBX using modern REST API
"""

import asyncio
import ari
from typing import Optional, Callable, Dict, Any
from loguru import logger

from ..config import settings


class AsteriskARI:
    """Asterisk ARI Interface for call control"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        app_name: str = "aiagc"
    ):
        """
        Initialize ARI interface
        
        Args:
            host: Asterisk host
            port: ARI HTTP port (default 8088)
            username: ARI username
            password: ARI password
            app_name: Stasis application name
        """
        self.host = host or settings.asterisk_ari_host
        self.port = port or settings.asterisk_ari_port
        self.username = username or settings.asterisk_ari_username
        self.password = password or settings.asterisk_ari_password
        self.app_name = app_name
        
        self.client = None
        self.channel = None
        self.bridge = None
        self.connected = False
        
    def connect(self):
        """Connect to Asterisk ARI"""
        try:
            self.client = ari.connect(
                f'http://{self.host}:{self.port}',
                self.username,
                self.password
            )
            self.connected = True
            logger.info(f"Connected to Asterisk ARI at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error connecting to ARI: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from ARI"""
        if self.client:
            try:
                self.client.close()
                self.connected = False
                logger.info("Disconnected from ARI")
            except Exception as e:
                logger.error(f"Error disconnecting from ARI: {e}")
    
    def answer_channel(self, channel_id: str = None) -> bool:
        """
        Answer the call
        
        Args:
            channel_id: Channel ID to answer (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.answer()
                logger.info(f"Answered channel: {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error answering channel: {e}")
            return False
    
    def hangup_channel(self, channel_id: str = None) -> bool:
        """
        Hang up the call
        
        Args:
            channel_id: Channel ID to hangup (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.hangup()
                logger.info(f"Hung up channel: {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error hanging up channel: {e}")
            return False
    
    def play_media(self, media: str, channel_id: str = None, language: str = None) -> Optional[str]:
        """
        Play media file to channel
        
        Args:
            media: Media URI (e.g., 'sound:hello-world' or 'recording:myfile')
            channel_id: Channel ID (uses self.channel if not provided)
            language: Language code for media
            
        Returns:
            Playback ID or None
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                playback = channel.play(media=media, lang=language or settings.asterisk_language)
                logger.info(f"Playing media '{media}' on channel {channel.id}")
                return playback.id
            return None
        except Exception as e:
            logger.error(f"Error playing media: {e}")
            return None
    
    def record_channel(
        self,
        name: str,
        format: str = "wav",
        max_duration_seconds: int = 0,
        max_silence_seconds: int = 0,
        channel_id: str = None
    ) -> Optional[str]:
        """
        Record audio from channel
        
        Args:
            name: Recording name
            format: Audio format (wav, gsm, etc.)
            max_duration_seconds: Maximum recording duration
            max_silence_seconds: Maximum silence duration before stopping
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Recording name or None
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                recording = channel.record(
                    name=name,
                    format=format,
                    maxDurationSeconds=max_duration_seconds,
                    maxSilenceSeconds=max_silence_seconds,
                    ifExists='overwrite',
                    beep=True
                )
                logger.info(f"Recording started: {name}")
                return recording.name
            return None
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return None
    
    def set_channel_variable(self, variable: str, value: str, channel_id: str = None) -> bool:
        """
        Set channel variable
        
        Args:
            variable: Variable name
            value: Variable value
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.setChannelVar(variable=variable, value=value)
                logger.debug(f"Set variable {variable}={value} on channel {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting channel variable: {e}")
            return False
    
    def get_channel_variable(self, variable: str, channel_id: str = None) -> Optional[str]:
        """
        Get channel variable
        
        Args:
            variable: Variable name
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Variable value or None
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                result = channel.getChannelVar(variable=variable)
                return result.get('value')
            return None
        except Exception as e:
            logger.error(f"Error getting channel variable: {e}")
            return None
    
    def get_channel_info(self, channel_id: str = None) -> Dict[str, Any]:
        """
        Get channel information
        
        Args:
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Channel information dictionary
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                return {
                    'id': channel.id,
                    'name': channel.json.get('name', ''),
                    'state': channel.json.get('state', ''),
                    'caller': channel.json.get('caller', {}),
                    'connected': channel.json.get('connected', {}),
                    'accountcode': channel.json.get('accountcode', ''),
                    'dialplan': channel.json.get('dialplan', {}),
                    'creationtime': channel.json.get('creationtime', ''),
                    'language': channel.json.get('language', ''),
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return {}
    
    def originate_call(
        self,
        endpoint: str,
        extension: str = None,
        context: str = None,
        caller_id: str = None,
        variables: Dict[str, str] = None,
        app: str = None,
        app_args: str = None
    ) -> Optional[str]:
        """
        Originate outbound call
        
        Args:
            endpoint: Channel endpoint (e.g., 'PJSIP/1234567890')
            extension: Extension to connect to
            context: Dialplan context
            caller_id: Caller ID to use
            variables: Channel variables
            app: Stasis application name
            app_args: Application arguments
            
        Returns:
            Channel ID or None
        """
        try:
            context = context or settings.asterisk_context
            caller_id = caller_id or settings.asterisk_caller_id
            app = app or self.app_name
            
            # Build originate parameters
            params = {
                'endpoint': endpoint,
                'app': app,
            }
            
            if extension and context:
                params['extension'] = extension
                params['context'] = context
            
            if caller_id:
                params['callerId'] = caller_id
            
            if app_args:
                params['appArgs'] = app_args
            
            if variables:
                params['variables'] = variables
            
            channel = self.client.channels.originate(**params)
            logger.info(f"Call originated to {endpoint}: {channel.id}")
            return channel.id
            
        except Exception as e:
            logger.error(f"Error originating call: {e}")
            return None
    
    def create_bridge(self, bridge_type: str = "mixing") -> Optional[str]:
        """
        Create a bridge for mixing channels
        
        Args:
            bridge_type: Type of bridge ('mixing' or 'holding')
            
        Returns:
            Bridge ID or None
        """
        try:
            bridge = self.client.bridges.create(type=bridge_type)
            self.bridge = bridge
            logger.info(f"Bridge created: {bridge.id}")
            return bridge.id
        except Exception as e:
            logger.error(f"Error creating bridge: {e}")
            return None
    
    def add_channel_to_bridge(self, channel_id: str, bridge_id: str = None) -> bool:
        """
        Add channel to bridge
        
        Args:
            channel_id: Channel ID to add
            bridge_id: Bridge ID (uses self.bridge if not provided)
            
        Returns:
            Success status
        """
        try:
            bridge = self.client.bridges.get(bridgeId=bridge_id) if bridge_id else self.bridge
            if bridge:
                bridge.addChannel(channel=channel_id)
                logger.info(f"Added channel {channel_id} to bridge {bridge.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding channel to bridge: {e}")
            return False
    
    def remove_channel_from_bridge(self, channel_id: str, bridge_id: str = None) -> bool:
        """
        Remove channel from bridge
        
        Args:
            channel_id: Channel ID to remove
            bridge_id: Bridge ID (uses self.bridge if not provided)
            
        Returns:
            Success status
        """
        try:
            bridge = self.client.bridges.get(bridgeId=bridge_id) if bridge_id else self.bridge
            if bridge:
                bridge.removeChannel(channel=channel_id)
                logger.info(f"Removed channel {channel_id} from bridge {bridge.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing channel from bridge: {e}")
            return False
    
    def destroy_bridge(self, bridge_id: str = None) -> bool:
        """
        Destroy bridge
        
        Args:
            bridge_id: Bridge ID (uses self.bridge if not provided)
            
        Returns:
            Success status
        """
        try:
            bridge = self.client.bridges.get(bridgeId=bridge_id) if bridge_id else self.bridge
            if bridge:
                bridge.destroy()
                logger.info(f"Bridge destroyed: {bridge.id}")
                if self.bridge and self.bridge.id == bridge.id:
                    self.bridge = None
                return True
            return False
        except Exception as e:
            logger.error(f"Error destroying bridge: {e}")
            return False
    
    def send_dtmf(self, dtmf: str, channel_id: str = None, duration: int = 100) -> bool:
        """
        Send DTMF tones to channel
        
        Args:
            dtmf: DTMF string to send (0-9, *, #, A-D)
            channel_id: Channel ID (uses self.channel if not provided)
            duration: Duration of each DTMF tone in milliseconds
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.sendDTMF(dtmf=dtmf, duration=duration)
                logger.info(f"Sent DTMF '{dtmf}' to channel {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error sending DTMF: {e}")
            return False
    
    def mute_channel(self, direction: str = "both", channel_id: str = None) -> bool:
        """
        Mute audio on channel
        
        Args:
            direction: Direction to mute ('in', 'out', or 'both')
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.mute(direction=direction)
                logger.info(f"Muted {direction} on channel {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error muting channel: {e}")
            return False
    
    def unmute_channel(self, direction: str = "both", channel_id: str = None) -> bool:
        """
        Unmute audio on channel
        
        Args:
            direction: Direction to unmute ('in', 'out', or 'both')
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.unmute(direction=direction)
                logger.info(f"Unmuted {direction} on channel {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unmuting channel: {e}")
            return False
    
    def hold_channel(self, channel_id: str = None) -> bool:
        """
        Place channel on hold
        
        Args:
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.hold()
                logger.info(f"Placed channel {channel.id} on hold")
                return True
            return False
        except Exception as e:
            logger.error(f"Error placing channel on hold: {e}")
            return False
    
    def unhold_channel(self, channel_id: str = None) -> bool:
        """
        Remove channel from hold
        
        Args:
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.unhold()
                logger.info(f"Removed channel {channel.id} from hold")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing channel from hold: {e}")
            return False
    
    def snoop_channel(
        self,
        channel_id: str,
        spy: str = "both",
        whisper: str = "none",
        app: str = None,
        app_args: str = None
    ) -> Optional[str]:
        """
        Create a snoop channel for monitoring/whispering
        
        Args:
            channel_id: Channel ID to snoop on
            spy: Direction to spy on ('in', 'out', 'both', 'none')
            whisper: Direction to whisper ('in', 'out', 'both', 'none')
            app: Stasis application for snoop channel
            app_args: Arguments for the application
            
        Returns:
            Snoop channel ID or None
        """
        try:
            channel = self.client.channels.get(channelId=channel_id)
            if channel:
                app = app or self.app_name
                snoop = channel.snoopChannel(
                    spy=spy,
                    whisper=whisper,
                    app=app,
                    appArgs=app_args
                )
                logger.info(f"Created snoop channel {snoop.id} for {channel_id}")
                return snoop.id
            return None
        except Exception as e:
            logger.error(f"Error creating snoop channel: {e}")
            return None
    
    def redirect_channel(self, endpoint: str, channel_id: str = None) -> bool:
        """
        Redirect channel to a new endpoint
        
        Args:
            endpoint: New endpoint to redirect to
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.redirect(endpoint=endpoint)
                logger.info(f"Redirected channel {channel.id} to {endpoint}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error redirecting channel: {e}")
            return False
    
    def ring_channel(self, channel_id: str = None) -> bool:
        """
        Indicate ringing on channel
        
        Args:
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.ring()
                logger.info(f"Ringing channel {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error ringing channel: {e}")
            return False
    
    def stop_ringing_channel(self, channel_id: str = None) -> bool:
        """
        Stop ringing indication on channel
        
        Args:
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.ringStop()
                logger.info(f"Stopped ringing on channel {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping ring on channel: {e}")
            return False
    
    def start_silence_detection(self, channel_id: str = None) -> bool:
        """
        Start silence detection on channel
        
        Args:
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.startSilence()
                logger.info(f"Started silence detection on channel {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error starting silence detection: {e}")
            return False
    
    def stop_silence_detection(self, channel_id: str = None) -> bool:
        """
        Stop silence detection on channel
        
        Args:
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Success status
        """
        try:
            channel = self.client.channels.get(channelId=channel_id) if channel_id else self.channel
            if channel:
                channel.stopSilence()
                logger.info(f"Stopped silence detection on channel {channel.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping silence detection: {e}")
            return False
    
    def get_asterisk_info(self) -> Dict[str, Any]:
        """
        Get Asterisk system information
        
        Returns:
            System information dictionary
        """
        try:
            info = self.client.asterisk.getInfo()
            return {
                'version': info.get('version', ''),
                'system_info': info.get('system', {}),
                'config': info.get('config', {}),
                'status': info.get('status', {}),
            }
        except Exception as e:
            logger.error(f"Error getting Asterisk info: {e}")
            return {}
    
    def list_channels(self) -> list:
        """
        List all active channels
        
        Returns:
            List of channel dictionaries
        """
        try:
            channels = self.client.channels.list()
            return [
                {
                    'id': ch.id,
                    'name': ch.json.get('name', ''),
                    'state': ch.json.get('state', ''),
                    'caller': ch.json.get('caller', {}),
                    'connected': ch.json.get('connected', {}),
                }
                for ch in channels
            ]
        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            return []
    
    def list_bridges(self) -> list:
        """
        List all active bridges
        
        Returns:
            List of bridge dictionaries
        """
        try:
            bridges = self.client.bridges.list()
            return [
                {
                    'id': br.id,
                    'type': br.json.get('bridge_type', ''),
                    'technology': br.json.get('technology', ''),
                    'channels': br.json.get('channels', []),
                }
                for br in bridges
            ]
        except Exception as e:
            logger.error(f"Error listing bridges: {e}")
            return []
    
    def get_recording(self, recording_name: str) -> Optional[Dict[str, Any]]:
        """
        Get stored recording information
        
        Args:
            recording_name: Name of the recording
            
        Returns:
            Recording information or None
        """
        try:
            recording = self.client.recordings.getStored(recordingName=recording_name)
            return {
                'name': recording.json.get('name', ''),
                'format': recording.json.get('format', ''),
                'state': recording.json.get('state', ''),
            }
        except Exception as e:
            logger.error(f"Error getting recording: {e}")
            return None
    
    def delete_recording(self, recording_name: str) -> bool:
        """
        Delete a stored recording
        
        Args:
            recording_name: Name of the recording
            
        Returns:
            Success status
        """
        try:
            recording = self.client.recordings.getStored(recordingName=recording_name)
            if recording:
                recording.deleteStored()
                logger.info(f"Deleted recording: {recording_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting recording: {e}")
            return False
    
    def play_recording(self, recording_name: str, channel_id: str = None) -> Optional[str]:
        """
        Play a stored recording on a channel
        
        Args:
            recording_name: Name of the recording to play
            channel_id: Channel ID (uses self.channel if not provided)
            
        Returns:
            Playback ID or None
        """
        try:
            media = f"recording:{recording_name}"
            return self.play_media(media, channel_id)
        except Exception as e:
            logger.error(f"Error playing recording: {e}")
            return None
    
    def subscribe_to_events(self, event_source: str) -> bool:
        """
        Subscribe to events from a specific source
        
        Args:
            event_source: Event source (e.g., 'channel:channel_id' or 'bridge:bridge_id')
            
        Returns:
            Success status
        """
        try:
            self.client.applications.subscribe(
                applicationName=self.app_name,
                eventSource=event_source
            )
            logger.info(f"Subscribed to events from {event_source}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to events: {e}")
            return False
    
    def unsubscribe_from_events(self, event_source: str) -> bool:
        """
        Unsubscribe from events from a specific source
        
        Args:
            event_source: Event source (e.g., 'channel:channel_id' or 'bridge:bridge_id')
            
        Returns:
            Success status
        """
        try:
            self.client.applications.unsubscribe(
                applicationName=self.app_name,
                eventSource=event_source
            )
            logger.info(f"Unsubscribed from events from {event_source}")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from events: {e}")
            return False
    
    def start_event_loop(self, on_stasis_start: Callable = None, on_stasis_end: Callable = None):
        """
        Start ARI event loop
        
        Args:
            on_stasis_start: Callback for StasisStart events
            on_stasis_end: Callback for StasisEnd events
        """
        try:
            if on_stasis_start:
                self.client.on_channel_event('StasisStart', on_stasis_start)
            
            if on_stasis_end:
                self.client.on_channel_event('StasisEnd', on_stasis_end)
            
            logger.info(f"Starting ARI event loop for app '{self.app_name}'")
            self.client.run(apps=self.app_name)
            
        except Exception as e:
            logger.error(f"Error in event loop: {e}")
            raise

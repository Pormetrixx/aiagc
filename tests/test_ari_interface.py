#!/usr/bin/env python3
"""
Unit tests for ARI interface
Tests all ARI functionality with Asterisk 20.15.2
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.asterisk.ari_interface import AsteriskARI


class TestARIConnection:
    """Test ARI connection operations"""
    
    @patch('src.asterisk.ari_interface.ari')
    def test_connect_success(self, mock_ari):
        """Test successful ARI connection"""
        mock_client = Mock()
        mock_ari.connect.return_value = mock_client
        
        ari_interface = AsteriskARI(
            host="localhost",
            port=8088,
            username="asterisk",
            password="test_password"
        )
        
        ari_interface.connect()
        
        assert ari_interface.connected is True
        assert ari_interface.client == mock_client
        mock_ari.connect.assert_called_once_with(
            'http://localhost:8088',
            'asterisk',
            'test_password'
        )
    
    @patch('src.asterisk.ari_interface.ari')
    def test_connect_failure(self, mock_ari):
        """Test ARI connection failure"""
        mock_ari.connect.side_effect = Exception("Connection failed")
        
        ari_interface = AsteriskARI()
        
        with pytest.raises(Exception):
            ari_interface.connect()
    
    def test_disconnect(self):
        """Test disconnecting from ARI"""
        ari_interface = AsteriskARI()
        ari_interface.client = Mock()
        ari_interface.connected = True
        
        ari_interface.disconnect()
        
        assert ari_interface.connected is False
        ari_interface.client.close.assert_called_once()


class TestChannelOperations:
    """Test channel control operations"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
        
        # Mock channel
        self.mock_channel = Mock()
        self.mock_channel.id = "test-channel-123"
        self.ari.client.channels.get.return_value = self.mock_channel
    
    def test_answer_channel(self):
        """Test answering a channel"""
        result = self.ari.answer_channel("test-channel-123")
        
        assert result is True
        self.mock_channel.answer.assert_called_once()
    
    def test_hangup_channel(self):
        """Test hanging up a channel"""
        result = self.ari.hangup_channel("test-channel-123")
        
        assert result is True
        self.mock_channel.hangup.assert_called_once()
    
    def test_mute_channel(self):
        """Test muting a channel"""
        result = self.ari.mute_channel("both", "test-channel-123")
        
        assert result is True
        self.mock_channel.mute.assert_called_once_with(direction="both")
    
    def test_unmute_channel(self):
        """Test unmuting a channel"""
        result = self.ari.unmute_channel("both", "test-channel-123")
        
        assert result is True
        self.mock_channel.unmute.assert_called_once_with(direction="both")
    
    def test_hold_channel(self):
        """Test putting channel on hold"""
        result = self.ari.hold_channel("test-channel-123")
        
        assert result is True
        self.mock_channel.hold.assert_called_once()
    
    def test_unhold_channel(self):
        """Test removing channel from hold"""
        result = self.ari.unhold_channel("test-channel-123")
        
        assert result is True
        self.mock_channel.unhold.assert_called_once()
    
    def test_ring_channel(self):
        """Test ringing a channel"""
        result = self.ari.ring_channel("test-channel-123")
        
        assert result is True
        self.mock_channel.ring.assert_called_once()
    
    def test_stop_ringing_channel(self):
        """Test stopping ring on a channel"""
        result = self.ari.stop_ringing_channel("test-channel-123")
        
        assert result is True
        self.mock_channel.ringStop.assert_called_once()
    
    def test_send_dtmf(self):
        """Test sending DTMF tones"""
        result = self.ari.send_dtmf("12345", "test-channel-123", duration=100)
        
        assert result is True
        self.mock_channel.sendDTMF.assert_called_once_with(dtmf="12345", duration=100)


class TestChannelVariables:
    """Test channel variable operations"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
        
        self.mock_channel = Mock()
        self.mock_channel.id = "test-channel-123"
        self.ari.client.channels.get.return_value = self.mock_channel
    
    def test_set_channel_variable(self):
        """Test setting a channel variable"""
        result = self.ari.set_channel_variable("TEST_VAR", "test_value", "test-channel-123")
        
        assert result is True
        self.mock_channel.setChannelVar.assert_called_once_with(
            variable="TEST_VAR",
            value="test_value"
        )
    
    def test_get_channel_variable(self):
        """Test getting a channel variable"""
        self.mock_channel.getChannelVar.return_value = {'value': 'test_value'}
        
        result = self.ari.get_channel_variable("TEST_VAR", "test-channel-123")
        
        assert result == 'test_value'
        self.mock_channel.getChannelVar.assert_called_once_with(variable="TEST_VAR")


class TestMediaOperations:
    """Test media playback and recording"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
        
        self.mock_channel = Mock()
        self.mock_channel.id = "test-channel-123"
        self.ari.client.channels.get.return_value = self.mock_channel
        
        self.mock_playback = Mock()
        self.mock_playback.id = "playback-123"
        self.mock_channel.play.return_value = self.mock_playback
    
    def test_play_media(self):
        """Test playing media"""
        playback_id = self.ari.play_media("sound:hello-world", "test-channel-123", "en")
        
        assert playback_id == "playback-123"
        self.mock_channel.play.assert_called_once_with(media="sound:hello-world", lang="en")
    
    def test_record_channel(self):
        """Test recording a channel"""
        self.mock_recording = Mock()
        self.mock_recording.name = "test_recording"
        self.mock_channel.record.return_value = self.mock_recording
        
        recording_name = self.ari.record_channel(
            name="test_recording",
            format="wav",
            max_duration_seconds=60,
            max_silence_seconds=5,
            channel_id="test-channel-123"
        )
        
        assert recording_name == "test_recording"
        self.mock_channel.record.assert_called_once()
    
    def test_play_recording(self):
        """Test playing a stored recording"""
        playback_id = self.ari.play_recording("my_recording", "test-channel-123")
        
        assert playback_id == "playback-123"
        self.mock_channel.play.assert_called_once_with(
            media="recording:my_recording",
            lang=pytest.ANY
        )


class TestBridgeOperations:
    """Test bridge operations"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
        
        self.mock_bridge = Mock()
        self.mock_bridge.id = "bridge-123"
        self.ari.client.bridges.create.return_value = self.mock_bridge
        self.ari.client.bridges.get.return_value = self.mock_bridge
    
    def test_create_bridge(self):
        """Test creating a bridge"""
        bridge_id = self.ari.create_bridge("mixing")
        
        assert bridge_id == "bridge-123"
        self.ari.client.bridges.create.assert_called_once_with(type="mixing")
    
    def test_add_channel_to_bridge(self):
        """Test adding channel to bridge"""
        result = self.ari.add_channel_to_bridge("channel-123", "bridge-123")
        
        assert result is True
        self.mock_bridge.addChannel.assert_called_once_with(channel="channel-123")
    
    def test_remove_channel_from_bridge(self):
        """Test removing channel from bridge"""
        result = self.ari.remove_channel_from_bridge("channel-123", "bridge-123")
        
        assert result is True
        self.mock_bridge.removeChannel.assert_called_once_with(channel="channel-123")
    
    def test_destroy_bridge(self):
        """Test destroying a bridge"""
        result = self.ari.destroy_bridge("bridge-123")
        
        assert result is True
        self.mock_bridge.destroy.assert_called_once()


class TestCallOrigination:
    """Test call origination"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
        
        self.mock_channel = Mock()
        self.mock_channel.id = "originated-channel-123"
        self.ari.client.channels.originate.return_value = self.mock_channel
    
    def test_originate_call_basic(self):
        """Test basic call origination"""
        channel_id = self.ari.originate_call(
            endpoint="PJSIP/1234567890",
            extension="s",
            context="outbound-calls"
        )
        
        assert channel_id == "originated-channel-123"
        self.ari.client.channels.originate.assert_called_once()
    
    def test_originate_call_with_variables(self):
        """Test call origination with variables"""
        variables = {
            "CAMPAIGN_TYPE": "test",
            "CALL_SOURCE": "unit_test"
        }
        
        channel_id = self.ari.originate_call(
            endpoint="PJSIP/1234567890",
            variables=variables
        )
        
        assert channel_id == "originated-channel-123"
        call_args = self.ari.client.channels.originate.call_args
        assert call_args[1]['variables'] == variables


class TestAdvancedFeatures:
    """Test advanced ARI features"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
        
        self.mock_channel = Mock()
        self.mock_channel.id = "test-channel-123"
        self.ari.client.channels.get.return_value = self.mock_channel
    
    def test_start_silence_detection(self):
        """Test starting silence detection"""
        result = self.ari.start_silence_detection("test-channel-123")
        
        assert result is True
        self.mock_channel.startSilence.assert_called_once()
    
    def test_stop_silence_detection(self):
        """Test stopping silence detection"""
        result = self.ari.stop_silence_detection("test-channel-123")
        
        assert result is True
        self.mock_channel.stopSilence.assert_called_once()
    
    def test_snoop_channel(self):
        """Test creating snoop channel"""
        mock_snoop = Mock()
        mock_snoop.id = "snoop-channel-123"
        self.mock_channel.snoopChannel.return_value = mock_snoop
        
        snoop_id = self.ari.snoop_channel(
            channel_id="test-channel-123",
            spy="both",
            whisper="none"
        )
        
        assert snoop_id == "snoop-channel-123"
        self.mock_channel.snoopChannel.assert_called_once()
    
    def test_redirect_channel(self):
        """Test redirecting a channel"""
        result = self.ari.redirect_channel("PJSIP/new-endpoint", "test-channel-123")
        
        assert result is True
        self.mock_channel.redirect.assert_called_once_with(endpoint="PJSIP/new-endpoint")
    
    def test_subscribe_to_events(self):
        """Test subscribing to events"""
        result = self.ari.subscribe_to_events("channel:test-channel-123")
        
        assert result is True
        self.ari.client.applications.subscribe.assert_called_once_with(
            applicationName="aiagc",
            eventSource="channel:test-channel-123"
        )
    
    def test_unsubscribe_from_events(self):
        """Test unsubscribing from events"""
        result = self.ari.unsubscribe_from_events("channel:test-channel-123")
        
        assert result is True
        self.ari.client.applications.unsubscribe.assert_called_once_with(
            applicationName="aiagc",
            eventSource="channel:test-channel-123"
        )


class TestSystemInfo:
    """Test system information retrieval"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
    
    def test_get_asterisk_info(self):
        """Test getting Asterisk system info"""
        mock_info = {
            'version': '20.15.2',
            'system': {'name': 'Test System'},
            'config': {},
            'status': {}
        }
        self.ari.client.asterisk.getInfo.return_value = mock_info
        
        info = self.ari.get_asterisk_info()
        
        assert info['version'] == '20.15.2'
        self.ari.client.asterisk.getInfo.assert_called_once()
    
    def test_list_channels(self):
        """Test listing active channels"""
        mock_channel = Mock()
        mock_channel.id = "channel-123"
        mock_channel.json = {
            'name': 'PJSIP/test-00000001',
            'state': 'Up',
            'caller': {'number': '1234567890'},
            'connected': {'number': '0987654321'}
        }
        
        self.ari.client.channels.list.return_value = [mock_channel]
        
        channels = self.ari.list_channels()
        
        assert len(channels) == 1
        assert channels[0]['id'] == "channel-123"
        assert channels[0]['state'] == 'Up'
    
    def test_list_bridges(self):
        """Test listing active bridges"""
        mock_bridge = Mock()
        mock_bridge.id = "bridge-123"
        mock_bridge.json = {
            'bridge_type': 'mixing',
            'technology': 'simple_bridge',
            'channels': ['channel-1', 'channel-2']
        }
        
        self.ari.client.bridges.list.return_value = [mock_bridge]
        
        bridges = self.ari.list_bridges()
        
        assert len(bridges) == 1
        assert bridges[0]['id'] == "bridge-123"
        assert bridges[0]['type'] == 'mixing'
        assert len(bridges[0]['channels']) == 2


class TestRecordingOperations:
    """Test recording management"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
        
        self.mock_recording = Mock()
        self.mock_recording.json = {
            'name': 'test_recording',
            'format': 'wav',
            'state': 'done'
        }
        self.ari.client.recordings.getStored.return_value = self.mock_recording
    
    def test_get_recording(self):
        """Test getting recording information"""
        info = self.ari.get_recording("test_recording")
        
        assert info['name'] == 'test_recording'
        assert info['format'] == 'wav'
        assert info['state'] == 'done'
    
    def test_delete_recording(self):
        """Test deleting a recording"""
        result = self.ari.delete_recording("test_recording")
        
        assert result is True
        self.mock_recording.deleteStored.assert_called_once()


class TestChannelInfo:
    """Test channel information retrieval"""
    
    def setup_method(self):
        """Setup test fixture"""
        self.ari = AsteriskARI()
        self.ari.client = Mock()
        self.ari.connected = True
        
        self.mock_channel = Mock()
        self.mock_channel.id = "test-channel-123"
        self.mock_channel.json = {
            'name': 'PJSIP/test-00000001',
            'state': 'Up',
            'caller': {'number': '1234567890', 'name': 'Test Caller'},
            'connected': {'number': '0987654321', 'name': 'Test Callee'},
            'accountcode': 'test-account',
            'dialplan': {'context': 'outbound', 'exten': 's', 'priority': 1},
            'creationtime': '2024-01-01T00:00:00.000Z',
            'language': 'en'
        }
        self.ari.client.channels.get.return_value = self.mock_channel
    
    def test_get_channel_info(self):
        """Test getting comprehensive channel info"""
        info = self.ari.get_channel_info("test-channel-123")
        
        assert info['id'] == 'test-channel-123'
        assert info['name'] == 'PJSIP/test-00000001'
        assert info['state'] == 'Up'
        assert info['caller']['number'] == '1234567890'
        assert info['connected']['number'] == '0987654321'
        assert info['language'] == 'en'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Asterisk AGI (Asterisk Gateway Interface) Integration
Handles telephony operations with Asterisk PBX
"""

import asyncio
from typing import Optional, Callable, Dict, Any
from loguru import logger
import socket
import re

from ..config import settings


class AsteriskAGI:
    """Asterisk AGI Interface for call control"""
    
    def __init__(self):
        """Initialize AGI interface"""
        self.env = {}
        self.stdin = None
        self.stdout = None
        
    def setup(self):
        """Setup AGI environment"""
        import sys
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        
        # Read AGI environment variables
        while True:
            line = self.stdin.readline().strip()
            if not line:
                break
            
            key, value = line.split(': ', 1)
            self.env[key.replace('agi_', '')] = value
        
        logger.info(f"AGI Environment: {self.env}")
    
    def _send_command(self, command: str) -> tuple[int, str]:
        """
        Send command to Asterisk
        
        Args:
            command: AGI command
            
        Returns:
            Tuple of (result_code, result_data)
        """
        logger.debug(f"AGI Command: {command}")
        self.stdout.write(f"{command}\n")
        self.stdout.flush()
        
        response = self.stdin.readline().strip()
        logger.debug(f"AGI Response: {response}")
        
        # Parse response
        match = re.search(r'result=(-?\d+)', response)
        result = int(match.group(1)) if match else -1
        
        return result, response
    
    def answer(self) -> bool:
        """Answer the call"""
        result, _ = self._send_command("ANSWER")
        return result == 0
    
    def hangup(self) -> bool:
        """Hang up the call"""
        result, _ = self._send_command("HANGUP")
        return result == 0
    
    def stream_file(self, filename: str, escape_digits: str = "") -> int:
        """
        Stream audio file to caller
        
        Args:
            filename: Audio file path (without extension)
            escape_digits: Digits that can interrupt playback
            
        Returns:
            Digit pressed or 0
        """
        result, _ = self._send_command(f'STREAM FILE "{filename}" "{escape_digits}"')
        return result
    
    def get_data(
        self,
        filename: str,
        timeout: int = 5000,
        max_digits: int = 10
    ) -> str:
        """
        Get DTMF input from caller
        
        Args:
            filename: Prompt file
            timeout: Timeout in milliseconds
            max_digits: Maximum digits to accept
            
        Returns:
            Digits entered
        """
        result, response = self._send_command(
            f'GET DATA "{filename}" {timeout} {max_digits}'
        )
        
        # Extract digits from response
        match = re.search(r'\((\d*)\)', response)
        return match.group(1) if match else ""
    
    def set_variable(self, name: str, value: str) -> bool:
        """Set channel variable"""
        result, _ = self._send_command(f'SET VARIABLE {name} "{value}"')
        return result == 1
    
    def get_variable(self, name: str) -> Optional[str]:
        """Get channel variable"""
        result, response = self._send_command(f'GET VARIABLE {name}')
        
        match = re.search(r'\((.*?)\)', response)
        return match.group(1) if match else None
    
    def record_file(
        self,
        filename: str,
        format: str = "wav",
        escape_digits: str = "#",
        timeout: int = -1,
        beep: bool = True
    ) -> tuple[int, str]:
        """
        Record audio from caller
        
        Args:
            filename: File to save recording
            format: Audio format
            escape_digits: Digits to stop recording
            timeout: Max recording time in milliseconds
            beep: Play beep before recording
            
        Returns:
            Tuple of (digit_pressed, endpos)
        """
        beep_flag = "beep" if beep else ""
        result, response = self._send_command(
            f'RECORD FILE "{filename}" {format} "{escape_digits}" {timeout} {beep_flag}'
        )
        
        match = re.search(r'endpos=(\d+)', response)
        endpos = match.group(1) if match else "0"
        
        return result, endpos
    
    def say_digits(self, digits: str, escape_digits: str = "") -> int:
        """Say digits to caller"""
        result, _ = self._send_command(f'SAY DIGITS {digits} "{escape_digits}"')
        return result
    
    def say_number(self, number: int, escape_digits: str = "") -> int:
        """Say number to caller"""
        result, _ = self._send_command(f'SAY NUMBER {number} "{escape_digits}"')
        return result
    
    def set_context(self, context: str) -> bool:
        """Set call context"""
        result, _ = self._send_command(f'SET CONTEXT {context}')
        return result == 0
    
    def set_extension(self, extension: str) -> bool:
        """Set call extension"""
        result, _ = self._send_command(f'SET EXTENSION {extension}')
        return result == 0
    
    def set_priority(self, priority: int) -> bool:
        """Set call priority"""
        result, _ = self._send_command(f'SET PRIORITY {priority}')
        return result == 0
    
    def verbose(self, message: str, level: int = 1):
        """Log verbose message"""
        self._send_command(f'VERBOSE "{message}" {level}')
    
    def get_channel_info(self) -> Dict[str, str]:
        """Get channel information from AGI environment"""
        return {
            'channel': self.env.get('channel', ''),
            'language': self.env.get('language', ''),
            'type': self.env.get('type', ''),
            'uniqueid': self.env.get('uniqueid', ''),
            'callerid': self.env.get('callerid', ''),
            'calleridname': self.env.get('calleridname', ''),
            'callingpres': self.env.get('callingpres', ''),
            'callington': self.env.get('callington', ''),
            'dnid': self.env.get('dnid', ''),
            'rdnis': self.env.get('rdnis', ''),
            'context': self.env.get('context', ''),
            'extension': self.env.get('extension', ''),
            'priority': self.env.get('priority', ''),
            'enhanced': self.env.get('enhanced', ''),
            'accountcode': self.env.get('accountcode', ''),
        }


class AsteriskAMI:
    """Asterisk Manager Interface for call origination and monitoring"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        secret: str = None
    ):
        """
        Initialize AMI connection
        
        Args:
            host: Asterisk host
            port: AMI port (default 5038)
            username: AMI username
            secret: AMI secret
        """
        self.host = host or settings.asterisk_host
        self.port = port or settings.asterisk_port
        self.username = username or settings.asterisk_username
        self.secret = secret or settings.asterisk_secret
        
        self.socket = None
        self.connected = False
    
    def connect(self):
        """Connect to Asterisk AMI"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            # Read greeting
            greeting = self._read_response()
            logger.info(f"AMI Greeting: {greeting}")
            
            # Login
            self._send_action({
                'Action': 'Login',
                'Username': self.username,
                'Secret': self.secret
            })
            
            response = self._read_response()
            if 'Success' in response:
                self.connected = True
                logger.info("AMI connected successfully")
            else:
                logger.error(f"AMI login failed: {response}")
                
        except Exception as e:
            logger.error(f"Error connecting to AMI: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from AMI"""
        if self.socket:
            self._send_action({'Action': 'Logoff'})
            self.socket.close()
            self.connected = False
            logger.info("AMI disconnected")
    
    def _send_action(self, action: Dict[str, str]):
        """Send action to AMI"""
        message = ""
        for key, value in action.items():
            message += f"{key}: {value}\r\n"
        message += "\r\n"
        
        self.socket.send(message.encode())
        logger.debug(f"AMI Action sent: {action}")
    
    def _read_response(self) -> str:
        """Read response from AMI"""
        response = ""
        while True:
            data = self.socket.recv(1024).decode()
            response += data
            if "\r\n\r\n" in response:
                break
        return response
    
    def originate_call(
        self,
        phone_number: str,
        context: str = None,
        extension: str = None,
        caller_id: str = None,
        variables: Dict[str, str] = None
    ) -> str:
        """
        Originate outbound call
        
        Args:
            phone_number: Number to call
            context: Dialplan context
            extension: Extension to connect to
            caller_id: Caller ID to use
            variables: Channel variables
            
        Returns:
            Action ID
        """
        context = context or settings.asterisk_context
        caller_id = caller_id or settings.asterisk_caller_id
        
        action = {
            'Action': 'Originate',
            'Channel': f'PJSIP/{phone_number}',
            'Context': context,
            'Exten': extension or 's',
            'Priority': '1',
            'CallerID': caller_id,
            'Timeout': '30000',
            'Async': 'true'
        }
        
        # Add variables
        if variables:
            var_string = ','.join([f'{k}={v}' for k, v in variables.items()])
            action['Variable'] = var_string
        
        self._send_action(action)
        response = self._read_response()
        
        logger.info(f"Call originated to {phone_number}: {response}")
        return response
    
    def hangup_call(self, channel: str) -> str:
        """Hangup a call"""
        action = {
            'Action': 'Hangup',
            'Channel': channel
        }
        
        self._send_action(action)
        response = self._read_response()
        
        logger.info(f"Hangup sent for {channel}")
        return response

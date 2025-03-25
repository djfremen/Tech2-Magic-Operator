import os
import time
import binascii
import sys
from contextlib import contextmanager


def hex_dump(data):
    """Convert binary data to a readable hex format"""
    if isinstance(data, bytes) or isinstance(data, bytearray):
        hex_data = binascii.hexlify(data).decode('ascii')
    else:
        hex_data = binascii.hexlify(bytes(data)).decode('ascii')
    return ' '.join([hex_data[i:i+2] for i in range(0, len(hex_data), 2)])


def log(message, debug=False):
    """Print log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    if debug:
        print(f"[{timestamp}][DEBUG] {message}")
    else:
        print(f"[{timestamp}] {message}")


class Tech2Communicator:
    """Class for handling all Tech2 device communication"""
    
    # Command constants
    RESTART_COMMAND = bytearray([0x8B, 0x56, 0x00, 0x1F])
    DOWNLOAD_COMMAND = bytearray([0xEF, 0x56, 0x80, 0x3B])
    
    # Chunk commands with offsets
    CHUNK_COMMANDS = [
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0x00, 0xA6, 0x42]),  # Offset: 0x00
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0xA6, 0xA6, 0x9C]),  # Offset: 0xA6
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x01, 0x4C, 0xA6, 0xF5]),  # Offset: 0x14C
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x01, 0xF2, 0xA6, 0x4F]),  # Offset: 0x1F2
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x02, 0x98, 0x32, 0x1C])   # Offset: 0x298
    ]
    
    # Expected chunk sizes
    CHUNK_SIZES = [169, 169, 169, 169, 53]
    
    def __init__(self, port_name, debug_mode=False):
        """Initialize with port name"""
        self.port_name = port_name
        self.port = None
        self.is_connected = False
        self.debug_mode = debug_mode
        
    def debug(self, message):
        """Log debug message if debug mode is enabled"""
        if self.debug_mode:
            log(message, True)
            
    def connect(self):
        """Open connection to the Tech2 device"""
        try:
            port_path = f"\\\\.\\{self.port_name}" if sys.platform == 'win32' else self.port_name
            log(f"Opening port: {port_path}", self.debug_mode)
            
            # Open port in binary mode
            binary_flag = os.O_BINARY if hasattr(os, 'O_BINARY') else 0
            self.port = os.open(port_path, os.O_RDWR | binary_flag)
            
            if self.port:
                log(f"Port opened with handle: {self.port}", self.debug_mode)
                time.sleep(1)  # Wait for port to stabilize
                self.is_connected = True
                return True
            return False
        except Exception as e:
            log(f"Error opening port: {e}", self.debug_mode)
            return False
    
    def disconnect(self):
        """Close the connection to the Tech2 device"""
        if self.port is not None and self.is_connected:
            try:
                # Send restart command before closing the port
                log("Sending final restart command before disconnecting", self.debug_mode)
                self.send_restart_command()
                
                log("Closing port", self.debug_mode)
                os.close(self.port)
                log("Port closed", self.debug_mode)
                self.is_connected = False
                self.port = None
                return True
            except Exception as e:
                log(f"Error closing port: {e}", self.debug_mode)
        return False
    
    def send_command(self, command, description=""):
        """Send a command to the Tech2 and log it"""
        if not self.is_connected or self.port is None:
            log("Not connected - cannot send command", self.debug_mode)
            return False
            
        log(f"Sending {description}: {hex_dump(command)}", self.debug_mode)
        try:
            bytes_written = os.write(self.port, command)
            self.debug(f"Sent {bytes_written} bytes")
            return bytes_written == len(command)
        except Exception as e:
            log(f"Error sending command: {e}", self.debug_mode)
            return False
    
    def read_response(self, expected_length, timeout=5, description="response"):
        """Read response from device with timeout"""
        if not self.is_connected or self.port is None:
            log("Not connected - cannot read response", self.debug_mode)
            return bytearray()
            
        try:
            log(f"Reading {description}... (expecting {expected_length} bytes)", self.debug_mode)
            response = bytearray()
            start_time = time.time()
            
            while len(response) < expected_length:
                if time.time() - start_time > timeout:
                    self.debug(f"Timeout waiting for {description}, continuing with {len(response)} bytes")
                    break
                
                try:
                    # Read in smaller chunks to avoid blocking
                    read_size = min(32, expected_length - len(response))
                    chunk = os.read(self.port, read_size)
                    
                    if chunk:
                        response.extend(chunk)
                        self.debug(f"Received {len(chunk)} bytes, total: {len(response)}/{expected_length}")
                        # Small pause to prevent flooding the device
                        time.sleep(0.05)
                    else:
                        # No data available, wait a bit
                        time.sleep(0.1)
                except OSError as e:
                    self.debug(f"Error reading from port: {e}")
                    # Try to continue reading despite error
                    time.sleep(0.2)
            
            if response:
                if self.debug_mode:
                    if len(response) <= 32:
                        self.debug(f"Response: {hex_dump(response)}")
                    else:
                        self.debug(f"Response first 32 bytes: {hex_dump(response[:32])}")
                        self.debug(f"... ({len(response) - 32} more bytes)")
            else:
                self.debug("No response received")
                
            return response
            
        except Exception as e:
            log(f"Error reading {description}: {e}", self.debug_mode)
            return bytearray()
    
    def send_restart_command(self):
        """Send restart command to the device"""
        result = self.send_command(self.RESTART_COMMAND, "restart command")
        log("Waiting 2 seconds for device to restart...", self.debug_mode)
        time.sleep(2)  # Wait for device to respond to restart
        return result
    
    def enter_download_mode(self):
        """Enter download mode by sending the download command and waiting"""
        try:
            # Send initial download command
            if not self.send_command(self.DOWNLOAD_COMMAND, "initial download command"):
                return False
                
            log("Waiting 2 seconds as per protocol", self.debug_mode)
            time.sleep(2)
            
            # Send verification download command
            if not self.send_command(self.DOWNLOAD_COMMAND, "verification download command"):
                return False
                
            # Read verification response - expect 4 bytes
            response = self.read_response(4, timeout=3, description="download mode verification")
            
            # Check if response exists and indicates success
            if response and len(response) == 4:
                if response[0] == 0xEF and response[1] == 0x56:
                    log("Download mode entered successfully", self.debug_mode)
                    return True
                else:
                    log(f"Unexpected verification response: {hex_dump(response)}", self.debug_mode)
            
            # Even if verification fails, try to continue
            log("Continuing despite verification issues", self.debug_mode)
            return True
            
        except Exception as e:
            log(f"Error entering download mode: {e}", self.debug_mode)
            return False
    
    def download_chunk(self, chunk_index):
        """Download a specific chunk of data by index (0-4)"""
        if chunk_index < 0 or chunk_index >= len(self.CHUNK_COMMANDS):
            log(f"Invalid chunk index: {chunk_index}", self.debug_mode)
            return bytearray()
        
        cmd = self.CHUNK_COMMANDS[chunk_index]
        expected_size = self.CHUNK_SIZES[chunk_index]
        
        log(f"Downloading chunk {chunk_index} (offset at cmd[4:6]={hex_dump(cmd[4:6])})...", self.debug_mode)
        
        # Send the chunk read command
        if not self.send_command(cmd, f"chunk {chunk_index} read command"):
            log(f"Failed to send read command for chunk {chunk_index}", self.debug_mode)
            return bytearray()
        
        # Try multiple times to read the chunk if necessary
        chunk_data = bytearray()
        max_attempts = 3
        
        for attempt in range(max_attempts):
            time.sleep(0.5)  # Wait for device to prepare data
            chunk_data = self.read_response(expected_size, timeout=5, 
                                          description=f"chunk {chunk_index} data (attempt {attempt+1})")
            
            if chunk_data and len(chunk_data) > 0:
                break
                
            self.debug(f"Attempt {attempt+1}/{max_attempts} failed, retrying...")
        
        if not chunk_data:
            log(f"Failed to read chunk {chunk_index} after {max_attempts} attempts", self.debug_mode)
            return bytearray()
        
        if len(chunk_data) != expected_size:
            log(f"Warning: Expected {expected_size} bytes for chunk {chunk_index}, got {len(chunk_data)}", self.debug_mode)
        
        return chunk_data
    
    def send_security_key(self, key):
        """Send security key to device"""
        # Create key command with the key value
        key_cmd = bytearray([0x8B, 0x56, 0x02, 0x00, (key >> 8) & 0xFF, key & 0xFF])
        
        if not self.send_command(key_cmd, "security key command"):
            return False
        
        # Wait for device to process the key
        time.sleep(0.5)
        
        # Read response to verify key acceptance
        response = self.read_response(4, timeout=5, description="key verification response")
        
        if len(response) != 4:
            log("Failed to receive key verification response", self.debug_mode)
            return False
        
        # Check if key was accepted
        if response[1] != 0x00:
            log(f"Key verification failed with status: 0x{response[1]:02X}", self.debug_mode)
            return False
        
        log("Security key accepted", self.debug_mode)
        return True

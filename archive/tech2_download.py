#!/usr/bin/env python3
"""
Tech2 Magic Operator - A tool for communicating with Tech2 diagnostic scanner via RS232

This script provides functionality to communicate with a Tech2 diagnostic tool
via a serial connection, implementing the necessary protocol for diagnostic services
including security access and data access.
"""

import serial
import time
import sys
import logging
import argparse
from enum import Enum, auto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tech2mm.log')
    ]
)

# Constants
DEFAULT_TIMEOUT = 1.0  # Default timeout for serial operations
DEFAULT_BAUDRATE = 38400  # Default baud rate for Tech2 communication
KEEP_ALIVE_INTERVAL = 2.0  # Interval in seconds for keep-alive messages

# Download mode command
DOWNLOAD_MODE_CMD = bytes([0xEF, 0x56, 0x80, 0x3B])
RESTART_CMD = bytes([0x8B, 0x56, 0x00, 0x1F])

class DiagnosticState(Enum):
    """Enumeration for the state of the diagnostic session"""
    DISCONNECTED = auto()
    CONNECTED = auto()
    SESSION_STARTED = auto()
    SECURITY_REQUESTED = auto()
    SECURITY_GRANTED = auto()


class SecurityLevel(Enum):
    """Security access levels supported by Tech2"""
    LEVEL_01 = 0x01  # Basic level
    LEVEL_FB = 0xFB  # Intermediate level
    LEVEL_FD = 0xFD  # Highest level


class Tech2Communicator:
    """Main class for Tech2 communication via serial port"""
    
    def __init__(self, port=None, baudrate=DEFAULT_BAUDRATE, debug=False):
        """Initialize the Tech2 communicator
        
        Args:
            port (str): Serial port to use (e.g., 'COM1', '/dev/ttyUSB0')
            baudrate (int): Baud rate for serial communication
            debug (bool): Enable debug mode for verbose logging
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.state = DiagnosticState.DISCONNECTED
        self.last_activity_time = 0
        self.debug = debug
        
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
    
    def connect(self):
        """Connect to the Tech2 device via serial port
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.port is None:
            logging.error("No serial port specified")
            return False
            
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Close any existing connection
                if self.ser and self.ser.is_open:
                    self.ser.close()
                    time.sleep(1)  # Wait for port to fully close
                
                # Try to open the port with a different method
                self.ser = serial.Serial()
                self.ser.port = self.port
                self.ser.baudrate = self.baudrate
                self.ser.bytesize = serial.EIGHTBITS
                self.ser.parity = serial.PARITY_NONE
                self.ser.stopbits = serial.STOPBITS_ONE
                self.ser.timeout = DEFAULT_TIMEOUT
                
                # Try to open with a small delay
                time.sleep(0.5)
                self.ser.open()
                    
                self.state = DiagnosticState.CONNECTED
                self.last_activity_time = time.time()
                logging.info(f"Connected to Tech2 on {self.port} at {self.baudrate} baud")
                return True
                
            except serial.SerialException as e:
                logging.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logging.error(f"Failed to connect to serial port {self.port} after {max_retries} attempts")
                    return False
    
    def disconnect(self):
        """Disconnect from the Tech2 device"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.state = DiagnosticState.DISCONNECTED
            logging.info("Disconnected from Tech2")
    
    def start_diagnostic_session(self):
        """Start a diagnostic session with the Tech2
        
        Returns:
            bool: True if session started successfully, False otherwise
        """
        if self.state == DiagnosticState.DISCONNECTED:
            logging.error("Cannot start session: Not connected to Tech2")
            return False
            
        # Send start diagnostic session command (Service 0x10)
        # Mode 0x10 = Diagnostic Session Control, subfunction 0x02 = Enhanced Diagnostics
        command = bytes([
            0x06,        # Frame length
            0x7E, 0x00,  # Target ID (0x7E0 - ECU address)
            0x02,        # Data length
            0x10,        # Service ID: Start Diagnostic Session
            0x02         # Session type: Enhanced diagnostics
        ])
        
        response = self.send_and_receive(command)
        
        if response and len(response) >= 5 and response[4] == 0x50:
            self.state = DiagnosticState.SESSION_STARTED
            logging.info("Diagnostic session started successfully")
            return True
        else:
            logging.error("Failed to start diagnostic session")
            if response:
                self.log_response_debug(response)
            return False
    
    def request_security_access(self, level=SecurityLevel.LEVEL_FD):
        """Request security access from the Tech2
        
        Args:
            level (SecurityLevel): Security access level
            
        Returns:
            bool: True if security access granted, False otherwise
            
        Raises:
            RuntimeError: If not in an active diagnostic session
        """
        if self.state < DiagnosticState.SESSION_STARTED:
            raise RuntimeError("No active diagnostic session")
            
        # Send security access request
        access_level = level.value if isinstance(level, SecurityLevel) else level
        
        command = self.format_security_access_request(access_level)
        logging.debug(f"Sending security access request for level 0x{access_level:02X}")
        self.log_command_debug(command)
        
        response = self.send_and_receive(command)
        if not response or len(response) < 7:
            logging.error("Invalid or no response to security access request")
            if response:
                self.log_response_debug(response)
            return False
            
        # Check response type
        if response[4] == 0x67 and response[5] == access_level:
            # Extract seed
            seed = (response[6] << 8) | response[7]
            
            # If seed is 0, security access is already granted
            if seed == 0:
                logging.info("Security access already granted")
                self.state = DiagnosticState.SECURITY_GRANTED
                return True
                
            logging.info(f"Received seed: 0x{seed:04X}")
            self.state = DiagnosticState.SECURITY_REQUESTED
            
            # Calculate key
            key = self.calculate_key(seed, access_level)
            logging.info(f"Calculated key: 0x{key:04X}")
            
            # Small delay before sending the key (as seen in the original code)
            time.sleep(0.1)
            
            # Send the key
            key_command = self.format_key_response(key, access_level)
            self.log_command_debug(key_command)
            
            key_response = self.send_and_receive(key_command)
            if not key_response:
                logging.error("No response to key submission")
                return False
                
            # Check if key was accepted
            if key_response[4] == 0x67 and key_response[5] == (access_level + 1):
                logging.info("Security access granted")
                self.state = DiagnosticState.SECURITY_GRANTED
                return True
            elif key_response[4] == 0x7F and key_response[5] == 0x27:
                error = self.translate_error_code(key_response[6])
                logging.error(f"Security access denied: {error}")
                return False
            else:
                logging.error("Unexpected response to key submission")
                self.log_response_debug(key_response)
                return False
        elif response[4] == 0x7F and response[5] == 0x27:
            error = self.translate_error_code(response[6])
            logging.error(f"Security access request rejected: {error}")
            return False
        else:
            logging.error("Unexpected response format")
            self.log_response_debug(response)
            return False
    
    def calculate_key(self, seed, level):
        """Calculate the key from the seed for security access
        
        This implements the Trionic 8 security access algorithm
        
        Args:
            seed (int): The seed value from the ECU (16-bit)
            level (int): The security access level (0x01, 0xFB, or 0xFD)
            
        Returns:
            int: The calculated key (16-bit)
        """
        # Base transformation
        key = ((seed >> 5) | (seed << 11)) & 0xFFFF
        key = (key + 0xB988) & 0xFFFF
        
        # Level-specific transformations
        if level == 0xFD:  # Highest access level
            key = (key // 3) & 0xFFFF
            key ^= 0x8749
            key = (key + 0x0ACF) & 0xFFFF
            key ^= 0x81BF
        elif level == 0xFB:  # Intermediate access level
            key ^= 0x8749
            key = (key + 0x06D3) & 0xFFFF
            key ^= 0xCFDF
        # Level 0x01 doesn't need additional transformations in the Trionic code
        
        return key
    
    def format_security_access_request(self, level):
        """Format a security access request message
        
        Args:
            level (int): Security access level (0x01, 0xFB, or 0xFD)
            
        Returns:
            bytes: Formatted message
        """
        return bytes([
            0x07,        # Frame length
            0x7E, 0x00,  # Target ID (0x7E0 - ECU address)
            0x03,        # Data length
            0x27,        # Service ID: Security Access
            level,       # Access level
            0x00         # Padding
        ])
    
    def format_key_response(self, key, level):
        """Format a key response message
        
        Args:
            key (int): The calculated key value
            level (int): Security access level
            
        Returns:
            bytes: Formatted message
        """
        return bytes([
            0x09,              # Frame length
            0x7E, 0x00,        # Target ID (0x7E0 - ECU address)
            0x05,              # Data length
            0x27,              # Service ID: Security Access
            level + 1,         # Response type (level + 1)
            (key >> 8) & 0xFF, # Key high byte
            key & 0xFF,        # Key low byte
            0x00               # Padding
        ])
    
    def translate_error_code(self, code):
        """Translate a diagnostic error code to a human-readable message
        
        Args:
            code (int): Error code byte
            
        Returns:
            str: Human-readable error message
        """
        error_codes = {
            0x10: "General reject",
            0x11: "Service not supported",
            0x12: "Sub-function not supported - invalid format",
            0x21: "Busy, repeat request",
            0x22: "Conditions not correct or request sequence error",
            0x23: "Routine not completed or service in progress",
            0x31: "Request out of range or session dropped",
            0x33: "Security access denied",
            0x35: "Invalid key supplied",
            0x36: "Exceeded number of attempts to get security access",
            0x37: "Required time delay not expired",
            0x78: "Response pending",
            0x7F: "General error"
        }
        
        return error_codes.get(code, f"Unknown error code: 0x{code:02X}")
    
    def send_keep_alive(self):
        """Send a keep-alive message (TesterPresent) to maintain the diagnostic session
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Only send if we're in an active session
        if self.state < DiagnosticState.SESSION_STARTED:
            return False
            
        command = bytes([
            0x06,        # Frame length
            0x7E, 0x00,  # Target ID (0x7E0 - ECU address)
            0x02,        # Data length
            0x3E,        # Service ID: Tester Present
            0x00         # Default mode
        ])
        
        response = self.send_and_receive(command, expect_response=False)
        self.last_activity_time = time.time()
        
        if response and len(response) >= 5 and response[4] == 0x7E:
            return True
        return False
    
    def maintain_session(self):
        """Check if a keep-alive message is needed and send it if necessary"""
        current_time = time.time()
        if (self.state >= DiagnosticState.SESSION_STARTED and 
            (current_time - self.last_activity_time) > KEEP_ALIVE_INTERVAL):
            self.send_keep_alive()
    
    def read_vin(self):
        """Read the Vehicle Identification Number (VIN)
        
        Returns:
            str: The VIN if successful, None otherwise
        """
        if self.state < DiagnosticState.SECURITY_GRANTED:
            logging.warning("Security access required to read VIN")
            return None
            
        # Send ReadDataByIdentifier for VIN (ID 0x90)
        command = bytes([
            0x07,        # Frame length
            0x7E, 0x00,  # Target ID (0x7E0 - ECU address)
            0x03,        # Data length
            0x22,        # Service ID: ReadDataByIdentifier
            0x00, 0x90   # Data Identifier for VIN
        ])
        
        response = self.send_and_receive(command)
        
        if not response or len(response) < 6:
            logging.error("Failed to read VIN - invalid response")
            if response:
                self.log_response_debug(response)
            return None
            
        # Check response format
        if response[4] == 0x62 and response[5] == 0x90:
            # Extract VIN characters (typically 17 characters)
            try:
                vin_bytes = response[6:23]
                vin = ''.join(chr(b) for b in vin_bytes if b >= 32 and b <= 126)
                if len(vin) == 17:
                    logging.info(f"Read VIN: {vin}")
                    return vin
                else:
                    logging.warning(f"VIN length incorrect: {len(vin)} chars")
                    return None
            except Exception as e:
                logging.error(f"Error parsing VIN: {str(e)}")
                return None
        elif response[4] == 0x7F and response[5] == 0x22:
            error = self.translate_error_code(response[6])
            logging.error(f"Failed to read VIN: {error}")
            return None
        else:
            logging.error("Unexpected response format for VIN read")
            self.log_response_debug(response)
            return None
    
    def read_data_by_identifier(self, identifier):
        """Read data using the ReadDataByIdentifier service
        
        Args:
            identifier (int): Data identifier (e.g., 0x90 for VIN)
            
        Returns:
            bytes: Data if successful, None otherwise
        """
        if self.state < DiagnosticState.SECURITY_GRANTED:
            logging.warning("Security access required to read data")
            return None
            
        command = bytes([
            0x07,                    # Frame length
            0x7E, 0x00,             # Target ID (0x7E0 - ECU address)
            0x03,                    # Data length
            0x22,                    # Service ID: ReadDataByIdentifier
            (identifier >> 8) & 0xFF,# Identifier high byte
            identifier & 0xFF        # Identifier low byte
        ])
        
        response = self.send_and_receive(command)
        
        if not response or len(response) < 6:
            logging.error(f"Failed to read identifier 0x{identifier:04X} - invalid response")
            if response:
                self.log_response_debug(response)
            return None
            
        # Check response format
        if response[4] == 0x62 and response[5] == (identifier >> 8) & 0xFF and response[6] == identifier & 0xFF:
            # Return the data (skip service ID and identifier)
            data = response[7:]
            logging.info(f"Successfully read identifier 0x{identifier:04X}")
            return data
        elif response[4] == 0x7F and response[5] == 0x22:
            error = self.translate_error_code(response[6])
            logging.error(f"Failed to read identifier 0x{identifier:04X}: {error}")
            return None
        else:
            logging.error(f"Unexpected response format for identifier 0x{identifier:04X}")
            self.log_response_debug(response)
            return None
    
    def write_data_by_identifier(self, identifier, data):
        """Write data using the WriteDataByIdentifier service
        
        Args:
            identifier (int): Data identifier (e.g., 0x01 for manufacturing data)
            data (bytes): Data to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.state < DiagnosticState.SECURITY_GRANTED:
            logging.warning("Security access required to write data")
            return False
            
        # Calculate total length (service ID + identifier + data)
        data_length = 3 + len(data)
        
        # Create command with appropriate length
        command = bytearray([
            data_length + 4,          # Frame length
            0x7E, 0x00,               # Target ID (0x7E0 - ECU address)
            data_length,              # Data length
            0x2E,                     # Service ID: WriteDataByIdentifier
            (identifier >> 8) & 0xFF, # Identifier high byte
            identifier & 0xFF         # Identifier low byte
        ])
        
        # Add the data to write
        command.extend(data)
        
        response = self.send_and_receive(bytes(command))
        
        if not response or len(response) < 6:
            logging.error(f"Failed to write identifier 0x{identifier:04X} - invalid response")
            if response:
                self.log_response_debug(response)
            return False
            
        # Check response format
        if response[4] == 0x6E and response[5] == (identifier >> 8) & 0xFF and response[6] == identifier & 0xFF:
            logging.info(f"Successfully wrote data to identifier 0x{identifier:04X}")
            return True
        elif response[4] == 0x7F and response[5] == 0x2E:
            error = self.translate_error_code(response[6])
            logging.error(f"Failed to write identifier 0x{identifier:04X}: {error}")
            return False
        else:
            logging.error(f"Unexpected response format for write to identifier 0x{identifier:04X}")
            self.log_response_debug(response)
            return False
    
    def execute_routine(self, routine_id, params=None):
        """Execute a routine using the RoutineControl service
        
        Args:
            routine_id (int): Routine identifier
            params (bytes, optional): Optional parameters for routine
            
        Returns:
            bytes: Routine results if successful, None otherwise
        """
        if self.state < DiagnosticState.SECURITY_GRANTED:
            logging.warning("Security access required to execute routine")
            return None
            
        # If no parameters provided, use empty bytes
        if params is None:
            params = b''
            
        # Calculate total length (service ID + subfunction + routine ID + params)
        data_length = 4 + len(params)
        
        # Create command with appropriate length
        command = bytearray([
            data_length + 4,          # Frame length
            0x7E, 0x00,               # Target ID (0x7E0 - ECU address)
            data_length,              # Data length
            0x31,                     # Service ID: RoutineControl
            0x01,                     # Subfunction: startRoutine
            (routine_id >> 8) & 0xFF, # Routine ID high byte
            routine_id & 0xFF         # Routine ID low byte
        ])
        
        # Add the parameters
        command.extend(params)
        
        response = self.send_and_receive(bytes(command))
        
        if not response or len(response) < 7:
            logging.error(f"Failed to execute routine 0x{routine_id:04X} - invalid response")
            if response:
                self.log_response_debug(response)
            return None
            
        # Check response format
        if response[4] == 0x71 and response[5] == 0x01:
            # Return the results (skip service ID, subfunction, and routine ID)
            results = response[8:]
            logging.info(f"Successfully executed routine 0x{routine_id:04X}")
            return results
        elif response[4] == 0x7F and response[5] == 0x31:
            error = self.translate_error_code(response[6])
            logging.error(f"Failed to execute routine 0x{routine_id:04X}: {error}")
            return None
        else:
            logging.error(f"Unexpected response format for routine 0x{routine_id:04X}")
            self.log_response_debug(response)
            return None
    
    def ecu_reset(self, reset_type=0x01):
        """Reset the ECU using the ECUReset service
        
        Args:
            reset_type (int): Reset type (0x01=hard, 0x02=key off/on, 0x03=soft, 0x04=enable rapid power shutdown, 0x05=disable rapid power shutdown)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Send ECUReset command
        command = bytes([
            0x07,        # Frame length
            0x7E, 0x00,  # Target ID (0x7E0 - ECU address)
            0x03,        # Data length
            0x11,        # Service ID: ECUReset
            reset_type,  # Reset type
            0x00         # Padding
        ])
        
        response = self.send_and_receive(command)
        
        if not response or len(response) < 5:
            logging.error("Failed to reset ECU - invalid response")
            if response:
                self.log_response_debug(response)
            return False
            
        # Check response format
        if response[4] == 0x51 and response[5] == reset_type:
            logging.info(f"ECU reset command accepted (type 0x{reset_type:02X})")
            return True
        elif response[4] == 0x7F and response[5] == 0x11:
            error = self.translate_error_code(response[6])
            logging.error(f"Failed to reset ECU: {error}")
            return False
        else:
            logging.error("Unexpected response format for ECU reset")
            self.log_response_debug(response)
            return False
            
    def send_raw_command(self, command_bytes):
        """Send a raw command to the ECU
        
        Args:
            command_bytes (bytes): Raw command bytes to send
            
        Returns:
            bytes: Response if any, None on error
        """
        if not self.ser or not self.ser.is_open:
            logging.error("Serial port not open")
            return None
            
        try:
            # Log command
            self.log_command_debug(command_bytes)
            
            # Send command
            self.ser.write(command_bytes)
            self.last_activity_time = time.time()
            
            # Wait for response
            response = bytearray()
            start_time = time.time()
            
            while (time.time() - start_time) < DEFAULT_TIMEOUT:
                if self.ser.in_waiting:
                    chunk = self.ser.read(self.ser.in_waiting)
                    if chunk:
                        response.extend(chunk)
                        
                    # If we have at least 1 byte, check if it's a complete frame
                    if len(response) >= 1:
                        expected_length = response[0]
                        if len(response) >= expected_length:
                            self.log_response_debug(bytes(response))
                            return bytes(response)
                
                # Small sleep to prevent CPU hogging
                time.sleep(0.01)
                
            # Timeout occurred
            logging.warning("Timeout waiting for response to raw command")
            return None
                
        except Exception as e:
            logging.error(f"Error sending raw command: {str(e)}")
            return None
    
    def send_and_receive(self, command, timeout=DEFAULT_TIMEOUT, retries=3, expect_response=True):
        """Send a command and receive the response
        
        Args:
            command (bytes): Command to send
            timeout (float): Timeout in seconds
            retries (int): Number of retries if no response
            expect_response (bool): Whether to expect a response
            
        Returns:
            bytes: Response data if successful, None otherwise
        """
        if not self.ser or not self.ser.is_open:
            logging.error("Serial port not open")
            return None
            
        for attempt in range(retries):
            try:
                # Clear any pending data
                self.ser.reset_input_buffer()
                
                # Send the command
                self.ser.write(command)
                self.last_activity_time = time.time()
                
                if not expect_response:
                    return None
                    
                # Wait for response
                response = bytearray()
                start_time = time.time()
                
                while (time.time() - start_time) < timeout:
                    if self.ser.in_waiting:
                        chunk = self.ser.read(self.ser.in_waiting)
                        if chunk:
                            response.extend(chunk)
                            
                        # If we have at least 1 byte, check if it's a complete frame
                        if len(response) >= 1:
                            expected_length = response[0]
                            if len(response) >= expected_length:
                                return bytes(response)
                    
                    # Small sleep to prevent CPU hogging
                    time.sleep(0.01)
                
                # Timeout occurred
                if attempt < retries - 1:
                    logging.warning(f"Response timeout, retrying ({attempt+1}/{retries})")
                else:
                    logging.error("Failed to receive response after multiple attempts")
                    return None
                    
            except Exception as e:
                logging.error(f"Communication error: {str(e)}")
                if attempt >= retries - 1:
                    return None
        
        return None
    
    def log_command_debug(self, command):
        """Log a command in a debug-friendly format
        
        Args:
            command (bytes): Command data
        """
        if self.debug:
            hex_str = ' '.join([f"{b:02X}" for b in command])
            logging.debug(f"TX: {hex_str}")
    
    def log_response_debug(self, response):
        """Log a response in a debug-friendly format
        
        Args:
            response (bytes): Response data
        """
        if self.debug:
            hex_str = ' '.join([f"{b:02X}" for b in response])
            logging.debug(f"RX: {hex_str}")


def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(description='Tech2 Magic Monitor - Tech2 Diagnostic Tool')
    parser.add_argument('-p', '--port', required=True, help='Serial port to use')
    parser.add_argument('-b', '--baudrate', type=int, default=DEFAULT_BAUDRATE,
                        help=f'Baud rate (default: {DEFAULT_BAUDRATE})')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    
    # Command options
    cmd_group = parser.add_argument_group('Commands')
    cmd_group.add_argument('--vin', action='store_true', help='Read Vehicle Identification Number')
    cmd_group.add_argument('--read-id', type=lambda x: int(x, 0), help='Read data by identifier (hex, e.g., 0x90)')
    cmd_group.add_argument('--write-id', type=lambda x: int(x, 0), help='Write data by identifier (hex, e.g., 0x01)')
    cmd_group.add_argument('--write-data', type=str, help='Data to write in hex format (e.g., "01 02 03")')
    cmd_group.add_argument('--routine', type=lambda x: int(x, 0), help='Execute routine by ID (hex, e.g., 0x0203)')
    cmd_group.add_argument('--routine-params', type=str, help='Routine parameters in hex format (e.g., "01 02 03")')
    cmd_group.add_argument('--reset', type=lambda x: int(x, 0), choices=[1, 2, 3, 4, 5], 
                           help='Reset ECU (1=hard, 2=key off/on, 3=soft, 4=enable rapid power shutdown, 5=disable rapid power shutdown)')
    cmd_group.add_argument('--raw-cmd', type=str, help='Send raw command in hex format (e.g., "07 E0 00 03 27 FD 00")')
    cmd_group.add_argument('--interactive', action='store_true', help='Start interactive mode')
    
    # Security access options
    sec_group = parser.add_argument_group('Security Access')
    sec_group.add_argument('--level', type=str, choices=['01', 'FB', 'FD'], default='FD',
                           help='Security access level (01, FB, or FD)')
    
    args = parser.parse_args()
    
    # Create Tech2 communicator
    tech2 = Tech2Communicator(port=args.port, baudrate=args.baudrate, debug=args.debug)
    
    try:
        # Connect to Tech2
        if not tech2.connect():
            sys.exit(1)
            
        # Start diagnostic session
        if not tech2.start_diagnostic_session():
            logging.error("Failed to start diagnostic session")
            sys.exit(1)
            
        # Request security access with specified level
        level = None
        if args.level == '01':
            level = SecurityLevel.LEVEL_01
        elif args.level == 'FB':
            level = SecurityLevel.LEVEL_FB
        else:
            level = SecurityLevel.LEVEL_FD
            
        if not tech2.request_security_access(level):
            logging.error("Failed to get security access")
            sys.exit(1)
        
        # Process commands based on arguments
        if args.vin:
            vin = tech2.read_vin()
            if vin:
                print(f"Vehicle Identification Number: {vin}")
            else:
                logging.error("Failed to read VIN")
                
        if args.read_id is not None:
            data = tech2.read_data_by_identifier(args.read_id)
            if data:
                print(f"Data for identifier 0x{args.read_id:04X}:")
                hex_str = ' '.join([f"{b:02X}" for b in data])
                ascii_str = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
                print(f"HEX: {hex_str}")
                print(f"ASCII: {ascii_str}")
            else:
                logging.error(f"Failed to read identifier 0x{args.read_id:04X}")
                
        if args.write_id is not None and args.write_data is not None:
            try:
                # Convert hex string to bytes
                write_data = bytes.fromhex(args.write_data.replace(' ', ''))
                
                if tech2.write_data_by_identifier(args.write_id, write_data):
                    print(f"Successfully wrote data to identifier 0x{args.write_id:04X}")
                else:
                    logging.error(f"Failed to write data to identifier 0x{args.write_id:04X}")
            except ValueError:
                logging.error("Invalid hex format for write data")
                
        if args.routine is not None:
            routine_params = None
            if args.routine_params:
                try:
                    # Convert hex string to bytes
                    routine_params = bytes.fromhex(args.routine_params.replace(' ', ''))
                except ValueError:
                    logging.error("Invalid hex format for routine parameters")
                    sys.exit(1)
                    
            results = tech2.execute_routine(args.routine, routine_params)
            if results is not None:
                print(f"Routine 0x{args.routine:04X} executed successfully")
                if results:
                    hex_str = ' '.join([f"{b:02X}" for b in results])
                    print(f"Results: {hex_str}")
            else:
                logging.error(f"Failed to execute routine 0x{args.routine:04X}")
                
        if args.reset is not None:
            if tech2.ecu_reset(args.reset):
                print(f"ECU reset command (type {args.reset}) accepted")
            else:
                logging.error("Failed to reset ECU")
                
        if args.raw_cmd is not None:
            try:
                # Convert hex string to bytes
                cmd_bytes = bytes.fromhex(args.raw_cmd.replace(' ', ''))
                
                response = tech2.send_raw_command(cmd_bytes)
                if response:
                    print("Command sent successfully")
                    hex_str = ' '.join([f"{b:02X}" for b in response])
                    print(f"Response: {hex_str}")
                else:
                    logging.error("No response received for raw command")
            except ValueError:
                logging.error("Invalid hex format for raw command")
                
        if args.interactive:
            run_interactive_mode(tech2)
                
    except KeyboardInterrupt:
        logging.info("Operation interrupted by user")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
    finally:
        # Disconnect from Tech2
        tech2.disconnect()


def run_interactive_mode(tech2):
    """Run interactive command mode
    
    Args:
        tech2 (Tech2Communicator): Tech2 communicator instance
    """
    print("\nTech2 Interactive Mode")
    print("----------------------")
    print("Available commands:")
    print("  quit, exit - Exit interactive mode")
    print("  help - Show this help message")
    print("  vin - Read VIN")
    print("  read <id> - Read data by identifier (hex, e.g., 0x90)")
    print("  write <id> <data> - Write data by identifier (hex, e.g., 0x01 01 02 03)")
    print("  routine <id> [params] - Execute routine (hex, e.g., 0x0203 01 02 03)")
    print("  reset <type> - Reset ECU (1=hard, 2=key off/on, 3=soft)")
    print("  raw <cmd> - Send raw command (hex, e.g., 07 E0 00 03 27 FD 00)")
    print("  keepalive - Send manual keep-alive")
    print("----------------------")
    
    while True:
        try:
            # Maintain session with keep-alive
            tech2.maintain_session()
            
            # Get user input
            cmd = input("\n> ").strip()
            
            if cmd in ['quit', 'exit', 'q']:
                print("Exiting interactive mode")
                break
                
            if cmd in ['help', '?', 'h']:
                print("Available commands:")
                print("  quit, exit - Exit interactive mode")
                print("  help - Show this help message")
                print("  vin - Read VIN")
                print("  read <id> - Read data by identifier (hex, e.g., 0x90)")
                print("  write <id> <data> - Write data by identifier (hex, e.g., 0x01 01 02 03)")
                print("  routine <id> [params] - Execute routine (hex, e.g., 0x0203 01 02 03)")
                print("  reset <type> - Reset ECU (1=hard, 2=key off/on, 3=soft)")
                print("  raw <cmd> - Send raw command (hex, e.g., 07 E0 00 03 27 FD 00)")
                print("  keepalive - Send manual keep-alive")
                continue
                
            if cmd == 'vin':
                vin = tech2.read_vin()
                if vin:
                    print(f"Vehicle Identification Number: {vin}")
                else:
                    print("Failed to read VIN")
                continue
                
            if cmd == 'keepalive':
                if tech2.send_keep_alive():
                    print("Keep-alive sent successfully")
                else:
                    print("Failed to send keep-alive")
                continue
                
            if cmd.startswith('read '):
                try:
                    # Parse identifier
                    id_str = cmd[5:].strip()
                    identifier = int(id_str, 0)  # Auto-detect base (0x for hex, 0 for octal, otherwise decimal)
                    
                    data = tech2.read_data_by_identifier(identifier)
                    if data:
                        print(f"Data for identifier 0x{identifier:04X}:")
                        hex_str = ' '.join([f"{b:02X}" for b in data])
                        ascii_str = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
                        print(f"HEX: {hex_str}")
                        print(f"ASCII: {ascii_str}")
                    else:
                        print(f"Failed to read identifier 0x{identifier:04X}")
                except ValueError:
                    print("Invalid identifier format. Use decimal (123) or hex (0x7B)")
                continue
                
            if cmd.startswith('write '):
                try:
                    # Parse command parts
                    parts = cmd[6:].strip().split(' ', 1)
                    if len(parts) != 2:
                        print("Invalid write command format. Use: write <id> <data>")
                        continue
                        
                    identifier = int(parts[0], 0)  # Auto-detect base
                    data_hex = parts[1].strip()
                    
                    # Convert hex string to bytes
                    write_data = bytes.fromhex(data_hex.replace(' ', ''))
                    
                    if tech2.write_data_by_identifier(identifier, write_data):
                        print(f"Successfully wrote data to identifier 0x{identifier:04X}")
                    else:
                        print(f"Failed to write data to identifier 0x{identifier:04X}")
                except ValueError as e:
                    print(f"Invalid format: {str(e)}")
                continue
                
            if cmd.startswith('routine '):
                try:
                    # Parse command parts
                    parts = cmd[8:].strip().split(' ', 1)
                    
                    routine_id = int(parts[0], 0)  # Auto-detect base
                    routine_params = None
                    
                    if len(parts) > 1:
                        # Convert hex string to bytes
                        routine_params = bytes.fromhex(parts[1].replace(' ', ''))
                        
                    results = tech2.execute_routine(routine_id, routine_params)
                    if results is not None:
                        print(f"Routine 0x{routine_id:04X} executed successfully")
                        if results:
                            hex_str = ' '.join([f"{b:02X}" for b in results])
                            print(f"Results: {hex_str}")
                    else:
                        print(f"Failed to execute routine 0x{routine_id:04X}")
                except ValueError as e:
                    print(f"Invalid format: {str(e)}")
                continue
                
            if cmd.startswith('reset '):
                try:
                    # Parse reset type
                    reset_type = int(cmd[6:].strip(), 0)  # Auto-detect base
                    
                    if reset_type < 1 or reset_type > 5:
                        print("Invalid reset type. Use 1=hard, 2=key off/on, 3=soft, 4=enable rapid power shutdown, 5=disable rapid power shutdown")
                        continue
                        
                    if tech2.ecu_reset(reset_type):
                        print(f"ECU reset command (type {reset_type}) accepted")
                    else:
                        print("Failed to reset ECU")
                except ValueError:
                    print("Invalid reset type format. Use decimal (1) or hex (0x01)")
                continue
                
            if cmd.startswith('raw '):
                try:
                    # Convert hex string to bytes
                    cmd_hex = cmd[4:].strip()
                    cmd_bytes = bytes.fromhex(cmd_hex.replace(' ', ''))
                    
                    response = tech2.send_raw_command(cmd_bytes)
                    if response:
                        print("Command sent successfully")
                        hex_str = ' '.join([f"{b:02X}" for b in response])
                        print(f"Response: {hex_str}")
                    else:
                        print("No response received for raw command")
                except ValueError:
                    print("Invalid hex format for raw command")
                continue
                
            # Unknown command
            print(f"Unknown command: {cmd}")
            print("Type 'help' for a list of available commands")
            
        except KeyboardInterrupt:
            print("\nExiting interactive mode")
            break
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()

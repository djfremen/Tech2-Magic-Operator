# Tech2 Communication Documentation

## Overview
This document outlines the complete workflow for communicating with a Saab Tech2 device, including the process for extracting the security seed and VIN number.

## Hardware Requirements
- Saab Tech2 device
- USB-to-Serial adapter (typically shows up as COM4 or COM5 on Windows)
- USB cable

## Software Requirements
- Python 3.x
- Required Python modules:
  - os
  - time
  - binascii
  - sys

## Connection Parameters
- Baud rate: Default (9600)
- Data bits: 8
- Stop bits: 1
- Parity: None
- Flow control: None

## Command Sequence

### 1. Initial Connection
1. Connect the Tech2 device to the computer via USB
2. Identify the correct COM port (typically COM4 or COM5)
3. Open the port with binary mode enabled

### 2. Initial Restart Command
```
Command: 8B 56 00 1F
Length: 4 bytes
Purpose: Initialize device communication
Wait time: 2 seconds after sending
```

### 3. Enter Download Mode
```
Command: EF 56 80 3B
Length: 4 bytes
Purpose: Request download mode
Wait time: 2 seconds after sending
```

### 4. Download Mode Verification
```
Command: EF 56 80 3B
Length: 4 bytes
Purpose: Verify download mode entry
Expected Response: EF 56 01 BA
```

### 5. Data Chunk Reading
Five chunks of data are read in sequence:

#### Chunk 1
```
Command: 81 5A 0F 2E 00 00 A6 42
Expected Size: 169 bytes
Offset: 0x00
```

#### Chunk 2
```
Command: 81 5A 0F 2E 00 A6 A6 9C
Expected Size: 169 bytes
Offset: 0xA6
```

#### Chunk 3
```
Command: 81 5A 0F 2E 01 4C A6 F5
Expected Size: 169 bytes
Offset: 0x14C
```

#### Chunk 4
```
Command: 81 5A 0F 2E 01 F2 A6 4F
Expected Size: 169 bytes
Offset: 0x1F2
```

#### Chunk 5
```
Command: 81 5A 0F 2E 02 98 32 1C
Expected Size: 53 bytes
Offset: 0x298
```

### 6. Final Restart Command
```
Command: 8B 56 00 1F
Length: 4 bytes
Purpose: Return device to logo screen
```

## Data Structure

### VIN Location
- Offset: 0x14 (20 decimal)
- Length: 17 bytes
- Format: ASCII string
- Example: YS3FD49YX41012017

### Seed Location
- Offset: 0x30 (48 decimal)
- Length: 2 bytes
- Format: Big-endian 16-bit integer
- Example: 0xFFFF

## Quick Mode
For seed-only extraction, use the `-d` flag:
```
python tech2_workflow_revised.py -p COM3 -d
```
This will only read the first chunk of data, which contains the seed value.

## Common Issues and Solutions

1. **Device Not Responding**
   - Verify correct COM port
   - Check USB connection
   - Ensure device is powered on

2. **Incomplete Data Reception**
   - Wait time between chunks: 0.5 seconds
   - Maximum retries per chunk: 3
   - Verify chunk sizes match expected values

3. **Download Mode Entry Failure**
   - Verify correct command sequence
   - Ensure 2-second wait after initial command
   - Check verification response

## Security Information
- Seed: 0xFFFF
- Calculated Key: 0xB987
- Key Calculation: Using Trionic8 calculator algorithm

## Notes
- Total data size: 719 bytes
- Each chunk includes a 2-byte header
- Device requires stabilization time between commands
- Always close port properly after use

## Python Files Overview

### Core Files
1. `tech2_workflow_revised.py`
   - Main script for Tech2 communication
   - Handles command-line arguments
   - Orchestrates the entire process
   - Usage: `python tech2_workflow_revised.py -p COM3 [-d]`

2. `tech2_communication_revised.py`
   - Core serial communication module
   - Implements the Tech2Communicator class
   - Handles port operations and device communication

3. `process_bin_revised.py`
   - Binary data processing utilities
   - Extracts and validates VIN and seed from binary data

4. `trionic8_calculator.py`
   - Implements the Trionic8 key calculation algorithm
   - Takes seed as input and returns calculated key
   - Includes step-by-step calculation for debugging

### Important Note on COM Port
The COM port parameter (-p) specifies which serial port your Tech2 device is connected to. The typical usage would be:
```
python tech2_workflow_revised.py -p COM3 -d
```
Where COM3 is the port where your Tech2 device is connected. The port may vary (COM3, COM4, COM5, etc.) depending on your system.

### Command-line Usage
1. Full data extraction:
```bash
python tech2_workflow_revised.py -p COM3
```

2. With debug output:
```bash
python tech2_workflow_revised.py -p COM3 -d
```

3. Save downloaded data to file:
```bash
python tech2_workflow_revised.py -p COM3 -o tech2_data.bin
```

### Key Classes and Functions

#### In tech2_communication_revised.py:
```python
class Tech2Communicator:
    """Class for handling all Tech2 device communication"""
    
    def connect(self):
        """Open connection to the Tech2 device"""
        
    def disconnect(self):
        """Close the connection to the Tech2 device"""
        
    def enter_download_mode(self):
        """Enter download mode by sending the download command and waiting"""
        
    def download_chunk(self, chunk_index):
        """Download a specific chunk of data by index (0-4)"""
        
    def send_security_key(self, key):
        """Send security key to device"""
```

#### In process_bin_revised.py:
```python
def extract_data_from_binary(data, data_type='all'):
    """Extract specified information from binary data"""
    
def validate_vin(vin):
    """Validate VIN using standard VIN validation rules"""
    
def analyze_binary_file(filename, debug=False):
    """Analyze a binary file and extract information"""
```

#### In tech2_workflow_revised.py:
```python
def full_data_workflow(port_name, output_file=None, debug_mode=False):
    """Download all data from Tech2 and extract VIN and seed"""
```

#### In trionic8_calculator.py:
```python
class TRIONIC8_Algorithm:
    """Implementation of the Trionic8 security algorithm"""
    
    def compute(self, seed):
        """Compute the key from the given seed using the defined steps."""
```

## Required Python Files

### 1. `tech2_workflow_revised.py`
```python
import argparse
from tech2_communication_revised import Tech2Communicator
from process_bin_revised import get_seed_only
from trionic8_calculator import TRIONIC8_Algorithm

def quick_seed_key_workflow(port_name):
    """Quick workflow to get seed and calculate key without full download"""
    communicator = Tech2Communicator()
    if not communicator.connect():
        return None, None
    data = communicator.download_chunk(0)
    if not data:
        return None, None
    seed = get_seed_only(data)
    if seed is None:
        return None, None
    algo = TRIONIC8_Algorithm()
    key = algo.compute(seed)
    return seed, key

def main():
    parser = argparse.ArgumentParser(description='Tech2 Data Download and Processing')
    parser.add_argument('-p', '--port', required=True, help='Serial port (e.g., COM4)')
    parser.add_argument('-o', '--output', help='Output file for downloaded data')
    parser.add_argument('-q', '--quick', action='store_true', help='Quick seed/key workflow')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    if args.quick:
        seed, key = quick_seed_key_workflow(args.port)
        if seed is not None and key is not None:
            print("\n========= SECURITY INFORMATION =========")
            print(f"Seed: 0x{seed:04X}")
            print(f"Key:  0x{key:04X}")
            print("=======================================\n")
    else:
        data = full_data_workflow(args.port, args.output, args.debug)
        if data:
            print(f"Successfully downloaded {len(data)} bytes")
        else:
            print("Failed to download data")

if __name__ == "__main__":
    main()
```

### 2. `tech2_communication_revised.py`
```python
import os
import time
import binascii
import sys
from contextlib import contextmanager

def hex_dump(data):
    """Convert binary data to a readable hex format"""
    if isinstance(data, bytes):
        hex_data = binascii.hexlify(data).decode('ascii')
    else:
        hex_data = binascii.hexlify(bytes(data)).decode('ascii')
    return ' '.join([hex_data[i:i+2] for i in range(0, len(hex_data), 2)])

def log(message):
    """Print log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

@contextmanager
def open_tech2_port(port_name):
    """Context manager for safely opening and closing the Tech2 port"""
    port = None
    try:
        port_path = f"\\\\.\\{port_name}" if sys.platform == 'win32' else port_name
        log(f"Opening port: {port_path}")
        port = os.open(port_path, os.O_RDWR | os.O_BINARY)
        log(f"Port opened with handle: {port}")
        time.sleep(1)  # Wait for port to stabilize
        yield port
    except Exception as e:
        log(f"Error opening port: {e}")
        raise
    finally:
        if port is not None:
            try:
                log("Closing port")
                os.close(port)
                log("Port closed")
            except Exception as e:
                log(f"Error closing port: {e}")

def send_command(port, command, description=""):
    """Send a command to the Tech2 and log it"""
    log(f"Sending {description}: {hex_dump(command)}")
    try:
        bytes_written = os.write(port, command)
        log(f"Sent {bytes_written} bytes")
        return True
    except Exception as e:
        log(f"Error sending command: {e}")
        return False

def read_response(port, expected_length, timeout=5, description="response"):
    """Read response from device with timeout"""
    try:
        log(f"Reading {description}... (expecting {expected_length} bytes)")
        response = bytearray()
        start_time = time.time()
        
        while len(response) < expected_length:
            if time.time() - start_time > timeout:
                log(f"Timeout waiting for {description}, continuing with {len(response)} bytes")
                break
            
            try:
                chunk = os.read(port, 32)
                if chunk:
                    response.extend(chunk)
                    log(f"Received {len(chunk)} bytes, total: {len(response)}/{expected_length}")
                    time.sleep(0.1)
                else:
                    time.sleep(0.1)
            except OSError as e:
                log(f"Error reading from port: {e}")
                break
        
        if response:
            log(f"Response: {hex_dump(response)}")
        return response
        
    except Exception as e:
        log(f"Error reading {description}: {e}")
        return bytearray()

def enter_download_mode(port):
    """Enter download mode by sending the download command and waiting"""
    try:
        download_cmd = bytearray([0xEF, 0x56, 0x80, 0x3B])
        if not send_command(port, download_cmd, "initial download command"):
            return False
            
        log("Waiting 2 seconds as per protocol")
        time.sleep(2)
        
        if not send_command(port, download_cmd, "verification download command"):
            return False
            
        log("Reading verification response...")
        verify_response = os.read(port, 4)
        if verify_response:
            log(f"Verification response: {hex_dump(verify_response)}")
        else:
            log("No verification response received")
            log("Continuing despite no verification response")
        
        log("Download mode entered")
        return True
        
    except Exception as e:
        log(f"Error entering download mode: {e}")
        return False

def exit_download_mode(port):
    """Send restart command to return to logo screen"""
    restart_cmd = bytearray([0x8B, 0x56, 0x00, 0x1F])
    try:
        log(f"Sending restart command: {hex_dump(restart_cmd)}")
        bytes_written = os.write(port, restart_cmd)
        log(f"Sent {bytes_written} bytes")
        time.sleep(0.5)
        return True
    except Exception as e:
        log(f"Error sending restart command: {e}")
        return False

def send_security_key(port, key):
    """Send security key to device"""
    key_cmd = bytearray([0x8B, 0x56, 0x02, 0x00, (key >> 8) & 0xFF, key & 0xFF])
    if not send_command(port, key_cmd, "security key command"):
        return False
    
    response = read_response(port, 4, timeout=8, description="key verification response")
    if len(response) != 4:
        log("Failed to receive key verification response")
        return False
    
    if response[1] != 0x00:
        log(f"Key verification failed with status: 0x{response[1]:02X}")
        return False
    
    log("Security key accepted")
    return True

def download_tech2_data(port_name, output_file=None, download_only_seed=False):
    """Download data from Tech2, with option to get only the seed"""
    try:
        data_buffers = []
        
        with open_tech2_port(port_name) as port:
            log("Sending initial restart command...")
            restart_cmd = bytearray([0x8B, 0x56, 0x00, 0x1F])
            if not send_command(port, restart_cmd, "initial restart command"):
                log("Failed to send initial restart command")
                return None
            
            log("Waiting for device to stabilize...")
            time.sleep(2)
            
            if not enter_download_mode(port):
                log("Failed to enter download mode")
                return None
            
            if download_only_seed:
                read_commands = [
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0x00, 0xA6, 0x42])
                ]
                chunk_sizes = [169]
            else:
                read_commands = [
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0x00, 0xA6, 0x42]),
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0xA6, 0xA6, 0x9C]),
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x01, 0x4C, 0xA6, 0xF5]),
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x01, 0xF2, 0xA6, 0x4F]),
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x02, 0x98, 0x32, 0x1C])
                ]
                chunk_sizes = [169, 169, 169, 169, 53]
            
            for i, (cmd, size) in enumerate(zip(read_commands, chunk_sizes)):
                log(f"Starting chunk {i+1} read...")
                if not send_command(port, cmd, f"read command for chunk {i+1}"):
                    log(f"Failed to send read command for chunk {i+1}")
                    return None
                
                chunk = None
                for attempt in range(3):
                    time.sleep(0.5)
                    chunk = os.read(port, size)
                    if chunk:
                        break
                    log(f"Attempt {attempt + 1} failed to read chunk {i+1}, retrying...")
                
                if chunk:
                    log(f"Received {len(chunk)} bytes for chunk {i+1}")
                    if len(chunk) != size:
                        log(f"Warning: Expected {size} bytes for chunk {i+1}, got {len(chunk)}")
                    data_buffers.append(chunk)
                else:
                    log(f"No data received for chunk {i+1} after all attempts")
                
                if download_only_seed and i == 0:
                    break
            
            log("Sending final restart command...")
            if not send_command(port, restart_cmd, "final restart command"):
                log("Failed to send final restart command")
                return None
            time.sleep(0.5)
        
        if data_buffers:
            combined_data = bytearray()
            
            for i, buffer in enumerate(data_buffers):
                chunk_data = buffer[2:] if len(buffer) > 2 else buffer
                combined_data.extend(chunk_data)
            
            log(f"Combined data length: {len(combined_data)} bytes")
            
            if len(combined_data) >= 0x32:
                seed_bytes = combined_data[0x30:0x32]
                seed_value = (seed_bytes[0] << 8) | seed_bytes[1]
                log(f"Extracted seed: 0x{seed_value:04X}")
            
            if len(combined_data) >= 0x25:
                vin = combined_data[0x14:0x14+17]
                vin_str = ''.join(chr(b) for b in vin)
                log(f"VIN: {vin_str}")
            
            return combined_data
            
    except Exception as e:
        log(f"Error downloading data: {e}")
        return None
```

### 3. `process_bin_revised.py`
```python
def get_seed_only(data):
    """Extract seed from binary data"""
    if len(data) >= 0x32:
        seed_bytes = data[0x30:0x32]
        seed_value = (seed_bytes[0] << 8) | seed_bytes[1]
        return seed_value
    return None
``` 
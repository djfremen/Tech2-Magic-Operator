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

def read_response(port, expected_length, timeout=15, description=""):
    """Read response from Tech2 with timeout"""
    log(f"Reading {description}... (expecting {expected_length} bytes)")
    start_time = time.time()
    response = bytearray()
    
    while len(response) < expected_length:
        if time.time() - start_time > timeout:
            log(f"Timeout after {timeout} seconds")
            break
            
        try:
            chunk = os.read(port, expected_length - len(response))
            if chunk:
                response.extend(chunk)
                log(f"Received {len(chunk)} bytes, total: {len(response)}/{expected_length}")
            else:
                time.sleep(0.1)  # No data available, wait a bit
        except Exception as e:
            log(f"Error reading response: {e}")
            break
    
    if response:
        log(f"Response: {hex_dump(response[:min(len(response), 20)])}{'...' if len(response) > 20 else ''}")
    else:
        log("No response received")
        
    return bytes(response)

def enter_download_mode(port):
    """Enter download mode and verify connection"""
    download_cmd = bytearray([0xEF, 0x56, 0x80, 0x3B])
    
    # Send initial download command
    if not send_command(port, download_cmd, "initial download command"):
        return False
    
    # Wait as per protocol
    log("Waiting 2 seconds as per protocol")
    time.sleep(2)
    
    # Send verification command
    if not send_command(port, download_cmd, "verification download command"):
        return False
    
    # Read verification response
    verify_response = read_response(port, 4, timeout=8, description="verification response")
    
    if len(verify_response) != 4:
        log("Failed to receive complete verification response")
        return False
        
    expected_response = bytearray([0xEF, 0x56, 0x01, 0xBA])
    if verify_response != expected_response:
        log(f"Unexpected verification response: {hex_dump(verify_response)}")
        log(f"Expected: {hex_dump(expected_response)}")
        return False
        
    log("Download mode entered successfully")
    return True

def send_restart_command(port):
    """Send restart command to the Tech2"""
    restart_cmd = bytearray([0x8B, 0x56, 0x00, 0x1F])
    return send_command(port, restart_cmd, "restart command")

def download_tech2_data(port_name, output_file=None, download_only_seed=False):
    """Download data from Tech2, with option to get only the seed"""
    try:
        data_buffers = []
        
        with open_tech2_port(port_name) as port:
            # Enter download mode
            if not enter_download_mode(port):
                log("Failed to enter download mode")
                return None
            
            if download_only_seed:
                # For seed-only mode, we only need the first chunk
                read_commands = [
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0x00, 0xA6, 0x42])  # Read 166 bytes at offset 0
                ]
                chunk_sizes = [169]  # Including 2-byte header
            else:
                # For full download, we need all chunks
                read_commands = [
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0x00, 0xA6, 0x42]),  # Read 166 bytes at offset 0
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0xA6, 0xA6, 0x9C]),  # Read 166 bytes at offset 166
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x01, 0x4C, 0xA6, 0xF5]),  # Read 166 bytes at offset 332
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x01, 0xF2, 0xA6, 0x4F]),  # Read 166 bytes at offset 498
                    bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x02, 0x98, 0x32, 0x1C])   # Read 50 bytes at offset 664
                ]
                chunk_sizes = [169, 169, 169, 169, 53]  # Including 2-byte headers
            
            # Read all chunks
            for i, (cmd, size) in enumerate(zip(read_commands, chunk_sizes)):
                if not send_command(port, cmd, f"read command for chunk {i+1}"):
                    log(f"Failed to send read command for chunk {i+1}")
                    return None
                
                chunk = read_response(port, size, timeout=15, description=f"chunk {i+1}")
                
                if len(chunk) != size:
                    log(f"Warning: Expected {size} bytes for chunk {i+1}, got {len(chunk)}")
                
                data_buffers.append(chunk)
                
                if download_only_seed and i == 0:
                    # If we only need the seed, we can exit after the first chunk
                    break
            
            # Send restart command before closing
            send_restart_command(port)
        
        # Process collected data
        if data_buffers:
            combined_data = bytearray()
            
            for i, buffer in enumerate(data_buffers):
                # Skip 2-byte header for each chunk
                chunk_data = buffer[2:] if len(buffer) > 2 else buffer
                combined_data.extend(chunk_data)
            
            log(f"Combined data length: {len(combined_data)} bytes")
            
            # Save data to file if requested
            if output_file:
                with open(output_file, 'wb') as f:
                    f.write(combined_data)
                log(f"Data saved to {output_file}")
            
            return combined_data
        
        return None
        
    except Exception as e:
        log(f"Error in download process: {e}")
        return None 
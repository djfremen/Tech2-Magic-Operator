import os
import time
import argparse
import sys
import binascii

def log(message):
    """Print log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def parse_tech2_data(data):
    """Parse Tech2 data to extract VIN, seed, and calculated key"""
    # Print the first 64 bytes in hex for debugging
    print("\nFirst 64 bytes of data:")
    print(binascii.hexlify(data[:64]).decode('ascii'))
    
    # VIN starts at offset 0x10 (16 bytes) and is 17 bytes long
    # Convert each byte to ASCII, skipping any non-printable characters
    vin_bytes = data[16:33]
    vin = ''.join(chr(b) for b in vin_bytes if 32 <= b <= 126)
    
    # Seed is at offset 0x30 (48 bytes) and is 2 bytes
    seed = int.from_bytes(data[48:50], byteorder='big')
    
    # Calculated key is at offset 0x32 (50 bytes) and is 2 bytes
    calculated_key = int.from_bytes(data[50:52], byteorder='big')
    
    return {
        'vin': vin,
        'seed': seed,
        'calculated_key': calculated_key
    }

def read_with_timeout(fd, length, timeout_sec=15):
    """Read specified number of bytes with timeout"""
    start_time = time.time()
    buffer = bytearray()
    
    while len(buffer) < length:
        if time.time() - start_time > timeout_sec:
            raise TimeoutError(f"Timeout reading {length} bytes (got {len(buffer)})")
            
        try:
            chunk = os.read(fd, length - len(buffer))
            if chunk:
                buffer.extend(chunk)
        except BlockingIOError:
            pass
            
        # Small delay to prevent CPU spinning
        time.sleep(0.01)
        
    return buffer

def download_tech2_data(port_name, output_file=None):
    """Download data from Tech2 device"""
    log(f"Opening port {port_name}")
    
    # Open port directly with os.open()
    port_path = f"\\\\.\\{port_name}"
    fd = os.open(port_path, os.O_RDWR | os.O_BINARY)
    log(f"Port handle: {fd}")
    
    try:
        # Step 1: Enter download mode
        log("Sending download mode command (first)")
        os.write(fd, bytearray([239, 86, 128, 59]))  # EF 56 80 3B
        log("Waiting 2 seconds...")
        time.sleep(2)
        
        # Verify connection by sending command again
        log("Sending download mode command (verification)")
        os.write(fd, bytearray([239, 86, 128, 59]))
        
        # Read verification response
        log("Reading verification response")
        response = read_with_timeout(fd, 4, timeout_sec=8)
        log(f"Verification response: {response.hex(' ')}")
        
        # Step 2: Read data chunks
        data_buffers = []
        
        # Chunk 1: 166 bytes at offset 0
        log("Reading chunk 1/5 (offset 0)")
        os.write(fd, bytearray([129, 90, 15, 46, 0, 0, 166, 66]))
        chunk1 = read_with_timeout(fd, 169, timeout_sec=15)
        data_buffers.append(chunk1[2:])  # Skip 2-byte header
        
        # Chunk 2: 166 bytes at offset 166
        log("Reading chunk 2/5 (offset 166)")
        os.write(fd, bytearray([129, 90, 15, 46, 0, 166, 166, 156]))
        chunk2 = read_with_timeout(fd, 169, timeout_sec=15)
        data_buffers.append(chunk2[2:])  # Skip 2-byte header
        
        # Chunk 3: 166 bytes at offset 332
        log("Reading chunk 3/5 (offset 332)")
        os.write(fd, bytearray([129, 90, 15, 46, 1, 76, 166, 245]))
        chunk3 = read_with_timeout(fd, 169, timeout_sec=15)
        data_buffers.append(chunk3[2:])  # Skip 2-byte header
        
        # Chunk 4: 166 bytes at offset 498
        log("Reading chunk 4/5 (offset 498)")
        os.write(fd, bytearray([129, 90, 15, 46, 1, 242, 166, 79]))
        chunk4 = read_with_timeout(fd, 169, timeout_sec=15)
        data_buffers.append(chunk4[2:])  # Skip 2-byte header
        
        # Chunk 5: 50 bytes at offset 664
        log("Reading chunk 5/5 (offset 664)")
        os.write(fd, bytearray([129, 90, 15, 46, 2, 152, 50, 28]))
        chunk5 = read_with_timeout(fd, 53, timeout_sec=15)
        data_buffers.append(chunk5[2:])  # Skip 2-byte header
        
        # Step 3: Combine data chunks
        log("Combining data chunks")
        combined_data = bytearray()
        for buffer in data_buffers:
            combined_data.extend(buffer)
        
        log(f"Total data size: {len(combined_data)} bytes")
        
        # Step 4: Restart the device
        log("Restarting Tech2 device")
        os.write(fd, bytearray([139, 86, 0, 31]))  # 8B 56 00 1F
        restart_response = read_with_timeout(fd, 4, timeout_sec=15)
        log(f"Restart response: {restart_response.hex(' ')}")
        
        # Save data if output file specified
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(combined_data)
            log(f"Data saved to {output_file}")
        
        return combined_data
        
    except Exception as e:
        log(f"Error: {str(e)}")
        return None
        
    finally:
        # Clean up
        os.close(fd)
        log("Port closed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download data from SAAB Tech2 device")
    parser.add_argument("-p", "--port", required=True, help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument("-o", "--output", help="Output file path (optional)")
    args = parser.parse_args()
    
    try:
        data = download_tech2_data(args.port, args.output)
        if data:
            log("Download completed successfully")
            
            # Parse and display the data
            parsed_data = parse_tech2_data(data)
            print("\nExtracted Information:")
            print(f"VIN: {parsed_data['vin']}")
            print(f"Seed: 0x{parsed_data['seed']:04X}")
            print(f"Calculated Key: 0x{parsed_data['calculated_key']:04X}")
            
            # Print some info about the data
            log(f"First 16 bytes: {data[:16].hex(' ')}")
            log(f"Last 16 bytes: {data[-16:].hex(' ')}")
        else:
            log("Download failed")
            sys.exit(1)
    except KeyboardInterrupt:
        log("Operation canceled by user")
        sys.exit(1) 
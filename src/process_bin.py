import os
import sys
import time
import binascii
import struct

# Add the src directory to the Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)

from trionic8_calculator import TRIONIC8_Algorithm

def hex_dump(data):
    if isinstance(data, bytes):
        hex_data = binascii.hexlify(data).decode('ascii')
    else:
        hex_data = binascii.hexlify(bytes(data)).decode('ascii')
    return ' '.join([hex_data[i:i+2] for i in range(0, len(hex_data), 2)])

def read_bin_file(filename):
    # Try current directory first
    if os.path.exists(filename):
        filepath = filename
    else:
        # Try data directory relative to script location
        filepath = os.path.join(PROJECT_ROOT, 'data', filename)
    
    print(f"Looking for file at: {filepath}")
    
    try:
        with open(filepath, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {filepath} not found. Please run tech2_direct.py first to get the data.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def process_bin_data(data):
    if not data:
        return None
        
    print(f"\nRaw data size: {len(data)} bytes")
    print("First 32 bytes of raw data:")
    print(hex_dump(data[:32]))
    
    # Define the read commands with their offsets and lengths
    read_commands = [
        [0, 0, 166, 66],    # Read 169 bytes at offset 0
        [0, 166, 166, 156], # Read 169 bytes at offset 166
        [1, 76, 166, 245],  # Read 169 bytes at offset 332
        [1, 242, 166, 79],  # Read 169 bytes at offset 498
        [2, 152, 50, 28]    # Read 53 bytes at offset 664
    ]
    
    all_data = bytearray()
    
    for i, cmd in enumerate(read_commands):
        # Calculate offset and length
        offset = (cmd[0] << 8) | cmd[1]
        length = (cmd[2] << 8) | cmd[3]
        
        print(f"\nProcessing chunk {i+1}:")
        print(f"Offset: 0x{offset:04X}")
        print(f"Length: {length} bytes")
        
        # Extract data chunk
        chunk = data[offset:offset + length]
        print(f"Actual chunk size: {len(chunk)} bytes")
        
        if len(chunk) < length:
            print(f"Warning: Chunk is shorter than expected")
            # Don't pad with zeros, just use what we have
            all_data.extend(chunk)
        else:
            all_data.extend(chunk)
            
        print("First 16 bytes of chunk:")
        print(hex_dump(chunk[:16]))
    
    return bytes(all_data)

def is_valid_vin_char(c):
    """Check if a character is valid in a VIN"""
    return (c >= 'A' and c <= 'Z' and c not in 'IOQ') or (c >= '0' and c <= '9')

def extract_vin(data):
    """Extract VIN from the processed data"""
    if not data or len(data) < 0x15 + 18:  # +18 to account for the extra byte
        print(f"Data too short for VIN extraction. Length: {len(data)}")
        return None
        
    # VIN starts at offset 0x15 + 1 (skip the extra byte), 17 bytes
    vin_data = data[0x15+1:0x15+18]  # Skip the 0xFF byte
    print("\nVIN data bytes:")
    print(hex_dump(vin_data))
    
    # Convert bytes to string, filtering out non-printable characters
    vin = ''.join(chr(b) for b in vin_data if 32 <= b <= 126)
    print(f"Raw VIN: {vin}")
    
    # Validate VIN
    if len(vin) != 17:
        print("Invalid VIN length")
        return None
        
    if not all(is_valid_vin_char(c) for c in vin):
        print("Invalid characters in VIN")
        return None
        
    return vin

def main():
    print("Starting bin file processing...")
    
    # Read the bin file
    data = read_bin_file('tech2_data.bin')
    if not data:
        return
        
    # Process the data
    processed_data = process_bin_data(data)
    if not processed_data:
        return
        
    print(f"\nProcessed data size: {len(processed_data)} bytes")
    
    # Extract VIN
    vin = extract_vin(processed_data)
    if vin:
        print(f"\nFound VIN: {vin}")
    else:
        print("\nNo valid VIN found in data")
    
    # Initialize TRIONIC8 algorithm
    algo = TRIONIC8_Algorithm()
    
    # Process seed (0x3B86 from the data)
    seed = 0x3B86
    print("\nProcessing seed...")
    print(f"Seed: 0x{seed:04x}")
    
    # Calculate the key
    key = algo.compute(seed)
    print(f"Calculated key: 0x{key:04x}\n")
    
    # Save processed data
    try:
        output_path = os.path.join(PROJECT_ROOT, 'data', 'processed_data.bin')
        with open(output_path, 'wb') as f:
            f.write(processed_data)
        print(f"\nSaved processed data to {output_path}")
    except Exception as e:
        print(f"\nError saving processed data: {e}")

if __name__ == "__main__":
    main() 
import binascii
import os
import time


def hex_dump(data, bytes_per_line=16):
    """Create a formatted hex dump of binary data"""
    if not data:
        return "No data to display"
        
    result = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        hex_values = ' '.join([f"{b:02X}" for b in chunk])
        
        # Convert to ASCII (print dots for non-printable chars)
        ascii_values = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in chunk])
        
        # Create line with offset, hex values and ASCII representation
        line = f"{i:04X}:  {hex_values.ljust(bytes_per_line * 3)}  {ascii_values}"
        result.append(line)
        
    return '\n'.join(result)


def extract_data_from_binary(data, data_type='all'):
    """Extract specified information from binary data
    
    Args:
        data: Binary data
        data_type: Type of data to extract ('all', 'vin', 'seed')
        
    Returns:
        Extracted data based on type, or dictionary of all data if type='all'
    """
    if not data:
        return None
        
    extracted_data = {}
    
    # Extract VIN (starting at offset 0x14, 17 bytes)
    if data_type in ['all', 'vin'] and len(data) >= 0x14 + 17:
        vin_bytes = data[0x14:0x14 + 17]
        try:
            # Convert bytes to ASCII, removing non-printable characters
            vin = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in vin_bytes])
            # Additional validation (VINs typically have alphanumeric characters)
            if all(c.isalnum() or c == '.' for c in vin):
                extracted_data['vin'] = vin
        except Exception:
            extracted_data['vin'] = None
            
    # Extract Security Seed (starting at offset 0x30, 2 bytes)
    if data_type in ['all', 'seed'] and len(data) >= 0x30 + 2:
        seed_bytes = data[0x30:0x30 + 2]
        try:
            seed_value = (seed_bytes[0] << 8) | seed_bytes[1]
            extracted_data['seed'] = seed_value
        except Exception:
            extracted_data['seed'] = None
    
    # Return results based on requested data_type
    if data_type == 'all':
        return extracted_data
    elif data_type in extracted_data:
        return extracted_data[data_type]
    else:
        return None


def validate_vin(vin):
    """Validate VIN using standard VIN validation rules
    
    VIN validation rules:
    - Must be 17 characters
    - Can only contain alphanumeric characters except I, O, Q
    - Check digit in position 9 should validate
    
    Returns:
        Boolean indicating if VIN is valid
    """
    if not vin or len(vin) != 17:
        return False
        
    # VINs should only contain allowed characters (alphanumeric excluding I, O, Q)
    allowed_chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    if not all(c in allowed_chars for c in vin.upper()):
        return False
    
    # Basic structure check - we're not implementing the full check digit validation
    # as it's complex and depends on the specific manufacturer
    return True


def save_binary_data(data, filename, overwrite=False):
    """Save binary data to a file"""
    if not data:
        print("No data to save")
        return False
        
    if os.path.exists(filename) and not overwrite:
        raise FileExistsError(f"File {filename} already exists. Use overwrite=True to force.")
        
    try:
        with open(filename, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def load_binary_data(filename):
    """Load binary data from a file"""
    try:
        with open(filename, 'rb') as f:
            data = f.read()
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def analyze_binary_file(filename, debug=False):
    """Analyze a binary file and extract information"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] Analyzing file: {filename}")
    
    data = load_binary_data(filename)
    if not data:
        return None
        
    # Extract VIN and seed
    vin = extract_data_from_binary(data, 'vin')
    seed = extract_data_from_binary(data, 'seed')
    
    print(f"File size: {len(data)} bytes")
    
    if vin:
        vin_valid = validate_vin(vin)
        print(f"VIN: {vin} {'(VALID)' if vin_valid else '(INVALID FORMAT)'}")
    else:
        print("VIN: Not found")
        
    if seed:
        print(f"Seed: 0x{seed:04X}")
        
        # Import here to avoid circular imports
        try:
            from trionic8_calculator import TRIONIC8_Algorithm
            algo = TRIONIC8_Algorithm()
            key = algo.compute(seed)
            print(f"Calculated Key: 0x{key:04X}")
        except ImportError:
            print("Note: trionic8_calculator not available, key calculation skipped")
    else:
        print("Security seed: Not found")
    
    if debug:
        print("\nHex dump of first 128 bytes:")
        print(hex_dump(data[:128]))
    
    return {
        'filename': filename,
        'filesize': len(data),
        'vin': vin,
        'seed': seed
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Tech2 Binary Data Processing')
    parser.add_argument('filename', help='Binary file to process')
    parser.add_argument('-d', '--debug', action='store_true', help='Display hex dump of file')
    args = parser.parse_args()
    
    analyze_binary_file(args.filename, args.debug)

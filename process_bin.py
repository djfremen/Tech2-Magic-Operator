def parse_tech2_data(data):
    """Parse the binary data from Tech2 to extract VIN, seed, and key"""
    if not data or len(data) < 0x50:
        return None
    
    # Extract VIN (starting at offset 0x15+1, 17 bytes)
    vin_data = data[0x15+1:0x15+18]
    vin = ''.join(chr(b) for b in vin_data if 32 <= b <= 126)
    
    # Extract seed (at offset 0x30, 2 bytes)
    if len(data) >= 0x32:
        seed_bytes = data[0x30:0x32]
        seed = (seed_bytes[0] << 8) | seed_bytes[1]
    else:
        seed = None
    
    # Extract calculated key (at offset 0x32, 2 bytes)
    if len(data) >= 0x34:
        key_bytes = data[0x32:0x34]
        key = (key_bytes[0] << 8) | key_bytes[1]
    else:
        key = None
    
    return {
        'vin': vin if len(vin) == 17 else None,
        'seed': seed,
        'calculated_key': key
    }

def get_seed_only(data):
    """Extract only the seed value from binary data"""
    if data and len(data) >= 0x32:
        # Seed is at offset 0x30, two bytes
        seed_bytes = data[0x30:0x32]
        seed_value = (seed_bytes[0] << 8) | seed_bytes[1]
        return seed_value
    return None

def read_bin_file(filename):
    """Read a binary file"""
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def save_bin_file(data, filename):
    """Save binary data to a file"""
    try:
        with open(filename, 'wb') as f:
            f.write(data)
        print(f"Data saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False 
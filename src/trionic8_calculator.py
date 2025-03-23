import os
import time
import binascii
import struct

def hex_dump(data):
    if isinstance(data, bytes):
        hex_data = binascii.hexlify(data).decode('ascii')
    else:
        hex_data = binascii.hexlify(bytes(data)).decode('ascii')
    return ' '.join([hex_data[i:i+2] for i in range(0, len(hex_data), 2)])

# --- Utility functions (16-bit operations) ---
def rotate_left(val, bits):
    """Rotate left by `bits` (16-bit safe)."""
    bits = bits % 16
    return ((val << bits) | (val >> (16 - bits))) & 0xFFFF

def rotate_right(val, bits):
    """Rotate right by `bits` (16-bit safe)."""
    bits = bits % 16
    return ((val >> bits) | (val << (16 - bits))) & 0xFFFF

def swap_bytes_and_add(val, add_value):
    """Swap high/low bytes and add a fixed value."""
    swapped = ((val >> 8) & 0xFF) | ((val & 0xFF) << 8)
    return (swapped + add_value) & 0xFFFF

def subtract(val, value):
    """Subtract a fixed value from val."""
    return (val - value) & 0xFFFF

# --- TRIONIC8 Algorithm Implementation ---
class TRIONIC8_Algorithm:
    def __init__(self):
        self.steps = [
            {'op': 'ror', 'bits': 7},
            {'op': 'rol', 'bits': 10},
            {'op': 'swap_add', 'value': 0xF8DA},
            {'op': 'sub', 'value': 0x3F52}
        ]

    def compute(self, seed):
        """Compute the key from the given seed using the defined steps."""
        key = seed
        for step in self.steps:
            if step['op'] == 'ror':
                key = rotate_right(key, step['bits'])
            elif step['op'] == 'rol':
                key = rotate_left(key, step['bits'])
            elif step['op'] == 'swap_add':
                key = swap_bytes_and_add(key, step['value'])
            elif step['op'] == 'sub':
                key = subtract(key, step['value'])
        return key

def read_tech2_data():
    try:
        with open('tech2_data.bin', 'rb') as f:
            return f.read()
    except FileNotFoundError:
        print("Error: tech2_data.bin not found. Please run download_data.py first.")
        return None

try:
    print("Starting security key process...")
    
    # Read the downloaded data
    data = read_tech2_data()
    if not data:
        exit(1)
    
    # Find VIN (starts at offset 0x15, 17 bytes)
    vin_offset = 0x15
    vin_data = data[vin_offset:vin_offset+17]
    vin = ''.join(chr(b) for b in vin_data if 32 <= b <= 126)
    print(f"\nFound VIN: {vin}")
    
    # Process the seed (0x3B86 from the data)
    seed = 0x3B86  # This is the seed we got from the data
    print("\nProcessing seed...")
    print(f"Seed: 0x{seed:04x}")
    
    # Initialize the TRIONIC8 algorithm
    algo = TRIONIC8_Algorithm()
    
    # Calculate the key
    key = algo.compute(seed)
    print(f"Calculated key: 0x{key:04x}\n")
    
    print("Key calculation complete. No keys were sent to the device.")

except Exception as e:
    print(f"Error: {e}") 
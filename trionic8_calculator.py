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

def print_key_calculation_steps(seed):
    """Print each step of the key calculation process for debugging"""
    print(f"\nTrionic8 Security Key Calculation:")
    print(f"Input Seed: 0x{seed:04X}")
    
    # Step 1: Rotate right by 7 bits
    step1 = rotate_right(seed, 7)
    print(f"Step 1 - ROR 7:    0x{step1:04X}")
    
    # Step 2: Rotate left by 10 bits
    step2 = rotate_left(step1, 10)
    print(f"Step 2 - ROL 10:   0x{step2:04X}")
    
    # Step 3: Swap bytes and add 0xF8DA
    step3 = swap_bytes_and_add(step2, 0xF8DA)
    print(f"Step 3 - SWAP+ADD: 0x{step3:04X}")
    
    # Step 4: Subtract 0x3F52
    step4 = subtract(step3, 0x3F52)
    print(f"Step 4 - SUB:      0x{step4:04X}")
    
    print(f"Final Key:         0x{step4:04X}")
    return step4

# Standalone testing function
def test_with_known_values():
    known_pairs = [
        (0x3B86, 0x3BAF),  # Example from your data
        (0x1234, 0x8A83),  # Test value
        (0xABCD, 0x2323)   # Test value
    ]
    
    algo = TRIONIC8_Algorithm()
    print("\nTesting with known seed-key pairs:")
    
    for seed, expected_key in known_pairs:
        calculated_key = algo.compute(seed)
        print(f"Seed: 0x{seed:04X}, Expected Key: 0x{expected_key:04X}, Calculated: 0x{calculated_key:04X}")
        if calculated_key == expected_key:
            print("✓ MATCH")
        else:
            print("✗ MISMATCH")

# Main function for standalone use
if __name__ == "__main__":
    print("Trionic8 Security Algorithm Calculator")
    print("=====================================")
    
    try:
        # Allow testing with command line argument
        import sys
        if len(sys.argv) > 1:
            try:
                # Try to parse the argument as a hex value
                test_seed = int(sys.argv[1], 16)
                print(f"Using provided seed: 0x{test_seed:04X}")
                print_key_calculation_steps(test_seed)
            except ValueError:
                print(f"Error: Could not parse '{sys.argv[1]}' as a hex value")
                sys.exit(1)
        else:
            # Run tests with known values
            test_with_known_values()
            
            # Interactive mode
            print("\nEnter a seed value to calculate the key (or press Ctrl+C to exit):")
            while True:
                try:
                    seed_input = input("Seed (hex, e.g. 3B86): 0x")
                    seed_value = int(seed_input, 16)
                    print_key_calculation_steps(seed_value)
                except ValueError:
                    print(f"Error: Could not parse '{seed_input}' as a hex value")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
    except Exception as e:
        print(f"Error: {e}")

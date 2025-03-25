import binascii
import sys


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


class TRIONIC8_Algorithm:
    """Implementation of the Trionic8 security algorithm"""
    
    def __init__(self):
        # Define the algorithm steps and parameters
        self.steps = [
            {'op': 'ror', 'bits': 7},           # Step 1: Rotate right by 7 bits
            {'op': 'rol', 'bits': 10},          # Step 2: Rotate left by 10 bits
            {'op': 'swap_add', 'value': 0xF8DA}, # Step 3: Swap bytes and add 0xF8DA
            {'op': 'sub', 'value': 0x3F52}      # Step 4: Subtract 0x3F52
        ]

    def compute(self, seed):
        """Compute the key from the given seed using the defined steps."""
        if not isinstance(seed, int) or seed < 0 or seed > 0xFFFF:
            raise ValueError(f"Seed must be a 16-bit integer (0-65535), got: {seed}")
            
        key = seed
        
        for i, step in enumerate(self.steps):
            op = step['op']
            
            if op == 'ror':
                key = rotate_right(key, step['bits'])
            elif op == 'rol':
                key = rotate_left(key, step['bits'])
            elif op == 'swap_add':
                key = swap_bytes_and_add(key, step['value'])
            elif op == 'sub':
                key = subtract(key, step['value'])
            else:
                raise ValueError(f"Unknown operation: {op}")
                
        return key
    
    def compute_with_steps(self, seed):
        """Compute the key and return intermediate steps for debugging."""
        if not isinstance(seed, int) or seed < 0 or seed > 0xFFFF:
            raise ValueError(f"Seed must be a 16-bit integer (0-65535), got: {seed}")
            
        results = [('Input Seed', seed)]
        key = seed
        
        for i, step in enumerate(self.steps):
            op = step['op']
            
            if op == 'ror':
                key = rotate_right(key, step['bits'])
                results.append((f"Step {i+1} - ROR {step['bits']}", key))
            elif op == 'rol':
                key = rotate_left(key, step['bits'])
                results.append((f"Step {i+1} - ROL {step['bits']}", key))
            elif op == 'swap_add':
                key = swap_bytes_and_add(key, step['value'])
                results.append((f"Step {i+1} - SWAP+ADD 0x{step['value']:04X}", key))
            elif op == 'sub':
                key = subtract(key, step['value'])
                results.append((f"Step {i+1} - SUB 0x{step['value']:04X}", key))
            else:
                raise ValueError(f"Unknown operation: {op}")
                
        results.append(('Final Key', key))
        return results


def print_key_calculation_steps(seed):
    """Print each step of the key calculation process for debugging"""
    print(f"\nTrionic8 Security Key Calculation:")
    
    algo = TRIONIC8_Algorithm()
    steps = algo.compute_with_steps(seed)
    
    for description, value in steps:
        print(f"{description}: 0x{value:04X}")
    
    return steps[-1][1]  # Return the final key


def test_with_known_values():
    """Test the algorithm with known seed-key pairs"""
    known_pairs = [
        (0x3B86, 0x3BAF),
        (0x1234, 0x8A83),
        (0xABCD, 0x2323),
        (0xFFFF, 0xB987)  # Typical default seed
    ]
    
    algo = TRIONIC8_Algorithm()
    print("\nTesting with known seed-key pairs:")
    
    for seed, expected_key in known_pairs:
        calculated_key = algo.compute(seed)
        print(f"Seed: 0x{seed:04X}, Expected Key: 0x{expected_key:04X}, Calculated: 0x{calculated_key:04X}", end=" ")
        if calculated_key == expected_key:
            print("✓ MATCH")
        else:
            print("✗ MISMATCH")


if __name__ == "__main__":
    print("Trionic8 Security Algorithm Calculator")
    print("=====================================")
    
    try:
        if len(sys.argv) > 1:
            try:
                test_seed = int(sys.argv[1], 16)
                print(f"Using provided seed: 0x{test_seed:04X}")
                key = print_key_calculation_steps(test_seed)
                print(f"\nSeed: 0x{test_seed:04X} → Key: 0x{key:04X}")
            except ValueError:
                print(f"Error: Could not parse '{sys.argv[1]}' as a hex value")
                sys.exit(1)
        else:
            test_with_known_values()
            
            print("\nEnter a seed value to calculate the key (or press Ctrl+C to exit):")
            while True:
                try:
                    seed_input = input("Seed (hex, e.g. 3B86): 0x")
                    seed_value = int(seed_input, 16)
                    key = print_key_calculation_steps(seed_value)
                    print(f"\nSeed: 0x{seed_value:04X} → Key: 0x{key:04X}")
                except ValueError:
                    print(f"Error: Could not parse '{seed_input}' as a hex value")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
    except Exception as e:
        print(f"Error: {e}")

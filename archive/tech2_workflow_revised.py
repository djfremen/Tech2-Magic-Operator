import argparse
import os
import sys
from tech2_communication_revised import Tech2Communicator
from trionic8_calculator import TRIONIC8_Algorithm
from process_bin_revised import extract_data_from_binary


def log(message, debug=False):
    """Print log message with timestamp"""
    import time
    timestamp = time.strftime("%H:%M:%S")
    
    if debug:
        print(f"[{timestamp}][DEBUG] {message}")
    else:
        print(f"[{timestamp}] {message}")


def full_data_workflow(port_name, output_file=None, debug_mode=False):
    """Download all data from Tech2 and extract VIN and seed"""
    log("Starting Tech2 data extraction workflow...", debug_mode)
    
    tech2 = Tech2Communicator(port_name, debug_mode=debug_mode)
    try:
        if not tech2.connect():
            log("Failed to connect to Tech2", debug_mode)
            return None
            
        tech2.send_restart_command()
        
        if not tech2.enter_download_mode():
            log("Failed to enter download mode", debug_mode)
            return None
            
        # Download all five chunks of data
        all_data = bytearray()
        
        for chunk_index in range(5):
            chunk_data = tech2.download_chunk(chunk_index)
            if not chunk_data:
                log(f"Failed to download chunk {chunk_index}", debug_mode)
                continue
            all_data.extend(chunk_data[2:] if len(chunk_data) > 2 else chunk_data)
        
        if not all_data:
            log("Failed to download any data", debug_mode)
            return None
            
        # Extract VIN and seed
        vin = extract_data_from_binary(all_data, 'vin')
        seed = extract_data_from_binary(all_data, 'seed')
        
        log(f"Data length: {len(all_data)} bytes", debug_mode)
        
        if vin:
            log(f"VIN: {vin}")
        else:
            log("WARNING: Could not extract VIN - data may be corrupted")
            
        if seed:
            log(f"Seed: 0x{seed:04X}")
            algo = TRIONIC8_Algorithm()
            key = algo.compute(seed)
            log(f"Calculated key: 0x{key:04X}")
        else:
            log("WARNING: Could not extract security seed - data may be corrupted")
        
        # Save data if output file is specified
        if output_file and all_data:
            try:
                with open(output_file, 'wb') as f:
                    f.write(all_data)
                log(f"Data saved to {output_file}")
            except Exception as e:
                log(f"Error saving data: {e}")
        
        return all_data
    finally:
        tech2.disconnect()


def validate_vin(vin):
    """Basic validation for VIN format"""
    if not vin or len(vin) != 17:
        return False
        
    # Check for valid VIN characters (alphanumeric except I, O, Q)
    valid_chars = set("ABCDEFGHJKLMNPRSTUVWXYZ0123456789")
    return all(c in valid_chars for c in vin.upper() if c.isalnum())


def main():
    parser = argparse.ArgumentParser(description='Tech2 Data Download and Processing Tool')
    parser.add_argument('-p', '--port', required=True, help='Serial port (e.g., COM4)')
    parser.add_argument('-o', '--output', help='Output file for downloaded data')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    data = full_data_workflow(args.port, args.output, args.debug)
    
    if data:
        log(f"Successfully downloaded {len(data)} bytes")
        
        # Print summary
        print("\n========= DEVICE INFORMATION =========")
        vin = extract_data_from_binary(data, 'vin')
        seed = extract_data_from_binary(data, 'seed')
        
        if vin:
            vin_valid = validate_vin(vin)
            print(f"VIN: {vin} {'(VALID)' if vin_valid else '(INVALID FORMAT)'}")
        else:
            print("VIN: Not found")
            
        if seed:
            algo = TRIONIC8_Algorithm()
            key = algo.compute(seed)
            print(f"Seed: 0x{seed:04X}")
            print(f"Key:  0x{key:04X}")
        else:
            print("Security seed: Not found")
        print("====================================\n")
    else:
        log("Failed to download data")


if __name__ == "__main__":
    main()

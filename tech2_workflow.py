import os
import sys
import time
import argparse
from trionic8_calculator import TRIONIC8_Algorithm
from import_serial import (
    log, download_tech2_data, open_tech2_port, 
    send_restart_command
)
from process_bin import (
    parse_tech2_data, get_seed_only,
    read_bin_file, save_bin_file
)

def quick_seed_key_workflow(port_name):
    """Quick workflow to get seed and calculate key without full download"""
    log("Starting quick seed/key workflow...")
    
    # Download just enough data to get the seed
    data = download_tech2_data(port_name, download_only_seed=True)
    
    if not data:
        log("Failed to get data from Tech2")
        return None, None
    
    # Extract seed from data
    seed = get_seed_only(data)
    if seed is None:
        log("Failed to extract seed from data")
        return None, None
    
    log(f"Got seed: 0x{seed:04X}")
    
    # Calculate the key
    algo = TRIONIC8_Algorithm()
    key = algo.compute(seed)
    log(f"Calculated key: 0x{key:04X}")
    
    return seed, key

def main():
    parser = argparse.ArgumentParser(description="Complete Tech2 workflow: download, process, and calculate keys")
    parser.add_argument("-p", "--port", help="Serial port (e.g., COM5)")
    parser.add_argument("-d", "--download", action="store_true", help="Download full data from Tech2")
    parser.add_argument("-q", "--quick", action="store_true", help="Quick seed/key only (faster)")
    parser.add_argument("-r", "--read", help="Read and process existing data file")
    parser.add_argument("-x", "--restart", action="store_true", help="Just send restart command to Tech2")
    args = parser.parse_args()

    try:
        # Handle restart-only mode
        if args.restart and args.port:
            log("Sending restart command to Tech2...")
            with open_tech2_port(args.port) as port:
                send_restart_command(port)
            log("Restart command sent")
            return
        
        # Quick seed/key mode
        if args.quick and args.port:
            seed, key = quick_seed_key_workflow(args.port)
            if seed and key:
                print("\n========= SECURITY INFORMATION =========")
                print(f"Seed: 0x{seed:04X}")
                print(f"Key:  0x{key:04X}")
                print("=======================================\n")
            return
        
        # Full download mode
        if args.download and args.port:
            log("Starting full download process...")
            data = download_tech2_data(args.port, "tech2_data.bin")
            
            if not data:
                log("Download failed")
                return
            
            # Parse and display the downloaded data
            parsed_data = parse_tech2_data(data)
            if parsed_data:
                print("\n======== DOWNLOADED DATA ========")
                print(f"VIN: {parsed_data['vin']}")
                print(f"Seed: 0x{parsed_data['seed']:04X}")
                
                # Calculate our own key
                algo = TRIONIC8_Algorithm()
                calculated_key = algo.compute(parsed_data['seed'])
                original_key = parsed_data['calculated_key']
                
                print(f"Original Key: 0x{original_key:04X}")
                print(f"Calculated Key: 0x{calculated_key:04X}")
                print(f"Keys Match: {original_key == calculated_key}")
                print("===============================\n")
            
        # Process existing file
        if args.read:
            log(f"Reading and processing data file: {args.read}")
            data = read_bin_file(args.read)
            
            if not data:
                log("Failed to read data file")
                return
            
            # Parse and display data
            parsed_data = parse_tech2_data(data)
            if parsed_data:
                print("\n======== FILE DATA ========")
                print(f"VIN: {parsed_data['vin']}")
                print(f"Seed: 0x{parsed_data['seed']:04X}")
                
                # Calculate our own key
                algo = TRIONIC8_Algorithm()
                calculated_key = algo.compute(parsed_data['seed'])
                original_key = parsed_data['calculated_key']
                
                print(f"Original Key: 0x{original_key:04X}")
                print(f"Calculated Key: 0x{calculated_key:04X}")
                print(f"Keys Match: {original_key == calculated_key}")
                print("==========================\n")
        
        log("Workflow completed successfully")
        
    except KeyboardInterrupt:
        log("Operation canceled by user")
        sys.exit(1)
    except Exception as e:
        log(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
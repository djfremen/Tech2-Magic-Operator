import os
import time
import argparse
import sys
from import_serial import download_tech2_data, parse_tech2_data
from process_bin import process_bin_data, read_bin_file

def log(message):
    """Print log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    parser = argparse.ArgumentParser(description="Complete Tech2 workflow: download, process, and upload data")
    parser.add_argument("-p", "--port", required=True, help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument("-d", "--download", action="store_true", help="Download data from Tech2")
    parser.add_argument("-r", "--read", action="store_true", help="Read and process existing data file")
    parser.add_argument("-u", "--upload", action="store_true", help="Upload processed data back to Tech2")
    args = parser.parse_args()

    try:
        data = None
        
        # Step 1: Download data if requested
        if args.download:
            log("Starting download process...")
            data = download_tech2_data(args.port, "tech2_data.bin")
            if not data:
                log("Download failed")
                return
            
            # Parse and display the downloaded data
            parsed_data = parse_tech2_data(data)
            print("\nDownloaded Data:")
            print(f"VIN: {parsed_data['vin']}")
            print(f"Seed: 0x{parsed_data['seed']:04X}")
            print(f"Calculated Key: 0x{parsed_data['calculated_key']:04X}")
        
        # Step 2: Process data if requested
        if args.read:
            log("Reading and processing data file...")
            try:
                # If we already have the data from download, use it
                if data is None:
                    data = read_bin_file("tech2_data.bin")
                
                if data:
                    parsed_data = parse_tech2_data(data)
                    print("\nProcessed Data:")
                    print(f"VIN: {parsed_data['vin']}")
                    print(f"Seed: 0x{parsed_data['seed']:04X}")
                    print(f"Calculated Key: 0x{parsed_data['calculated_key']:04X}")
                    
                    # Process the binary file
                    processed_data = process_bin_data(data)
                    if processed_data:
                        log("Data processing completed")
                    else:
                        log("Data processing failed")
                else:
                    log("Failed to read data file")
                    return
            except Exception as e:
                log(f"Error processing data: {str(e)}")
                return
        
        # Step 3: Upload data if requested
        if args.upload:
            log("Starting upload process...")
            # TODO: Implement upload functionality
            log("Upload functionality to be implemented")
        
        log("Workflow completed successfully")
        
    except KeyboardInterrupt:
        log("Operation canceled by user")
        sys.exit(1)
    except Exception as e:
        log(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
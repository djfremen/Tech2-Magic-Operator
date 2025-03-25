# Tech2 Communication Tool

A Python-based tool for communicating with Saab Tech2 diagnostic devices to extract vehicle information, including VIN numbers and security seeds.

## Overview

This tool provides a reliable way to establish a serial connection with a Tech2 diagnostic device, extract data, and process the results. The implementation follows the Tech2 communication protocol, handles error cases gracefully, and provides comprehensive debugging capabilities.

## Key Features

- Tech2 device communication via serial port
- Automatic extraction of VIN and security seed
- Trionic8 key calculation algorithm
- Binary data processing and validation
- Detailed logging and debugging options
- Proper device reboot after data transmission

## Requirements

- Python 3.6 or higher
- Windows, macOS, or Linux
- No external Python packages required (uses standard libraries)
- Tech2 device with USB-to-Serial adapter

## Hardware Setup

1. Connect the Tech2 device to your computer via a USB-to-Serial adapter
2. Identify the correct COM port:
   - Windows: Usually COM3, COM4, or COM5
   - macOS/Linux: Usually /dev/tty.usbserial-*

## Usage

### Basic Operation

To extract VIN and security seed from the Tech2 device:

```bash
python tech2_workflow_revised.py -p COM3
```

### With Debug Output

For detailed logging during operation:

```bash
python tech2_workflow_revised.py -p COM3 -d
```

### Save Binary Data

To save the extracted binary data to a file:

```bash
python tech2_workflow_revised.py -p COM3 -o tech2_data.bin
```

## Project Structure

The project consists of four main Python files:

### 1. tech2_workflow_revised.py

The main script that orchestrates the entire process. It handles command-line arguments, initializes the Tech2 communication, and processes the extracted data.

**Key Functions:**
- `full_data_workflow()`: Downloads all data and extracts information
- `validate_vin()`: Validates VIN format and structure
- `main()`: Handles command-line arguments and runs the workflow

### 2. tech2_communication_revised.py

Handles all device communication with robust error handling. Implements the Tech2Communicator class that manages the serial port connection and communication protocol.

**Key Methods:**
- `connect()`: Establishes connection to the device
- `disconnect()`: Safely closes the connection and reboots the device
- `send_restart_command()`: Sends device restart command
- `enter_download_mode()`: Puts device in download mode
- `download_chunk()`: Downloads a specific data chunk
- `send_security_key()`: Sends calculated security key to device

### 3. process_bin_revised.py

Processes binary data extracted from the device. Provides functions for data extraction, validation, and analysis.

**Key Functions:**
- `extract_data_from_binary()`: Extracts VIN or seed
- `validate_vin()`: Validates VIN format and structure
- `analyze_binary_file()`: Analyzes existing binary files

### 4. trionic8_calculator.py

Implements the Trionic8 security algorithm for key calculation.

**Key Classes and Functions:**
- `TRIONIC8_Algorithm` class: Implementation of the security algorithm
- `compute()`: Calculates key from seed value
- `compute_with_steps()`: Shows intermediate calculation steps

## Technical Details

### Communication Protocol

The communication with the Tech2 device follows this sequence:

1. **Initial Connection**: Open the serial port with binary mode enabled
2. **Initial Restart**: Send restart command (`8B 56 00 1F`)
3. **Enter Download Mode**: Send download command (`EF 56 80 3B`), wait 2 seconds, and send it again
4. **Download Verification**: Expect response (`EF 56 01 BA`)
5. **Data Chunk Reading**: Download five chunks of data with specific offsets
6. **Final Restart**: Send restart command to return the device to its normal state

### Data Structure

The data downloaded from the Tech2 device contains important information at specific offsets:

| Data | Offset | Length | Format |
|------|--------|--------|--------|
| VIN  | 0x14   | 17 bytes | ASCII string |
| Seed | 0x30   | 2 bytes  | Big-endian 16-bit integer |

### Security Key Calculation

The Trionic8 security algorithm calculates a key from the extracted seed following these steps:

1. Rotate Right by 7 bits
2. Rotate Left by 10 bits
3. Swap high/low bytes and add 0xF8DA
4. Subtract 0x3F52 from the result

Example:
- Seed: 0xFFFF
- Calculated Key: 0xB987

## Advanced Topics

### Error Handling

The tool implements robust error handling:
- Connection failures
- Timeout handling for unresponsive devices
- Retry mechanisms for data chunk downloading
- Graceful shutdown with device reboot

### Serial Port Configuration

- Baud rate: 9600
- Data bits: 8
- Stop bits: 1
- Parity: None
- Flow control: None

## Troubleshooting

### Common Issues

1. **Device Not Responding**
   - Verify correct COM port
   - Check USB connection
   - Ensure device is powered on

2. **Incomplete Data Reception**
   - Use debug mode to see detailed logs
   - Verify chunk sizes match expected values
   - Try increasing timeouts in code

3. **Download Mode Entry Failure**
   - Verify correct command sequence
   - Ensure 2-second wait after initial command
   - Check verification response

## License

This project is available under the MIT License.

## Acknowledgements

- Based on reverse engineering of the Tech2 communication protocol
- Special thanks to the Saab community for documentation and testing 
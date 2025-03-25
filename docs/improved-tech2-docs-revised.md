# Tech2 Communication Guide

This document provides a comprehensive guide for communicating with a Saab Tech2 device using Python.

## Overview

The Tech2 device communicates through a serial interface, typically appearing as COM3, COM4, or COM5 on Windows systems. This tool enables:

1. Extracting the vehicle's VIN number
2. Retrieving the security seed for key calculation  
3. Performing diagnostic operations

## System Requirements

- Python 3.6+
- Windows, Linux, or macOS
- USB-to-Serial adapter
- Tech2 device with correct cabling

## Basic Usage

The most common operation is to connect to the device and retrieve information:

```bash
python tech2_workflow_revised.py -p COM3 -d
```

Where:
- `-p COM3` specifies the COM port the device is connected to
- `-d` enables debug output

## Data Files

The following Python modules provide the core functionality:

1. `tech2_workflow_revised.py` - Main script
2. `tech2_communication_revised.py` - Communication module
3. `process_bin_revised.py` - Binary data processing
4. `trionic8_calculator.py` - Security key calculation

## Technical Details

### Serial Communication Parameters

- Baud rate: 9600
- Data bits: 8
- Parity: None
- Stop bits: 1
- Flow control: None

### Key Command Sequences

The communication protocol uses specific command sequences:

1. Initialization: `0x8B 0x56 0x00 0x1F`
2. Download mode: `0xEF 0x56 0x80 0x3B`
3. Data chunk requests - Five chunks with specific offsets
4. Security key transmission: `0x8B 0x56 0x02 0x00 [KEY_HIGH] [KEY_LOW]`

### Data Structure

The data retrieved from the Tech2 is organized as follows:

- VIN: Located at offset 0x14 (20 bytes)
- Security seed: Located at offset 0x30 (2 bytes)
- Additional diagnostic data at various offsets

## Advanced Operations

For more complex operations, the `tech2_workflow_revised.py` script supports additional options:

```bash
python tech2_workflow_revised.py -p COM3 -o data.bin
```

This command saves the raw binary data to a file for further analysis.

## Troubleshooting

Common issues include:

1. **Device not responding**
   - Ensure correct COM port is selected
   - Check USB connection
   - Verify device is powered on

2. **Incomplete data**
   - Try increasing timeout values in the code
   - Use debug mode to monitor communication
   - Verify chunk sizes match expectations

3. **Key calculation errors**
   - Ensure seed is correctly extracted
   - Verify the Trionic8 algorithm parameters

## Developer Information

The code follows an object-oriented approach with the `Tech2Communicator` class handling the core communication operations. See the main script file for complete workflow implementation. 
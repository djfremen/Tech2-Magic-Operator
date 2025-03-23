# SAAB Tech2 Implementation

## Overview
This document describes the implementation of SAAB Tech2 communication and data processing. The system uses direct port access for reliable communication with the Tech2 device.

## Project Structure
The implementation is split into several modules:

1. `tech2_workflow.py`: Main workflow script that orchestrates all operations
2. `import_serial.py`: Handles direct device communication
3. `process_bin.py`: Processes binary data and file operations
4. `trionic8_calculator.py`: Implements the security key algorithm

## Communication Method
We use direct port access via `os.open()` instead of the `serial` library for more reliable communication with the Tech2 device. This approach provides better control over the communication process and helps avoid permission issues.

### Port Configuration
```python
port_path = f"\\\\.\\{port_name}"  # Windows format
fd = os.open(port_path, os.O_RDWR | os.O_BINARY)
```

## Data Flow
1. Download data from Tech2 (import_serial.py)
2. Process binary data (process_bin.py)
3. Calculate security keys (trionic8_calculator.py)
4. Display results (tech2_workflow.py)

## Command Sequence
1. Enter download mode:
   - Send: `EF 56 80 3B`
   - Wait 2 seconds
   - Send verification: `EF 56 80 3B`
   - Read verification response

2. Read data chunks:
   - Chunk 1: 166 bytes at offset 0
   - Chunk 2: 166 bytes at offset 166
   - Chunk 3: 166 bytes at offset 332
   - Chunk 4: 166 bytes at offset 498
   - Chunk 5: 50 bytes at offset 664

3. Restart device:
   - Send: `8B 56 00 1F`

## Data Structure
The binary data contains:
- VIN (17 bytes, starting at offset 0x10)
- Seed (2 bytes, at offset 0x30)
- Calculated Key (2 bytes, at offset 0x32)

## Module Responsibilities

### tech2_workflow.py
- Main entry point
- Command line argument parsing
- Orchestrates operations between modules
- Provides user interface and output formatting

### import_serial.py
- Direct port communication
- Command sending and response reading
- Download mode management
- Device restart functionality

### process_bin.py
- Binary data parsing
- VIN extraction and validation
- Seed and key extraction
- File I/O operations

### trionic8_calculator.py
- TRIONIC8 security algorithm implementation
- Key calculation from seed
- Algorithm step verification

## Workflow Script
The `tech2_workflow.py` script provides a complete workflow:
```bash
python tech2_workflow.py -p COM5 -d -r
```

Options:
- `-p, --port`: Serial port (required)
- `-d, --download`: Download data from Tech2
- `-r, --read`: Read and process existing data file
- `-q, --quick`: Quick seed/key only mode
- `-x, --restart`: Send restart command only

## Current Status
- ✅ Direct port access implementation
- ✅ Data download working
- ✅ VIN extraction working
- ✅ Seed and key extraction working
- ✅ Data processing working
- ✅ Modular code organization
- ⏳ Upload functionality (TODO)

## Error Handling
The implementation includes robust error handling for:
- Port access issues
- Data reading timeouts
- Invalid data formats
- File operations
- Command verification

## Future Improvements
1. Implement upload functionality
2. Add data validation
3. Improve error reporting
4. Add support for different Tech2 models
5. Add unit tests
6. Add configuration file support 
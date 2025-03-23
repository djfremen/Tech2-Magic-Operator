# SAAB Tech2 Implementation

## Overview
This document describes the implementation of SAAB Tech2 communication and data processing. The system uses direct port access for reliable communication with the Tech2 device.

## Communication Method
We use direct port access via `os.open()` instead of the `serial` library for more reliable communication with the Tech2 device. This approach provides better control over the communication process and helps avoid permission issues.

### Port Configuration
```python
port_path = f"\\\\.\\{port_name}"  # Windows format
fd = os.open(port_path, os.O_RDWR | os.O_BINARY)
```

## Data Flow
1. Download data from Tech2
2. Process binary data
3. Calculate security keys
4. Upload processed data back to Tech2

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

## Workflow Script
The `tech2_workflow.py` script provides a complete workflow:
```bash
python src/tech2_workflow.py -p COM5 -d -r
```
Options:
- `-p, --port`: Serial port (required)
- `-d, --download`: Download data from Tech2
- `-r, --read`: Read and process existing data file
- `-u, --upload`: Upload processed data back to Tech2 (TODO)

## Key Files
1. `src/tech2_workflow.py`: Main workflow script
2. `src/import_serial.py`: Data download and parsing
3. `src/process_bin.py`: Binary data processing
4. `src/trionic8_calculator.py`: Security key calculation

## Current Status
- ✅ Direct port access implementation
- ✅ Data download working
- ✅ VIN extraction working
- ✅ Seed and key extraction working
- ✅ Data processing working
- ⏳ Upload functionality (TODO)

## Error Handling
The implementation includes robust error handling for:
- Port access issues
- Data reading timeouts
- Invalid data formats
- File operations

## Future Improvements
1. Implement upload functionality
2. Add data validation
3. Improve error reporting
4. Add support for different Tech2 models 
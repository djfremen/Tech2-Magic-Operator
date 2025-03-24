# Tech2 Command Implementation Guide

## Overview
This document details the low-level command implementation and protocol used by the Tech2 diagnostic tool. The protocol includes various modes of operation, security features, and command sequences.

## Communication Parameters
- Default Baud Rate: 19200
- Data Bits: 8
- Stop Bits: 2
- Parity: Even (0x4E)

## Command Modes

### Download Mode
The download mode is used for firmware updates and security operations. It requires a specific sequence of commands:

#### Enter Download Mode Command
```
[0xEF, 0x56, 0x80, 0x00]
```
- 0xEF: Command identifier
- 0x56: Subcommand
- 0x80: Download mode flag
- 0x00: Reserved

#### Exit Download Mode Command
```
[0x8B, 0x56, 0x01, 0x00]
```
- 0x8B: Command identifier
- 0x56: Subcommand
- 0x01: Exit flag
- 0x00: Reserved

### Security Access Mode
The security access mode is used for authentication and authorization. It follows a specific sequence:

1. Initial Download Mode Entry
2. Seed Request
3. Key Calculation
4. Download Mode Exit
5. Download Mode Re-entry
6. Key Transmission
7. Access Level Verification

#### Security Access Levels
The device supports multiple access levels (1-18) with different permissions:
- Level 1: Basic diagnostics
- Level 2: Enhanced diagnostics
- Level 3: Programming
- Level 4: Security operations
- Level 5: Configuration
- Level 6: Calibration
- Level 7: Special functions
- Level 8: System access
- Level 9: Advanced programming
- Level 10: Security management
- Level 11: System configuration
- Level 12: Advanced calibration
- Level 13: Special operations
- Level 14: System programming
- Level 15: Security programming
- Level 16: System security
- Level 17: Advanced security
- Level 18: Master access

## Command Sequences

### Security Access Sequence
1. Enter download mode
2. Request seed from device
3. Calculate key based on seed using CRC32 algorithm
4. Exit download mode
5. Wait for device stabilization (500ms)
6. Re-enter download mode
7. Send calculated key
8. Verify access level
9. Exit download mode

## Error Handling

### Common Error Codes
- 0x00: Success
- 0x01: Invalid command
- 0x02: Invalid parameter
- 0x03: Device busy
- 0x04: Security violation
- 0x05: Invalid seed/key
- 0x06: Access denied
- 0x07: Communication error
- 0x08: Timeout
- 0x09: Device not ready

### Retry Mechanism
- Maximum retries: 5
- Retry delay: 500ms
- Timeout: 1000ms

## Security Features

### Seed Calculation
The device uses a CRC32-based algorithm for seed calculation:
```c
// CRC32 lookup table
static const uint32_t crc32_table[256] = {
    0x00000000, 0x77073096, 0xEE0E612C, 0x990951BA,
    // ... (full table omitted for brevity)
};
```

### Key Verification
1. Device generates a random seed
2. Host calculates key using seed and algorithm
3. Device verifies key matches expected value
4. Access level is granted based on verification

## Implementation Details

### Command Structure
All commands follow this format:
```
[Command Byte, Subcommand Byte, Data Byte(s), Checksum]
```

### Checksum Calculation
```c
uint8_t calculate_checksum(uint8_t* data, size_t length) {
    uint8_t checksum = 0;
    for(size_t i = 0; i < length; i++) {
        checksum -= data[i];
    }
    return checksum;
}
```

### Response Format
Device responses follow this format:
```
[Response Byte, Status Byte, Data Byte(s), Checksum]
```

## Notes
- All timing values are critical for proper operation
- Security access must be completed before certain operations
- Device state must be verified before each major operation
- Checksums are mandatory for all commands and responses
- Access levels determine available operations

## License
This documentation is provided for educational and research purposes only. Use at your own risk.

## Contributing
Feel free to submit issues and enhancement requests! 
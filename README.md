# Tech2 Magic Operator

A Python-based tool for communicating with Saab Tech2 diagnostic devices, processing data, and calculating security keys for Trionic 8 ECUs.

## Project Structure

```
.
├── tech2_workflow.py      # Main workflow script
├── import_serial.py       # Tech2 communication functions
├── process_bin.py         # Binary data processing
├── trionic8_calculator.py # T8 security algorithm
└── saab_implementation.md # Implementation details
```

## Features

* Direct communication with Tech2 diagnostic device
* Quick seed/key calculation mode
* Full data download and processing
* VIN extraction and validation
* TRIONIC8 security key algorithm implementation
* Binary data processing and analysis

## Requirements

* Python 3.6+
* Windows OS (tested on Windows 10)

## Installation

1. Clone this repository
2. No additional dependencies required (uses built-in Python libraries)

## Usage

The tool provides several modes of operation:

### Quick Seed/Key Mode (Fastest)
```bash
python tech2_workflow.py -p COM5 -q
```

### Full Download Mode
```bash
python tech2_workflow.py -p COM5 -d
```

### Read Existing File Mode
```bash
python tech2_workflow.py -r tech2_data.bin
```

### Restart Device Mode
```bash
python tech2_workflow.py -p COM5 -x
```

## Command Line Options

* `-p, --port`: Serial port (e.g., COM5)
* `-d, --download`: Download full data from Tech2
* `-q, --quick`: Quick seed/key only (faster)
* `-r, --read`: Read and process existing data file
* `-x, --restart`: Send restart command to Tech2

## Security Key Algorithm

The TRIONIC8 security key algorithm performs the following steps:

1. Rotate right by 7 bits
2. Rotate left by 10 bits
3. Swap bytes and add 0xF8DA
4. Subtract 0x3F52

## License

MIT License - See LICENSE file for details

## About

This tool is designed for working with Saab vehicles equipped with Trionic 8 ECUs. It provides a reliable way to communicate with Tech2 diagnostic devices and calculate security access keys. 
# Tech2 Magic Operator

A Python-based tool for processing Tech2 diagnostic data and calculating security keys for Saab vehicles with Trionic 8 ECUs.

## Project Structure

```
.
├── src/                    # Source code
│   ├── process_bin.py      # Binary file processor and key calculator
│   └── trionic8_calculator.py  # T8 security algorithm
├── data/                   # Data files
│   ├── tech2_data.bin     # Raw Tech2 data
│   └── processed_data.bin  # Processed binary data
├── docs/                   # Documentation
│   ├── tech2_connection_workflow.txt
│   ├── saab_implementation_details.txt
│   └── requirements.txt
├── logs/                   # Log files
│   └── tech2mm.log
└── archive/               # Archived files
    ├── tech2_direct.py    # Direct Tech2 communication (archived)
    └── tech2_download.py  # Data download utilities (archived)
```

## Features

- Process binary data from Tech2 device
- Extract and validate VIN information
- Calculate security access keys using TRIONIC8 algorithm
- Handle binary data processing and analysis

## Requirements

- Python 3.6+
- Windows OS (tested on Windows 10)

## Installation

1. Clone this repository
2. Install required packages:
```bash
pip install -r docs/requirements.txt
```

## Usage

Process the binary data and calculate security keys:
```bash
python src/process_bin.py
```

## Security Key Algorithm

The TRIONIC8 security key algorithm performs the following steps:
1. Rotate right by 7 bits
2. Rotate left by 10 bits
3. Swap bytes and add 0xF8DA
4. Subtract 0x3F52

## License

MIT License - See LICENSE file for details 
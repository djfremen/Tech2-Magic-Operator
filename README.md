# Tech2 Magic Operator

A Python-based tool for communicating with Tech2 diagnostic devices, specifically designed for Saab vehicles with Trionic 8 ECUs.

## Features

- Download data from Tech2 device
- Read and parse VIN information
- Calculate security access keys using TRIONIC8 algorithm
- Handle device communication via COM port

## Requirements

- Python 3.6+
- Windows OS (tested on Windows 10)
- Tech2 device connected via COM port

## Installation

1. Clone this repository
2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Connect your Tech2 device
2. Download data from the device:
```bash
python tech2_download.py
```
3. Calculate security keys:
```bash
python trionic8_calculator.py
```

## Files

- `tech2_download.py` - Downloads data from Tech2 device
- `trionic8_calculator.py` - Calculates security keys using TRIONIC8 algorithm
- `requirements.txt` - Python package dependencies

## Security Key Algorithm

The TRIONIC8 security key algorithm performs the following steps:
1. Rotate right by 7 bits
2. Rotate left by 10 bits
3. Swap bytes and add 0xF8DA
4. Subtract 0x3F52

## License

MIT License - See LICENSE file for details 
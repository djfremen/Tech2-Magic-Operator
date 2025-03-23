import os
import time
import binascii

def hex_dump(data):
    if isinstance(data, bytes):
        hex_data = binascii.hexlify(data).decode('ascii')
    else:
        hex_data = binascii.hexlify(bytes(data)).decode('ascii')
    return ' '.join([hex_data[i:i+2] for i in range(0, len(hex_data), 2)])

try:
    print("Starting download process...")
    
    # Open the port directly
    port = os.open('\\\\.\\COM5', os.O_RDWR | os.O_BINARY)
    print(f"Port opened with handle: {port}")
    
    # Wait for port to stabilize
    time.sleep(1)
    
    # Send download mode command first time
    download_cmd = bytearray([0xEF, 0x56, 0x80, 0x3B])
    print(f"Sending initial download command: {hex_dump(download_cmd)}")
    os.write(port, download_cmd)
    time.sleep(2)  # Wait 2 seconds as per protocol
    
    # Send download command second time to verify
    print(f"Sending verification download command: {hex_dump(download_cmd)}")
    os.write(port, download_cmd)
    
    # Read verification response
    print("Reading verification response...")
    verify_response = os.read(port, 4)
    if verify_response:
        print(f"Verification response: {hex_dump(verify_response)}")
    else:
        print("No verification response received")
        raise Exception("Failed to verify connection")
    
    # Define all read commands
    read_commands = [
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0x00, 0xA6, 0x42]),  # Read 166 bytes at offset 0
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x00, 0xA6, 0xA6, 0x9C]),  # Read 166 bytes at offset 166
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x01, 0x4C, 0xA6, 0xF5]),  # Read 166 bytes at offset 332
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x01, 0xF2, 0xA6, 0x4F]),  # Read 166 bytes at offset 498
        bytearray([0x81, 0x5A, 0x0F, 0x2E, 0x02, 0x98, 0x32, 0x1C])   # Read 50 bytes at offset 664
    ]
    
    chunk_sizes = [169, 169, 169, 169, 53]  # Including 2-byte headers
    
    # Read all chunks
    data_buffers = []
    for i, (cmd, size) in enumerate(zip(read_commands, chunk_sizes)):
        print(f"\nReading chunk {i+1}/5: {hex_dump(cmd)}")
        os.write(port, cmd)
        chunk = os.read(port, size)
        
        if len(chunk) != size:
            print(f"Warning: Expected {size} bytes, got {len(chunk)}")
        else:
            print(f"Received {len(chunk)} bytes")
            print(f"First few bytes: {hex_dump(chunk[:10])}")
            data_buffers.append(chunk)
    
    # Combine data (excluding 2-byte headers)
    if len(data_buffers) == 5:
        combined_data = bytearray()
        combined_data.extend(data_buffers[0][2:168])  # Skip 2-byte header, get 166 bytes
        combined_data.extend(data_buffers[1][2:168])  # Skip 2-byte header, get 166 bytes
        combined_data.extend(data_buffers[2][2:168])  # Skip 2-byte header, get 166 bytes
        combined_data.extend(data_buffers[3][2:168])  # Skip 2-byte header, get 166 bytes
        combined_data.extend(data_buffers[4][2:52])   # Skip 2-byte header, get 50 bytes
        
        print(f"\nCombined data length: {len(combined_data)} bytes")
        print(f"First 50 bytes: {hex_dump(combined_data[:50])}")
        
        # Save data to file
        with open('tech2_data.bin', 'wb') as f:
            f.write(combined_data)
        print("Data saved to tech2_data.bin")
        
        # Send close download command
        close_cmd = bytearray([0xEF, 0x56, 0x80, 0x3C])
        print(f"\nSending close download command: {hex_dump(close_cmd)}")
        os.write(port, close_cmd)
        time.sleep(0.1)
        
        # Read close response
        close_response = os.read(port, 4)
        print(f"Close response: {hex_dump(close_response)}")
        
        # Send restart command to return to logo screen
        restart_cmd = bytearray([0x8B, 0x56, 0x00, 0x1F])
        print(f"\nSending restart command: {hex_dump(restart_cmd)}")
        os.write(port, restart_cmd)
        time.sleep(1)  # Wait for restart to take effect
    
    # Close the port
    os.close(port)
    print("\nPort closed")

except Exception as e:
    print(f"Error: {e}")
    try:
        os.close(port)
    except:
        pass 
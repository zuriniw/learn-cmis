# imu_logger.py - Save IMU data from both Arduino boards to a file with timestamps
import serial
import numpy as np
import csv
import os
import datetime
import time

# Set up serial ports
ARDUINO_PORT_left = '/dev/cu.usbmodem13401'
ARDUINO_PORT_right = '/dev/cu.usbmodem13201'

# Open serial ports for both boards
ser_left = serial.Serial(ARDUINO_PORT_left, 9600, timeout=0.4)
ser_right = serial.Serial(ARDUINO_PORT_right, 9600, timeout=0.4)

# Create directory for data if it doesn't exist
data_dir = 'imu_data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Create filename with timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
data_file = os.path.join(data_dir, f'imu_data_{timestamp}.csv')

def process_data(line, side):
    if not line:
        return None
    try:
        line_clean = line.replace(";", ",")
        parts = line_clean.split(',')
        values = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            for prefix in ["ACC:", "GYR:"]:
                if part.startswith(prefix):
                    part = part.replace(prefix, "")
            try:
                values.append(float(part))
            except Exception as e:
                print(f"[{side}] cannot transform: {part}")
                raise e
        if len(values) != 6:
            print(f"[{side}] length error: {len(values)}")
            return None
        acc_values = np.array(values[:3], dtype=np.float32) 
        gyr_values = np.array(values[3:], dtype=np.float32) 
        return acc_values, gyr_values
    except Exception as e:
        print(f"[{side}] fail to deal with data: {str(e)}")
        return None

# Open file for writing data
with open(data_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Write header row with timestamp
    header = [
        'L-AccX', 'L-AccY', 'L-AccZ',
        'L-GyrX', 'L-GyrY', 'L-GyrZ',
        'R-AccX', 'R-AccY', 'R-AccZ',
        'R-GyrX', 'R-GyrY', 'R-GyrZ',
        'timestamp'  # Added timestamp column
    ]
    writer.writerow(header)
    
    print(f"Logging data to {data_file}...")
    print("Press Ctrl+C to stop logging.")
    
    try:
        while True:
            # Get current timestamp
            current_time = time.time()
            
            # Read data from both boards
            line_left = ser_left.readline().decode('utf-8', errors='ignore').strip()
            line_right = ser_right.readline().decode('utf-8', errors='ignore').strip()
            
            # Process data
            processed_left = process_data(line_left, "LEFT")
            processed_right = process_data(line_right, "RIGHT")
            
            if processed_left is None or processed_right is None:
                continue
                
            acc_left, gyr_left = processed_left
            acc_right, gyr_right = processed_right
            
            # Combine data including timestamp
            combined_data = np.concatenate([acc_left, gyr_left, acc_right, gyr_right]).tolist()
            combined_data.append(current_time)  # Add timestamp to the data
            
            # Write to file
            writer.writerow(combined_data)
            
            # Print data (optional)
            print(combined_data)
            
    except KeyboardInterrupt:
        print("\nLogging stopped by user.")
    finally:
        # Close serial ports
        ser_left.close()
        ser_right.close()
        print(f"Data saved to {data_file}")

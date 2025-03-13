import serial
import threading
import numpy as np
import pickle
import socket
from collections import deque

##############################################
############# set up serial port #############
##############################################
# ARDUINO_PORT = 'COM7' # Windows-style port
ARDUINO_PORT_left = '/dev/cu.usbmodem113401'  # Mac-style port for left board
ARDUINO_PORT_right = '/dev/cu.usbmodem113201'  # Mac-style port for right board

# Open serial ports for both boards
ser_left = serial.Serial(ARDUINO_PORT_left, 9600)
ser_right = serial.Serial(ARDUINO_PORT_right, 9600)

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

######

##############################################
### load model and label encoder #############
##############################################
window_size = 50
buffer_left = deque(maxlen=window_size)
buffer_right = deque(maxlen=window_size)

# Fill buffer with 0s
for _ in range(buffer_left.maxlen):
    buffer_left.append(np.zeros(6))
for _ in range(buffer_right.maxlen):
    buffer_right.append(np.zeros(6))

model_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/example_models/b_l_o_r_u.keras'
label_encoder_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/example_models/label_encoder_b_l_o_r_u.pkl'

# prediction mapping
prediction_to_key = {
    'b': 'S',
    'r': 'D',
    'l': 'A',
    'u': 'W',
}
print("loading model and label encoder")

# Load model and label encoder
with open(model_path, 'rb') as f:
    model = pickle.load(f)
with open(label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)

print("loaded everything")

# Function to process data from the left Arduino
def process_left_data():
    count_left = 0
    while True:
        try:
            line_left = ser_left.readline().decode('utf-8').strip()
            values_left = np.array(line_left.split(',')).astype(np.float32)
            values_left[:3] = values_left[:3] / 8         # Normalize
            values_left[3:] = values_left[3:] / 4000     # Normalize
            buffer_left.append(list(values_left))
            count_left += 1

            if count_left % 10 == 0:
                raw_prediction_left = np.argmax(model.predict(np.array(buffer_left, dtype=np.float32).reshape(1, window_size * 6), verbose=0))
                prediction_left = label_encoder.inverse_transform([raw_prediction_left])
                if prediction_left[0] != 'o':
                    print(f"Left Board Prediction: {prediction_left[0]}")
                    key_left = prediction_to_key[prediction_left[0]]
                    sock.sendto(key_left.encode("utf-8"), (UDP_IP, UDP_PORT))

        except Exception as e:
            print(f"Error processing left board data: {e}")

# Function to process data from the right Arduino
def process_right_data():
    count_right = 0
    while True:
        try:
            line_right = ser_right.readline().decode('utf-8').strip()
            values_right = np.array(line_right.split(',')).astype(np.float32)
            values_right[:3] = values_right[:3] / 8         # Normalize
            values_right[3:] = values_right[3:] / 4000     # Normalize
            buffer_right.append(list(values_right))
            count_right += 1

            if count_right % 10 == 0:
                raw_prediction_right = np.argmax(model.predict(np.array(buffer_right, dtype=np.float32).reshape(1, window_size * 6), verbose=0))
                prediction_right = label_encoder.inverse_transform([raw_prediction_right])
                if prediction_right[0] != 'o':
                    print(f"Right Board Prediction: {prediction_right[0]}")
                    key_right = prediction_to_key[prediction_right[0]]
                    sock.sendto(key_right.encode("utf-8"), (UDP_IP, UDP_PORT))

        except Exception as e:
            print(f"Error processing right board data: {e}")

# Create threads for each Arduino board
left_thread = threading.Thread(target=process_left_data)
right_thread = threading.Thread(target=process_right_data)

# Start threads
left_thread.start()
right_thread.start()

# Keep the main thread alive
left_thread.join()
right_thread.join()

import serial
import threading
import numpy as np
import pickle
import socket
from collections import deque

##############################################
############# Set Up Serial Ports ############
##############################################
ARDUINO_PORT_LEFT = '/dev/cu.usbmodem113401'  # Mac-style port for left board
ARDUINO_PORT_RIGHT = '/dev/cu.usbmodem113201'  # Mac-style port for right board

# Open serial ports for both boards
ser_left = serial.Serial(ARDUINO_PORT_LEFT, 9600)
ser_right = serial.Serial(ARDUINO_PORT_RIGHT, 9600)

##############################################
############# Set Up UDP Socket ##############
##############################################
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

##############################################
######## Load Models and Label Encoders ######
##############################################
window_size = 50
buffer_left = deque(maxlen=window_size)
buffer_right = deque(maxlen=window_size)

# Fill buffers with zeros
for _ in range(window_size):
    buffer_left.append(np.zeros(6))
    buffer_right.append(np.zeros(6))

# Load separate models for left and right hands
model_path_left = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/b_l_o_r_u__1741828442-900589.keras'
model_path_right = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/f_n_t__1741844850-225251.keras'

label_encoder_path_left = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/label_encoder_b_l_o_r_u__1741828442-900589.pkl'
label_encoder_path_right = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/label_encoder_f_n_t__1741844850-225251.pkl'

print("Loading models and label encoders...")

# Load models
with open(model_path_left, 'rb') as f:
    model_left = pickle.load(f)
with open(model_path_right, 'rb') as f:
    model_right = pickle.load(f)

# Load label encoders
with open(label_encoder_path_left, 'rb') as f:
    label_encoder_left = pickle.load(f)
with open(label_encoder_path_right, 'rb') as f:
    label_encoder_right = pickle.load(f)

print("Loaded models and encoders successfully.")

##############################################
##### Define Prediction-to-Key Mapping #######
##############################################
prediction_to_key = {
    'b': 'S',  # Back
    'r': 'D',  # Right
    'l': 'A',  # Left
    'u': 'W',  # Up
    'f': 'F',  # Forward (right model)
    't': 'T',  # Trigger (right model)
    'n': 'N',  # Neutral (right model)
}

##############################################
######## Functions to Process Data ###########
##############################################

# Process left board data
def process_left_data():
    count_left = 0
    while True:
        try:
            line_left = ser_left.readline().decode('utf-8').strip()
            values_left = np.array(line_left.split(',')).astype(np.float32)

            # Normalize data
            values_left[:3] = values_left[:3] / 8  
            values_left[3:] = values_left[3:] / 4000  

            buffer_left.append(values_left)
            count_left += 1

            # Predict every 10 iterations
            if count_left % 10 == 0:
                buffer_array_left = np.array(buffer_left, dtype=np.float32).reshape(1, window_size * 6)
                raw_prediction_left = np.argmax(model_left.predict(buffer_array_left, verbose=0))
                prediction_left = label_encoder_left.inverse_transform([raw_prediction_left])[0]

                if prediction_left != 'o':  # Ignore 'o' (no action)
                    print(f"Left Board Prediction: {prediction_left}")
                    if prediction_left in prediction_to_key:
                        key_left = prediction_to_key[prediction_left]
                        sock.sendto(key_left.encode("utf-8"), (UDP_IP, UDP_PORT))
                    else:
                        print(f"Unknown prediction (left): {prediction_left}")

        except Exception as e:
            print(f"Error processing left board data: {e}")

# Process right board data
def process_right_data():
    count_right = 0
    while True:
        try:
            line_right = ser_right.readline().decode('utf-8').strip()
            values_right = np.array(line_right.split(',')).astype(np.float32)

            # Normalize data
            values_right[:3] = values_right[:3] / 8  
            values_right[3:] = values_right[3:] / 4000  

            buffer_right.append(values_right)
            count_right += 1

            # Predict every 10 iterations
            if count_right % 10 == 0:
                buffer_array_right = np.array(buffer_right, dtype=np.float32).reshape(1, window_size * 6)
                raw_prediction_right = np.argmax(model_right.predict(buffer_array_right, verbose=0))
                prediction_right = label_encoder_right.inverse_transform([raw_prediction_right])[0]

                if prediction_right != 'o':  # Ignore 'o' (no action)
                    print(f"Right Board Prediction: {prediction_right}")
                    if prediction_right in prediction_to_key:
                        key_right = prediction_to_key[prediction_right]
                        sock.sendto(key_right.encode("utf-8"), (UDP_IP, UDP_PORT))
                    else:
                        print(f"Unknown prediction (right): {prediction_right}")

        except Exception as e:
            print(f"Error processing right board data: {e}")

##############################################
####### Create and Start Threads #############
##############################################
left_thread = threading.Thread(target=process_left_data)
right_thread = threading.Thread(target=process_right_data)

# Start threads
left_thread.start()
right_thread.start()

# Keep the main thread alive
left_thread.join()
right_thread.join()

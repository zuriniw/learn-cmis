import serial
from collections import deque
import numpy as np
import pickle
import time
import socket

# You might need to change this (you can find it by looking at the port in the Arduino IDE)
# ARDUINO_PORT = 'COM7'
ARDUINO_PORT = '/dev/cu.usbmodem113401' # Mac-style port

# Open the serial port
ser = serial.Serial(ARDUINO_PORT, 9600)


#### UDP Socket Configuration ####
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
# create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
####


window_size = 50
buffer = deque(maxlen=window_size)
# fill buffer with 0s
for _ in range(buffer.maxlen):
    buffer.append(np.zeros(6))
    

absolute_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/example_models/rf_b_l_o_r_u.pkl'
# model_path = 'example_models/rf_b_l_o_r_u.pkl'
model_path = absolute_path
# load model
with open(model_path, 'rb') as f:
    model = pickle.load(f)

## there are more commands that you can use
### (L, R, A, D, W, S, +, -) ###
prediction_to_key = {
    'b': 'S',
    'r': 'D',
    'l': 'A',
    'u': 'W',
}

count = 0
while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        values = np.array(line.split(',')).astype(np.float32)
        values[:3] = values[:3] / 8
        values[3:] = values[3:] / 4000
        # buffer.append(list(values))
        buffer.append(np.array(values, dtype=np.float32))       # ensure the data type is float32
        count += 1

        # predict with the rf model
        if count % 10 == 0:  # Only predict every 10 iterations
            # prediction = model.predict(np.array(buffer, dtype=np.float32).reshape(1, window_size * 6))
            # 改为
            buffer_array = np.array([list(item) for item in buffer], dtype=np.float32)  # 先将每个元素转换为列表
            prediction = model.predict(buffer_array.reshape(1, window_size * 6))

            # time.sleep(1500 / 1000 / 100)
            if prediction[0] == 'o':
                continue
            else:
                print(f"Prediction: {prediction[0]}")
                # convert to key
                if prediction[0] in prediction_to_key:
                    key = prediction_to_key[prediction[0]]
                    # send key over udp
                    sock.sendto(key.encode("utf-8"), (UDP_IP, UDP_PORT))
    except Exception as e:
        print(e)

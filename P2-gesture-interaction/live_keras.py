import serial
from collections import deque
import numpy as np
import pickle
import time
import keras
import socket

# You might need to change this (you can find it by looking at the port in the Arduino IDE)
# ARDUINO_PORT = 'COM7' # Windows-style port
ARDUINO_PORT = '/dev/cu.usbmodem113401' # Mac-style port

# Open the serial port
ser = serial.Serial(ARDUINO_PORT, 9600)

#### You probably don't want to change this ####
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

# change to your model path
model_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/example_models/b_l_o_r_u.keras'
label_encoder_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/example_models/label_encoder_b_l_o_r_u.pkl'

## there are more commands that you can use
### (L, R, A, D, W, S, +, -) ###
## 这里需要修改 ##

prediction_to_key = {
    'b': 'S',
    'r': 'D',
    'l': 'A',
    'u': 'W',
}

print("loading model and label encoder")
# load model
with open(model_path, 'rb') as f:
    model = pickle.load(f)
with open(label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)

print("loaded everything")
count = 0
while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        values = np.array(line.split(',')).astype(np.float32)
        values[:3] = values[:3] / 8         #这里可能需要修改来让null起作用
        values[3:] = values[3:] / 4000     #这里可能需要修改来让null起作用
        buffer.append(list(values))
        count += 1

        # predict with the rf model
        if count % 10 == 0:
            raw_prediction = np.argmax(model.predict(np.array(buffer, dtype=np.float32).reshape(1, window_size * 6), verbose=0))
            prediction = label_encoder.inverse_transform([raw_prediction])
            # time.sleep(1500 / 1000 / 100)
            if prediction[0] == 'o':
                continue
            else:
                print(f"Prediction: {prediction[0]}")
                # convert to key
                key = prediction_to_key[prediction[0]]

                # send key over udp
                sock.sendto(key.encode("utf-8"), (UDP_IP, UDP_PORT))

    except Exception as e:
        print(e)

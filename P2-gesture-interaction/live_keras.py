import serial
import numpy as np
import pickle
import socket
from collections import deque
import tensorflow as tf  # 确保导入TensorFlow

##############################################
############# set up serial port #############
##############################################
# ARDUINO_PORT = 'COM7' # Windows-style port
ARDUINO_PORT_left = '/dev/cu.usbmodem13401' # Mac-style port for left board
ARDUINO_PORT_right = '/dev/cu.usbmodem13201' # Mac-style port for right board

# Open serial ports for both boards
ser_left = serial.Serial(ARDUINO_PORT_left, 9600)
ser_right = serial.Serial(ARDUINO_PORT_right, 9600)

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

##############################################
### load model and label encoder #############
##############################################
window_size = 50
buffer = deque(maxlen=window_size)

# Fill buffer with 0s (12 features for combined data from both boards)
for _ in range(window_size):
    buffer.append(np.zeros(12))

model_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/b_c_d_f_i_l_n_o_u_x_y__1742078486-1205251.keras'
label_encoder_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/label_encoder_b_c_d_f_i_l_n_o_u_x_y__1742078486-1205251.pkl'

# prediction mapping
prediction_to_key = {
    'x': 'X',
    'y': 'Y',
    'l': 'L',
    'c': 'C',
    'd': 'D',
    'u': 'U',
    'i': 'I',
    'o': 'O',
    'f': 'F',
    'b': 'B',
    'n': 'N',  # 添加了可能缺少的映射
}

print("loading model and label encoder")
# 加载模型
model = tf.keras.models.load_model(model_path)  # 使用正确的TensorFlow加载方式
with open(label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)
print("loaded everything")

def process_data(line, side):
    """带校验的数据处理函数，支持类似：
       "ACC:0.24,-0.38,0.88; GYR:4.64,-6.53,1.04"
    """
    if not line:
        return None
    try:
        # 将分号替换为逗号，统一分隔符
        line_clean = line.replace(";", ",")
        # 按逗号拆分数据
        parts = line_clean.split(',')
        values = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # 移除已知标签
            for prefix in ["ACC:", "GYR:"]:
                if part.startswith(prefix):
                    part = part.replace(prefix, "")
            try:
                values.append(float(part))
            except Exception as e:
                print(f"[{side}] 无法转换值: {part}")
                raise e
        if len(values) != 6:
            print(f"[{side}] 数据长度错误: {len(values)}")
            return None
        # 标准化处理：假设前3个为加速度，后3个为陀螺仪或EMG
        normalized = np.concatenate([
            np.array(values[:3], dtype=np.float32) / 8,
            np.array(values[3:], dtype=np.float32) / 4000
        ])
        return normalized
    except Exception as e:
        print(f"[{side}] 数据处理失败: {str(e)}")
        return None

# 主处理循环
count = 0
while True:
    try:
        # 读取双板数据（带空数据检查）
        line_left = ser_left.readline().decode('utf-8', errors='ignore').strip()
        line_right = ser_right.readline().decode('utf-8', errors='ignore').strip()
        
        # 处理数据
        processed_left = process_data(line_left, "LEFT")
        processed_right = process_data(line_right, "RIGHT")
        
        if processed_left is None or processed_right is None:
            continue
            
        # 合并特征
        combined = np.concatenate([processed_left, processed_right])
        buffer.append(combined)
        
        count += 1
        if count % 10 == 0:
            # 关键修改：正确调整输入形状为(1, 50, 12)
            prediction_input = np.array(buffer).reshape(1, window_size, 12)
            raw_prediction = model.predict(prediction_input, verbose=0)
            prediction_index = np.argmax(raw_prediction)
            prediction = label_encoder.inverse_transform([prediction_index])
            
            if prediction[0] != 'o':
                print(f"Combined Prediction: {prediction[0]}")
                if prediction[0] in prediction_to_key:
                    key = prediction_to_key[prediction[0]]
                    sock.sendto(key.encode("utf-8"), (UDP_IP, UDP_PORT))
                else:
                    print(f"Warning: No mapping for prediction '{prediction[0]}'")
    except Exception as e:
        print(f"Error in main processing loop: {e}")

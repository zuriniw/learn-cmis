import serial
from collections import deque
import numpy as np
import pickle
import time
import socket

#### 串口配置 ####
ARDUINO_PORT_LEFT = '/dev/cu.usbmodem13401'  # 左板
ARDUINO_PORT_RIGHT = '/dev/cu.usbmodem13201'  # 右板

# 配置带超时的串口（重要修复）
ser_left = serial.Serial(ARDUINO_PORT_LEFT, 9600, timeout=1)
ser_right = serial.Serial(ARDUINO_PORT_RIGHT, 9600, timeout=1)

#### UDP配置 ####
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#### 模型配置 ####
window_size = 50
buffer = deque(maxlen=window_size)

# 初始化缓冲区（重要修复）
INIT_FEATURES = 12  # 6左 + 6右
for _ in range(window_size):
    buffer.append(np.zeros(INIT_FEATURES))

# 加载模型（添加异常捕获）
try:
    model_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/rf_a_d_f_n_o_p_t_x_y__1741899264-312792.pkl'
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
except Exception as e:
    print(f"模型加载失败: {str(e)}")
    exit()

#### 键位映射 ####
prediction_to_key = {
    'd': 'S', 'a': 'A', 'x': 'X', 'y': 'Y',
    'f': 'F', 't': 'T', 'n': 'N', 'p': 'P', 'o': 'O'
}

def process_data(line, side):
    """带校验的数据处理函数"""
    if not line:
        return None
    try:
        values = np.array(line.split(',')).astype(np.float32)
        if len(values) != 6:
            print(f"[{side}] 数据长度错误: {len(values)}")
            return None
        # 标准化处理
        normalized = np.concatenate([
            values[:3]/8,    # 加速度
            values[3:]/4000  # EMG
        ])
        return normalized
    except Exception as e:
        print(f"[{side}] 数据处理失败: {str(e)}")
        return None

count = 0
while True:
    try:
        # 读取双板数据（带空数据检查）
        line_left = ser_left.readline().decode('utf-8', errors='ignore').strip()
        line_right = ser_right.readline().decode('utf-8', errors='ignore').strip()
        
        # 处理数据（重要修改）
        processed_left = process_data(line_left, "LEFT")
        processed_right = process_data(line_right, "RIGHT")
        
        if processed_left is None or processed_right is None:
            continue
            
        # 合并特征
        combined = np.concatenate([processed_left, processed_right])
        buffer.append(combined)
        
        # 预测逻辑（优化形状检查）
        if count % 10 == 0 and len(buffer) >= window_size:
            try:
                input_data = np.array(list(buffer)).reshape(1, -1)
                
                # 形状验证（关键修复）
                expected_shape = (1, window_size * INIT_FEATURES)
                if input_data.shape != expected_shape:
                    print(f"输入形状异常: 期望{expected_shape} 实际{input_data.shape}")
                    continue
                    
                prediction = model.predict(input_data)[0]
                print(f"预测结果: {prediction}")
                
                # 发送指令
                if prediction in prediction_to_key:
                    key = prediction_to_key[prediction]
                    sock.sendto(key.encode(), (UDP_IP, UDP_PORT))
            except Exception as e:
                print(f"预测异常: {str(e)}")
                
        count += 1
        
    except serial.SerialException as se:
        print(f"串口错误: {str(se)}")
        time.sleep(1)
    except Exception as e:
        print(f"全局异常: {str(e)}")
        time.sleep(0.5)
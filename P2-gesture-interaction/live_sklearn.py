import serial
import socket
import numpy as np
import pickle
from collections import deque
import time
import threading
import queue

#### 串口配置 ####
ARDUINO_PORT_LEFT = '/dev/cu.usbmodem13401'  # 左板
ARDUINO_PORT_RIGHT = '/dev/cu.usbmodem13201'  # 右板

# 优化串口通信配置：提高波特率和降低超时
ser_left = serial.Serial(ARDUINO_PORT_LEFT, 9600, timeout=0.4)
ser_right = serial.Serial(ARDUINO_PORT_RIGHT, 9600, timeout=0.4)

#### UDP配置 ####
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#### 模型配置 ####
window_size = 50
INIT_FEATURES = 12  # 6左 + 6右

# 使用线程安全的队列来存储传感器数据
data_queue = queue.Queue(maxsize=100)

# 预测结果队列
prediction_queue = queue.Queue()

# 线程间共享的buffer，使用线程锁保护
buffer = deque(maxlen=window_size)
buffer_lock = threading.Lock()

# 初始化缓冲区
for _ in range(window_size):
    buffer.append(np.zeros(INIT_FEATURES))

# 加载模型
try:
    model_path = '/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/rf_b_d_f_g_h_i_m_n_o_u__1742084517-9129019.pkl'
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print("模型加载成功")
except Exception as e:
    print(f"模型加载失败: {str(e)}")
    exit()

#### 键位映射 ####
prediction_to_key = {
    'x': 'X', 'y': 'Y', 'l': 'L', 'c': 'C',
    'd': 'D', 'u': 'U', 'i': 'I', 'o': 'O',
    'f': 'F', 'b': 'B','m': 'N', 'n': 'N'
}

# 优化数据处理函数
def process_data(line, side):
    """优化的数据处理函数"""
    if not line:
        return None
    try:
        # 使用更高效的分割方法
        line_clean = line.replace(";", ",")
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
            except Exception:
                continue
                
        if len(values) != 6:
            return None
            
        # 一次性标准化
        return np.array([
            values[0]/8, values[1]/8, values[2]/8,
            values[3]/4000, values[4]/4000, values[5]/4000
        ], dtype=np.float32)
    except Exception as e:
        print(f"[{side}] 数据处理失败: {str(e)}")
        return None

# 非阻塞读取函数
def read_serial_nonblocking(ser):
    if ser.in_waiting > 0:
        return ser.readline().decode('utf-8', errors='ignore').strip()
    return None

# 数据采集线程
def data_collection_thread():
    print("数据采集线程启动")
    while True:
        try:
            # 非阻塞读取
            line_left = read_serial_nonblocking(ser_left)
            line_right = read_serial_nonblocking(ser_right)
            
            # 如果两个传感器都有数据时才处理
            if line_left and line_right:
                processed_left = process_data(line_left, "LEFT")
                processed_right = process_data(line_right, "RIGHT")
                
                if processed_left is not None and processed_right is not None:
                    # 合并特征
                    combined = np.concatenate([processed_left, processed_right])
                    
                    # 线程安全地更新buffer
                    with buffer_lock:
                        buffer.append(combined)
            
            # 短暂休眠，减轻CPU负担            
            time.sleep(0.005)  # 5ms延迟，避免过度轮询
                
        except serial.SerialException as se:
            print(f"串口错误: {str(se)}")
            time.sleep(1)
        except Exception as e:
            print(f"数据采集异常: {str(e)}")
            time.sleep(0.5)

# 预测线程
def prediction_thread():
    print("预测线程启动")
    predict_counter = 0
    while True:
        try:
            # 控制预测频率
            predict_counter += 1
            
            if predict_counter % 10 == 0:  # 每5次循环预测一次
                # 线程安全地访问buffer
                with buffer_lock:
                    if len(buffer) >= window_size:
                        # 复制buffer以避免长时间锁定
                        buffer_copy = list(buffer)
                
                # 预测
                input_data = np.array(buffer_copy).reshape(1, -1)
                
                # 形状验证
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
            
            # 预测间隔时间
            time.sleep(0.05)  # 20ms
                
        except Exception as e:
            print(f"预测异常: {str(e)}")
            time.sleep(0.2)

# 主函数
def main():
    try:
        # 创建并启动线程
        data_thread = threading.Thread(target=data_collection_thread, daemon=True)
        pred_thread = threading.Thread(target=prediction_thread, daemon=True)
        
        data_thread.start()
        pred_thread.start()
        
        # 主线程等待，可以通过Ctrl+C终止
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("程序被用户终止")
    except Exception as e:
        print(f"主线程异常: {str(e)}")
    finally:
        # 清理资源
        try:
            ser_left.close()
            ser_right.close()
            sock.close()
        except:
            pass
        print("程序已退出")

# 启动程序
if __name__ == "__main__":
    main()

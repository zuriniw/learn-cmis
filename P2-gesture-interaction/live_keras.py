import serial
import numpy as np
import pickle
import socket
from collections import deque
import tensorflow as tf
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib as mpl
import threading

##############################################
############# set up serial port #############
##############################################

ARDUINO_PORT_left = '/dev/cu.usbmodem13401'
ARDUINO_PORT_right = '/dev/cu.usbmodem13201'

# Open serial ports for both boards
ser_left = serial.Serial(ARDUINO_PORT_left, 9600, timeout=0.4)
ser_right = serial.Serial(ARDUINO_PORT_right, 9600, timeout=0.4)

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

##############################################
### load model and label encoder #############
##############################################
window_size = 50
buffer = deque(maxlen=window_size)
buffer_lock = threading.Lock()  # 添加锁以保护共享数据

# Fill buffer with 0s (12 features for combined data from both boards)
for _ in range(window_size):
    buffer.append(np.zeros(12))

# 定义模型名称
model_name = 'b_c_d_f_g_h_n_o_u__1742102633-8481479'

# 使用模型名称动态生成路径
model_path = f'/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/{model_name}.keras'
label_encoder_path = f'/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/label_encoder_{model_name}.pkl'

# prediction mapping
prediction_to_key = {
    'a': 'A',
    'l': 'L',
    'd': 'D', 
    'u': 'U', 
    'r': 'R', 
    'o': 'O',
    'n': 'N', 
    'm': 'N', 
    'c': 'C'
}

print("loading model and label encoder")


last_prediction = None  # 上一次的预测结果
last_sent_prediction = None  # 上一次发送的预测结果
consecutive_predictions = 0  # 连续预测相同结果的次数

# 加载模型
model = tf.keras.models.load_model(model_path)
with open(label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)
print("loaded everything")

def process_data(line, side):
    """带校验的数据处理函数"""
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
                print(f"[{side}] 无法转换值: {part}")
                raise e
                
        if len(values) != 6:
            print(f"[{side}] 数据长度错误: {len(values)}")
            return None
            
        acc_values = np.array(values[:3], dtype=np.float32) / 8
        gyr_values = np.array(values[3:], dtype=np.float32) / 4000
        
        return acc_values, gyr_values
        
    except Exception as e:
        print(f"[{side}] 数据处理失败: {str(e)}")
        return None

##############################################
########### 添加可视化相关代码 ###############
##############################################

# 创建图表
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(window_size)
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5',
          '#FF9999', '#88D8B0', '#FFCC99', '#99CCFF', '#C2B3CD', '#FF6666']
labels = [
    'L-AccX', 'L-AccY', 'L-AccZ',
    'L-GyrX', 'L-GyrY', 'L-GyrZ',
    'R-AccX', 'R-AccY', 'R-AccZ',
    'R-GyrX', 'R-GyrY', 'R-GyrZ'
]

lines = []
for i in range(12):
    line, = ax.plot(x, np.zeros(window_size),
                   color=colors[i],
                   linewidth=0.8,
                   label=labels[i])
    lines.append(line)

ax.legend(ncol=3, loc='upper right', fontsize=6)
ax.set_title("Dual Board Sensor Data with Predictions", color='#333333', fontsize=10)
ax.set_facecolor('#F5F5F5')

# 添加预测文本显示
prediction_text = ax.text(0.02, 0.95, "Prediction: None", transform=ax.transAxes, 
                         fontsize=12, fontweight='bold', color='#FF4444')

def animate(frame):
    """更新图表"""
    with buffer_lock:
        data_array = np.array(buffer)
    for i in range(12):
        lines[i].set_ydata(data_array[:, i])
    
    # 更新预测文本
    if last_prediction:
        prediction_text.set_text(f"Prediction: {last_prediction}")
    
    ax.relim()
    ax.autoscale_view()
    return lines + [prediction_text]

def on_key_press(event):
    """处理键盘事件"""
    key = event.key.lower()
    if key == 'q':
        plt.close()

# 连接键盘事件
fig.canvas.mpl_connect('key_press_event', on_key_press)

##############################################
############ 数据处理线程函数 ################
##############################################
# 初始化全局变量
last_letter = None         # 上一次预测的字符
last_sent = None           # 上一次实际发送的字符
consecutive_count = 0      # 连续计数

def data_processing_thread():
    """数据处理线程"""
    global last_letter, last_sent, consecutive_count, last_prediction
    count = 0
    while True:
        try:
            # 读取双板数据
            line_left = ser_left.readline().decode('utf-8', errors='ignore').strip()
            line_right = ser_right.readline().decode('utf-8', errors='ignore').strip()
            
            # 处理数据
            processed_left = process_data(line_left, "LEFT")
            processed_right = process_data(line_right, "RIGHT")
            
            if processed_left is None or processed_right is None:
                continue

            acc_left, gyr_left = processed_left
            acc_right, gyr_right = processed_right
            combined = np.concatenate([acc_left, gyr_left, acc_right, gyr_right])

            # 更新缓冲区
            with buffer_lock:
                buffer.append(combined)
                
            count += 1

            if count % 5 == 0:
                # 获取预测输入
                with buffer_lock:
                    prediction_input = np.array(buffer).reshape(1, window_size, 12)
                
                raw_prediction = model.predict(prediction_input, verbose=0)
                prediction_index = np.argmax(raw_prediction)
                prediction = label_encoder.inverse_transform([prediction_index])
                current_pred = prediction[0]
                last_prediction = current_pred

                # 更新连续计数：若当前预测和上次一致，则计数加1，否则重置为1
                if current_pred == last_letter:
                    consecutive_count += 1
                else:
                    last_letter = current_pred
                    consecutive_count = 1

                # 根据不同字符的要求判断是否发送
                send = False
                if current_pred == 'c':
                    # c 要求连续3次，并且上次发送的不能是 c
                    if consecutive_count == 3 and last_sent != 'c':
                        send = True
                elif current_pred == 'n':
                    # n 只需一次，并且上次发送的不能是 n
                    if consecutive_count == 1 and last_sent != 'n':
                        send = True
                elif current_pred == 'o':
                    # o 需2次，并且上次发送的不能是 o
                    if consecutive_count == 2 and last_sent != 'o':
                        send = True      
                else:
                    # 其他字符要求连续2次，允许重复发送
                    if consecutive_count == 2:
                        send = True

                # 如果满足发送条件，则发送并重置连续计数
                if send:
                    last_sent = current_pred
                    print(f"Combined Prediction: {current_pred}")
                    if current_pred in prediction_to_key:
                        key = prediction_to_key[current_pred]
                        sock.sendto(key.encode("utf-8"), (UDP_IP, UDP_PORT))
                    else:
                        print(f"Warning: No mapping for prediction '{current_pred}'")
                    # 发送后重置连续计数，以便下一轮统计
                    consecutive_count = 0

        except Exception as e:
            print(f"Error in data processing thread: {e}")

##############################################
############### 主函数 #######################
##############################################

def main():
    try:
        # 创建并启动数据处理线程
        thread = threading.Thread(target=data_processing_thread, daemon=True)
        thread.start()
        
        # 启动动画
        ani = animation.FuncAnimation(fig, animate, interval=20, blit=True)
        plt.show()
        
    except KeyboardInterrupt:
        print("程序被用户终止")
    except Exception as e:
        print(f"主线程异常: {str(e)}")
    finally:
        # 清理资源
        ser_left.close()
        ser_right.close()
        sock.close()
        print("程序已退出")

if __name__ == "__main__":
    main()

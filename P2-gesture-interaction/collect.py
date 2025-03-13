import serial
from collections import deque
import numpy as np
import pickle
import time
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import matplotlib as mpl

# 双板卡配置
ARDUINO_PORT_LEFT = '/dev/cu.usbmodem13401'  # 左板
ARDUINO_PORT_RIGHT = '/dev/cu.usbmodem13201'  # 右板

# 初始化串口
ser_left = serial.Serial(ARDUINO_PORT_LEFT, 9600)
ser_right = serial.Serial(ARDUINO_PORT_RIGHT, 9600)

# 数据存储配置
recording = {"active": False, "letter": None, "file": None}
recording_lock = threading.Lock()

# 创建数据存储目录
run_timestamp = str(time.time()).replace(".", "-")
data_folder_path = os.path.join("./data", run_timestamp)
os.makedirs(data_folder_path, exist_ok=True)

# 初始化双板卡数据缓冲区（12维特征）
buffer = deque(maxlen=100)  # 存储12维特征向量
for _ in range(buffer.maxlen):
    buffer.append(np.zeros(12))  # 左6维 + 右6维

def read_serial():
    """双板卡数据采集线程"""
    while True:
        try:
            # 读取双板数据
            line_left = ser_left.readline().decode('utf-8').strip()
            line_right = ser_right.readline().decode('utf-8').strip()
            
            # 处理左板数据
            if line_left:
                values_left = np.array(line_left.split(',')).astype(np.float32)
                if len(values_left) != 6:
                    continue
                processed_left = values_left[:3]/8, values_left[3:]/4000  # 分离加速度和陀螺仪
                
            # 处理右板数据
            if line_right:
                values_right = np.array(line_right.split(',')).astype(np.float32)
                if len(values_right) != 6:
                    continue
                processed_right = values_right[:3]/8, values_right[3:]/4000
                
            # 合并双板数据（加速度+陀螺仪）
            combined = np.concatenate([
                processed_left[0],  # 左加速度
                processed_left[1],  # 左陀螺仪
                processed_right[0], # 右加速度
                processed_right[1]  # 右陀螺仪
            ])
            
            buffer.append(combined)
            
            # 数据记录
            timestamp = time.time()
            with recording_lock:
                if recording["active"] and recording["file"] is not None:
                    csv_line = ",".join(map(str, combined))
                    recording["file"].write(f"{csv_line},{timestamp}\n")
                    recording["file"].flush()
                    
        except Exception as e:
            print(f"Serial Error: {str(e)}")
            time.sleep(0.1)

# 可视化配置
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(buffer.maxlen)

# 12通道颜色和标签配置
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5',
          '#FF9999', '#88D8B0', '#FFCC99', '#99CCFF', '#C2B3CD', '#FF6666']
labels = [
    'L-AccX', 'L-AccY', 'L-AccZ', 
    'L-GyrX', 'L-GyrY', 'L-GyrZ',
    'R-AccX', 'R-AccY', 'R-AccZ',
    'R-GyrX', 'R-GyrY', 'R-GyrZ'
]

# 初始化绘图对象
lines = []
for i in range(12):
    line, = ax.plot(x, np.zeros(buffer.maxlen), 
                   color=colors[i], 
                   linewidth=0.8,
                   label=labels[i])
    lines.append(line)

ax.legend(ncol=3, loc='upper right', fontsize=6)
ax.set_title("Dual Board Sensor Data", color='#333333', fontsize=10)
ax.set_facecolor('#F5F5F5')

def animate(frame):
    """实时数据更新"""
    data_array = np.array(buffer)
    for i in range(12):
        lines[i].set_ydata(data_array[:, i])
    ax.relim()
    ax.autoscale_view()
    return lines

def on_key_press(event):
    """增强版按键处理"""
    global recording
    key = event.key.lower()
    
    if key == 'q':
        plt.close()
        return
        
    if len(key) != 1 or not key.isalpha():
        return
    
    with recording_lock:
        if not recording["active"]:
            # 开始记录
            recording["active"] = True
            recording["letter"] = key
            filename = os.path.join(data_folder_path, f"{key}.csv")
            recording["file"] = open(filename, "w")
            # 12维数据头
            header = ",".join(labels) + ",timestamp\n"
            recording["file"].write(header)
            ax.set_title(f"Recording [{key.upper()}]", color='#FF4444', fontweight='bold')
        else:
            # 停止记录
            if recording["letter"] == key:
                recording["active"] = False
                if recording["file"]:
                    recording["file"].close()
                    recording["file"] = None
                ax.set_title("Dual Board Sensor Data", color='#333333')
                
    fig.canvas.draw_idle()

# 启动系统
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()
fig.canvas.mpl_connect('key_press_event', on_key_press)
ani = animation.FuncAnimation(fig, animate, interval=20, blit=True)
plt.show()
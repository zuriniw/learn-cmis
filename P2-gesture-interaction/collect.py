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


############### data recording ################
recording = {"active": False, "letter": None, "file": None}
recording_lock = threading.Lock()

run_timestamp = str(time.time()).replace(".", "-")
data_folder_path = os.path.join("./data", run_timestamp)
os.makedirs(data_folder_path, exist_ok=True)


############### serial reading ################
ARDUINO_PORT_LEFT = '/dev/cu.usbmodem13401'  # left
ARDUINO_PORT_RIGHT = '/dev/cu.usbmodem13201'  # right

ser_left = serial.Serial(ARDUINO_PORT_LEFT, 9600)
ser_right = serial.Serial(ARDUINO_PORT_RIGHT, 9600)

############### data processing ################
buffer = deque(maxlen=100)
for _ in range(buffer.maxlen):
    buffer.append(np.zeros(12)) 

def parse_sensor_line(line, label_acc="ACC:", label_gyr="GYR:"):
    """
    input a line of sensor data: "ACC:0.24,-0.38,0.88; GYR:4.64,-6.53,1.04"
    output 2 numpy array：(acc_values, gyr_values)
    return none if parsing failed
    """
    parts = line.split(';')
    if len(parts) != 2:
        return None
    # ACC
    acc_part = parts[0].strip()
    if not acc_part.startswith(label_acc):
        return None
    acc_values_str = acc_part[len(label_acc):].strip()
    try:
        acc_values = [float(x) for x in acc_values_str.split(',') if x]
    except Exception:
        return None

    # GYR
    gyr_part = parts[1].strip()
    if not gyr_part.startswith(label_gyr):
        return None
    gyr_values_str = gyr_part[len(label_gyr):].strip()
    try:
        gyr_values = [float(x) for x in gyr_values_str.split(',') if x]
    except Exception:
        return None

    if len(acc_values) != 3 or len(gyr_values) != 3:
        return None

    # Normalize
    acc_values = np.array(acc_values, dtype=np.float32)
    gyr_values = np.array(gyr_values, dtype=np.float32)

    return acc_values, gyr_values

def read_serial():
    """double board data reading"""
    while True:
        try:
            line_left = ser_left.readline().decode('utf-8').strip()
            line_right = ser_right.readline().decode('utf-8').strip()
        
            parsed_left = parse_sensor_line(line_left)
            parsed_right = parse_sensor_line(line_right)
            
            if parsed_left is None or parsed_right is None:
                continue
            
            combined = np.concatenate([
                parsed_left[0],  # left acc
                parsed_left[1],  # left gyr
                parsed_right[0], # right acc
                parsed_right[1]  # right gyr
            ])
            
            buffer.append(combined)
            
            timestamp = time.time()
            with recording_lock:
                if recording["active"] and recording["file"] is not None:
                    csv_line = ",".join(map(str, combined))
                    recording["file"].write(f"{csv_line},{timestamp}\n")
                    recording["file"].flush()
                    
        except Exception as e:
            print(f"Serial Error: {str(e)}")
            time.sleep(0.1)

############### visualization ################
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(buffer.maxlen)

colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5',
          '#FF9999', '#88D8B0', '#FFCC99', '#99CCFF', '#C2B3CD', '#FF6666']
labels = [
    'L-AccX', 'L-AccY', 'L-AccZ', 
    'L-GyrX', 'L-GyrY', 'L-GyrZ',
    'R-AccX', 'R-AccY', 'R-AccZ',
    'R-GyrX', 'R-GyrY', 'R-GyrZ']

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
    data_array = np.array(buffer)
    normalized_data = normalize_for_display(data_array)
    for i in range(12):
        lines[i].set_ydata(normalized_data[:, i])
        ax.set_ylim(-1, 1)
    return lines

def normalize_for_display(data_array):
    result = np.copy(data_array)
    # 左侧加速度 (0,1,2)
    result[:, 0:3] = normalize_acc_gyr(data_array[:, 0:3], is_acc=True)
    # 左侧陀螺仪 (3,4,5)
    result[:, 3:6] = normalize_acc_gyr(data_array[:, 3:6], is_acc=False)
    # 右侧加速度 (6,7,8)
    result[:, 6:9] = normalize_acc_gyr(data_array[:, 6:9], is_acc=True)
    # 右侧陀螺仪 (9,10,11)
    result[:, 9:12] = normalize_acc_gyr(data_array[:, 9:12], is_acc=False)
    return result

def normalize_acc_gyr(values, is_acc=True):
    if is_acc:
        MIN_VAL, MAX_VAL = -2.0, 2.0
    else:
        MIN_VAL, MAX_VAL = -500.0, 500.0
    normalized = 2*(values - MIN_VAL) / (MAX_VAL - MIN_VAL)-1

    normalized = np.clip(normalized, -1, 1)
    
    return normalized
def on_key_press(event):
    global recording
    key = event.key.lower()
    if key == 'q':
        plt.close()
        
        return
    if len(key) != 1 or not key.isalpha():
        return
    with recording_lock:
        if not recording["active"]:
            # lets go
            recording["active"] = True
            recording["letter"] = key
            filename = os.path.join(data_folder_path, f"{key}.csv")
            recording["file"] = open(filename, "w")
            # 12 dimentions
            header = ",".join(labels) + ",timestamp\n"
            recording["file"].write(header)
            ax.set_title(f"Recording [{key.upper()}]", color='#FF4444', fontweight='bold')
        else:
            # stop
            if recording["letter"] == key:
                recording["active"] = False
                if recording["file"]:
                    recording["file"].close()
                    recording["file"] = None
                ax.set_title("Dual Board Sensor Data", color='#333333')         
    fig.canvas.draw_idle()


############### main loop ################
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()
fig.canvas.mpl_connect('key_press_event', on_key_press)
ani = animation.FuncAnimation(fig, animate, interval=20, blit=True)
plt.show()
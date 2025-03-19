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
ser_left = serial.Serial(ARDUINO_PORT_left, 9600)
ser_right = serial.Serial(ARDUINO_PORT_right, 9600)

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

##############################################
### load model and label encoder #############
##############################################
window_size = 8
buffer = deque(maxlen=window_size)
buffer_lock = threading.Lock()

# Fill buffer with 0s (12 features for combined data from both boards)
for _ in range(window_size):
    buffer.append(np.zeros(12))

model_name = 'a_b_c_d_e_f_h_i_j_k_l_m_n_o_p_r_s_t_v_w_x_y_z__1742260240_264978'
model_path = f'/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/{model_name}.keras'
label_encoder_path = f'/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/label_encoder_{model_name}.pkl'

prediction_to_key = {
    'a': 'A', # leftleft moveStep * 2.5
    's': 'S', # left moveStep * 1
    ##
    'k': 'K', # right
    'l': 'L', # rightright
    ##
    'y': 'Y',# upup
    't': 'T',# up
    ##
    'v': 'V', # down
    'b': 'B', # downdown
    #####
    'i': 'Q', # leftupleftup
    'w': 'W', # leftup
    ##
    'p': 'P', # rightuprightup
    'o': 'O', # rightup
    ##
    'x': 'X', # leftdown
    'z': 'Z', # leftdownleftdown
    ##
    'n': 'N', # rightdown
    'm': 'M', # rightdownrightdown
    ###########
    'd': 'D', # smaller
    'f': 'F', # bigger
    ### 
    'j': 'J', #ccw
    'h': 'H', #cw
    ##
    'e': 'E', # messy
    'r': 'R', # null
    ##
    'c': 'C' # confirm
}

print("loading model and label encoder")


last_prediction = None  
last_sent_prediction = None  
consecutive_predictions = 0 

model = tf.keras.models.load_model(model_path)
with open(label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)
print("loaded everything")


##############################################
########### visualization ###############
##############################################

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
ax.set_ylim(-1, 1)

prediction_text = ax.text(0.02, 0.95, "Prediction: None", transform=ax.transAxes, 
                         fontsize=12, fontweight='bold', color='#FF4444')

def animate(frame):
    """更新图表"""
    with buffer_lock:
        data_array = np.array(buffer)
    for i in range(12):
        lines[i].set_ydata(data_array[:, i])
    
    if last_prediction:
        prediction_text.set_text(f"Prediction: {last_prediction}")
    
    ax.relim()
    ax.autoscale_view()
    return lines + [prediction_text]


##############################################
############ data processing ################
##############################################
last_letter = None     
last_sent = None       
consecutive_count = 0   

def data_processing_thread():
    global last_letter, last_sent, consecutive_count, last_prediction
    count = 0
    while True:
        try:
            line_left = ser_left.readline().decode('utf-8', errors='ignore').strip()
            line_right = ser_right.readline().decode('utf-8', errors='ignore').strip()
            
            processed_left = process_data(line_left, "LEFT")
            processed_right = process_data(line_right, "RIGHT")
            
            if processed_left is None or processed_right is None:
                continue

            acc_left, gyr_left = processed_left
            acc_right, gyr_right = processed_right
            combined = np.concatenate([acc_left, gyr_left, acc_right, gyr_right])

            with buffer_lock:
                buffer.append(combined)
                
            count += 1

            if count % 5 == 0:
                with buffer_lock:
                    prediction_input = np.array(buffer).reshape(1, window_size, 12)
                
                raw_prediction = model.predict(prediction_input, verbose=0)
                prediction_index = np.argmax(raw_prediction)
                prediction = label_encoder.inverse_transform([prediction_index])
                current_pred = prediction[0]
                last_prediction = current_pred

                if current_pred == last_letter:
                    consecutive_count += 1
                else:
                    last_letter = current_pred
                    consecutive_count = 1

                send = False

                if current_pred in {'e', 'r'}:
                    if consecutive_count == 1 and last_sent not in {'e', 'r'}:
                        send = True
                elif current_pred == 'c':
                    if last_sent != 'c' and consecutive_count == 3:
                        send = True
                elif current_pred in {'h', 'j'}:
                    if last_sent not in {'h', 'j'} and consecutive_count == 2:
                        send = True
                else:
                    if last_sent != current_pred:
                        if consecutive_count == 2:
                            send = True
                    else:
                        if consecutive_count >= 1:
                            send = True

                if send:
                    last_sent = current_pred
                    print(f"Combined Prediction: {current_pred}")
                    if current_pred in prediction_to_key:
                        key = prediction_to_key[current_pred]
                        sock.sendto(key.encode("utf-8"), (UDP_IP, UDP_PORT))
                    else:
                        print(f"Warning: No mapping for prediction '{current_pred}'")
                    consecutive_count = 0

        except Exception as e:
            print(f"Error in data processing thread: {e}")

def process_data(line, side):
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
                print(f"[{side}] cannot transf: {part}")
                raise e
                
        if len(values) != 6:
            print(f"[{side}] length error: {len(values)}")
            return None
            
        acc_values = np.array(values[:3], dtype=np.float32)
        gyr_values = np.array(values[3:], dtype=np.float32)

        acc_values, gyr_values = normalize(acc_values, gyr_values)
        
        return acc_values, gyr_values
        
    except Exception as e:
        print(f"[{side}] error processing: {str(e)}")
        return None
    
############### normalization ################
def normalize(acc_values, gyr_values):
    ACC_MIN, ACC_MAX = -2.0, 2.0  
    GYR_MIN, GYR_MAX = -500.0, 500.0  
    
    norm_acc = 2 * (np.array(acc_values) - ACC_MIN) / (ACC_MAX - ACC_MIN) - 1
    norm_gyr = 2 * (np.array(gyr_values) - GYR_MIN) / (GYR_MAX - GYR_MIN) - 1
    
    norm_acc = np.clip(norm_acc, -1, 1)
    norm_gyr = np.clip(norm_gyr, -1, 1)
    
    return norm_acc, norm_gyr

##############################################
############### mainnn #######################
##############################################

def main():
    try:
        thread = threading.Thread(target=data_processing_thread, daemon=True)
        thread.start()
        
        ani = animation.FuncAnimation(fig, animate, interval=20, blit=True)
        plt.show()
        
    except KeyboardInterrupt:
        print("interrupted")
    except Exception as e:
        print(f"mainerror: {str(e)}")
    finally:
        ser_left.close()
        ser_right.close()
        sock.close()
        print("exited")

if __name__ == "__main__":
    main()

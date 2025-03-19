import numpy as np
import pickle
import tensorflow as tf
from collections import deque
import os
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.patches as mpatches
import os

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.patches as mpatches
import os

# Gesture to symbol mapping
gesture_symbols = {
    'a': '⬅️⬅️',  # leftleft
    's': '⬅️',    # left
    'k': '➡️',    # right
    'l': '➡️➡️',  # rightright
    'y': '⬆️⬆️',  # upup
    't': '⬆️',    # up
    'v': '⬇️',    # down
    'b': '⬇️⬇️',  # downdown
    'i': '↖️↖️',  # leftupleftup
    'w': '↖️',    # leftup
    'p': '↗️↗️',  # rightuprightup
    'o': '↗️',    # rightup
    'x': '↙️',    # leftdown
    'z': '↙️↙️',  # leftdownleftdown
    'n': '↘️',    # rightdown
    'm': '↘️↘️',  # rightdownrightdown
    'd': '-',   # smaller
    'f': '+',   # bigger
    'j': '↪️',    # ccw
    'h': '↩️',    # cw
    'e': '∅',    # messy
    'r': '∅',     # null
    'c': '✓'      # confirm
}

# Also provide text description for legend
gesture_descriptions = {
    'a': 'Left x2 (A)',
    's': 'Left (S)',
    'k': 'Right (K)',
    'l': 'Right x2 (L)',
    'y': 'Up x2 (Y)',
    't': 'Up (T)',
    'v': 'Down (V)',
    'b': 'Down x2 (B)',
    'i': 'Left-Up x2 (Q)',
    'w': 'Left-Up (W)',
    'p': 'Right-Up x2 (P)',
    'o': 'Right-Up (O)',
    'x': 'Left-Down (X)',
    'z': 'Left-Down x2 (Z)',
    'n': 'Right-Down (N)',
    'm': 'Right-Down x2 (M)',
    'd': 'Smaller (D)',
    'f': 'Bigger (F)',
    'j': 'Counter-Clockwise (J)',
    'h': 'Clockwise (H)',
    'e': 'Messy (E)',
    'r': 'Null (R)',
    'c': 'Confirm (C)'
}

def visualize_predictions_and_sent(predictions_file, sent_file, output_image='timeline_visualization.png'):
    """
    Create visualization of predictions and sent gestures on a shared timeline.
    Predictions shown at top, sent gestures at bottom.
    """
    # Read data files
    predictions_df = pd.read_csv(predictions_file)
    sent_df = pd.read_csv(sent_file)
    
    # Convert timestamps to relative time (seconds from start)
    min_time = min(predictions_df['timestamp'].min(), sent_df['timestamp'].min())
    predictions_df['relative_time'] = predictions_df['timestamp'] - min_time
    sent_df['relative_time'] = sent_df['timestamp'] - min_time
    
    # Get all unique prediction letters and create color map
    all_predictions = sorted(predictions_df['prediction'].unique())
    colors = plt.cm.tab20(np.linspace(0, 1, len(all_predictions)))
    color_map = dict(zip(all_predictions, colors))
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot predictions (top)
    for i, row in predictions_df.iterrows():
        color = color_map[row['prediction']]
        symbol = gesture_symbols.get(row['prediction'], row['prediction'])
        ax.scatter(row['relative_time'], 0.7, 
                  color=color, s=100, alpha=0.7)
        ax.text(row['relative_time'], 0.72, 
               symbol, ha='center', va='bottom', fontsize=9)
    
    # Plot sent data (bottom)
    for i, row in sent_df.iterrows():
        color = color_map[row['prediction']]
        symbol = gesture_symbols.get(row['prediction'], row['prediction'])
        ax.scatter(row['relative_time'], 0.3, 
                  color=color, s=150, marker='*', alpha=0.9)
        ax.text(row['relative_time'], 0.25, 
               symbol, ha='center', va='top', fontsize=12, fontweight='bold')
    
    # Add horizontal dividing line
    ax.axhline(y=0.5, color='gray', linestyle='-', alpha=0.3)
    
    # Create legend with descriptions
    patches = [mpatches.Patch(color=color_map[pred], 
                             label=f"{gesture_symbols.get(pred, pred)} {gesture_descriptions.get(pred, pred)}") 
              for pred in all_predictions]
    ax.legend(handles=patches, loc='upper right', ncol=2, fontsize=8)
    
    # Add labels
    ax.set_yticks([0.3, 0.7])
    ax.set_yticklabels(['Sent Gestures', 'Predicted Gestures'])
    ax.set_ylim(0, 1)
    ax.set_xlabel('Time (seconds from start)')
    ax.set_title('Gesture Prediction and Sent Action Timeline')
    
    # Remove y-axis lines for clarity
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    print(f"Visualization saved to {output_image}")
    
    # Show figure (if in interactive mode)
    plt.show()


# Configuration
window_size = 8
model_name = 'a_b_c_d_e_f_h_i_j_k_l_m_n_o_p_r_s_t_v_w_x_y_z__1742260240_264978'

# Attempt to find model paths (from original code)
model_path = f'/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/{model_name}.keras'
label_encoder_path = f'/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/label_encoder_{model_name}.pkl'

# Mapping of predictions to keys (from original code)
prediction_to_key = {
    'a': 'A', 's': 'S', 'k': 'K', 'l': 'L', 'y': 'Y', 't': 'T',
    'v': 'V', 'b': 'B', 'i': 'Q', 'w': 'W', 'p': 'P', 'o': 'O',
    'x': 'X', 'z': 'Z', 'n': 'N', 'm': 'M', 'd': 'D', 'f': 'F',
    'j': 'J', 'h': 'H', 'e': 'E', 'r': 'R', 'c': 'C'
}

def load_model_and_encoder():
    """Load the TensorFlow model and label encoder"""
    print(f"Loading model from {model_path}")
    print(f"Loading label encoder from {label_encoder_path}")
    
    try:
        model = tf.keras.models.load_model(model_path)
        with open(label_encoder_path, 'rb') as f:
            label_encoder = pickle.load(f)
        print("Model and label encoder loaded successfully")
        return model, label_encoder
    except Exception as e:
        print(f"Error loading model or label encoder: {e}")
        raise e

def normalize(acc_values, gyr_values):
    """Normalize accelerometer and gyroscope values to [-1,1] range"""
    # Predefined sensor data ranges
    ACC_MIN, ACC_MAX = -2.0, 2.0  # Accelerometer typically in ±2g range
    GYR_MIN, GYR_MAX = -500.0, 500.0  # Gyroscope typically in ±500 degrees/sec range
    
    # Normalize to [-1,1]
    norm_acc = 2 * (np.array(acc_values) - ACC_MIN) / (ACC_MAX - ACC_MIN) - 1
    norm_gyr = 2 * (np.array(gyr_values) - GYR_MIN) / (GYR_MAX - GYR_MIN) - 1
    
    # Ensure values are within [-1,1] range (handle outliers)
    norm_acc = np.clip(norm_acc, -1, 1)
    norm_gyr = np.clip(norm_gyr, -1, 1)
    
    return norm_acc, norm_gyr

def parse_data_line(line):
    """Parse a single line of sensor data"""
    try:
        parts = line.strip().split(',')
        if len(parts) != 13:  # 12 sensor values + timestamp
            print(f"Warning: Line has {len(parts)} values, expected 13: {line}")
            return None, None
        
        # Extract sensor values and timestamp
        sensor_values = [float(val) for val in parts[:12]]
        timestamp = float(parts[12])
        
        return sensor_values, timestamp
    except Exception as e:
        print(f"Error parsing data line: {e}")
        return None, None

def process_data(sensor_values):
    """Process sensor values into normalized feature vector"""
    # Split into left and right sensor values
    acc_left = sensor_values[0:3]
    gyr_left = sensor_values[3:6]
    acc_right = sensor_values[6:9]
    gyr_right = sensor_values[9:12]
    
    # Normalize the values
    acc_left_norm, gyr_left_norm = normalize(acc_left, gyr_left)
    acc_right_norm, gyr_right_norm = normalize(acc_right, gyr_right)
    
    # Combine into a single feature vector
    combined = np.concatenate([acc_left_norm, gyr_left_norm, acc_right_norm, gyr_right_norm])
    
    return combined

def predict_from_file(input_file, prediction_output_file, sent_output_file):
    """Process data from file and generate prediction and sent files"""
    # Load model and label encoder
    model, label_encoder = load_model_and_encoder()
    
    # Initialize the sliding window buffer
    buffer = deque(maxlen=window_size)
    for _ in range(window_size):
        buffer.append(np.zeros(12))
    
    # Initialize tracking variables
    last_letter = None         # Last predicted character
    last_sent = None           # Last actually sent character
    consecutive_count = 0      # Consecutive count
    
    # Lists to store results
    all_predictions = []
    all_sent = []
    
    # Read data from file
    data_lines = []
    timestamps = []
    
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Try to parse as data
            sensor_values, timestamp = parse_data_line(line)
            if sensor_values is not None:
                data_lines.append(sensor_values)
                timestamps.append(timestamp)
    
    print(f"Read {len(data_lines)} data lines from {input_file}")
    
    # If we have very few samples, repeat them to fill the buffer
    if len(data_lines) < window_size:
        print(f"Warning: Only {len(data_lines)} samples, which is less than window_size ({window_size})")
        print("Repeating samples to fill the buffer")
        repeat_count = window_size // len(data_lines) + 1
        original_data = data_lines.copy()
        original_timestamps = timestamps.copy()
        for _ in range(repeat_count - 1):
            data_lines.extend(original_data)
            timestamps.extend(original_timestamps)
    
    # Process each line of data
    for i, (sensor_values, timestamp) in enumerate(zip(data_lines, timestamps)):
        # Process the sensor values
        combined = process_data(sensor_values)
        
        # Update the buffer
        buffer.append(combined)
        
        # Make prediction (similar to original code's every 5 samples)
        if i % 5 == 0 or len(data_lines) < 10:
            # Get prediction input
            prediction_input = np.array(buffer).reshape(1, window_size, 12)
            
            # Make prediction
            raw_prediction = model.predict(prediction_input, verbose=0)
            prediction_index = np.argmax(raw_prediction)
            prediction = label_encoder.inverse_transform([prediction_index])
            current_pred = prediction[0]
            
            # Record prediction with timestamp
            all_predictions.append((timestamp, current_pred))
            print(f"Sample {i+1}: Predicted '{current_pred}' at time {timestamp}")
            
            # Update consecutive count
            if current_pred == last_letter:
                consecutive_count += 1
            else:
                last_letter = current_pred
                consecutive_count = 1
            
            send = False

            if current_pred in {'e', 'r'}:
                # noise
                if consecutive_count == 1 and last_sent not in {'e', 'r'}:
                    send = True
            elif current_pred == 'c':
                # confirming
                if last_sent != 'c' and consecutive_count == 3:
                    send = True
            elif current_pred in {'h', 'j'}:
                # rotating
                if last_sent not in {'h', 'j'} and consecutive_count == 2:
                    send = True
            else:
                # new
                if last_sent != current_pred:
                    if consecutive_count == 2:
                        send = True
                else:
                    # stable
                    if consecutive_count >= 1:
                        send = True


            
            # If we should "send" this prediction, record it
            if send:
                last_sent = current_pred
                print(f"  -> Sending prediction: {current_pred}")
                
                if current_pred in prediction_to_key:
                    key = prediction_to_key[current_pred]
                    all_sent.append((timestamp, current_pred, key))
                else:
                    print(f"Warning: No mapping for prediction '{current_pred}'")
                
                # Reset consecutive count after sending
                consecutive_count = 0
    
    # Write predictions to file
    with open(prediction_output_file, 'w') as f:
        f.write("timestamp,prediction\n")
        for timestamp, pred in all_predictions:
            f.write(f"{timestamp},{pred}\n")
    
    # Write sent predictions to file
    with open(sent_output_file, 'w') as f:
        f.write("timestamp,prediction,key\n")
        for timestamp, pred, key in all_sent:
            f.write(f"{timestamp},{pred},{key}\n")
    
    print(f"Processed {len(data_lines)} samples")
    print(f"Made {len(all_predictions)} predictions")
    print(f"Sent {len(all_sent)} keys")
    print(f"Results written to {prediction_output_file} and {sent_output_file}")

if __name__ == "__main__":
    input_file = 'P2-gesture-interaction/offlinetest/input_data.csv'
    prediction_output_file = 'P2-gesture-interaction/offlinetest/predictions.csv'
    sent_output_file = 'P2-gesture-interaction/offlinetest/sent.csv'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)
    
    # Track execution time
    start_time = time.time()
    predict_from_file(input_file, prediction_output_file, sent_output_file)
    elapsed_time = time.time() - start_time
    print(f"Execution completed in {elapsed_time:.2f} seconds")
    predictions_file = 'P2-gesture-interaction/offlinetest/predictions.csv'
    sent_file = 'P2-gesture-interaction/offlinetest/sent.csv'
    
    visualize_predictions_and_sent(prediction_output_file, sent_output_file)



# imu_classifier.py - Process saved IMU data and perform classification
import numpy as np
import pickle
import tensorflow as tf
import csv
from collections import deque

# Define window size for model input
window_size = 50
batch_size = 8  # Process in groups of 8 rows

# Hardcoded data file path
data_file = 'imu_data/imu_data_20250316-140530.csv'

# Load model and label encoder
model_name = 'a_c_d_g_h_k_l_m_n_o_t_u_y_z__1742146385-909744'
model_path = f'/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/{model_name}.keras'
label_encoder_path = f'/Users/ziru/Documents/GitHub/CMIS_1/P2-gesture-interaction/models/label_encoder_{model_name}.pkl'

print("Loading model and encoder...")
model = tf.keras.models.load_model(model_path)
with open(label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)
print("Model loaded successfully.")

# Mapping for prediction results
prediction_to_key = {
    'a': 'A', 'l': 'L', 'm': 'M', 'z': 'Z',
    'd': 'D', 'g': 'G', 'h': 'H', 'u': 'U',
    'y': 'Y', 't': 'T', 'o': 'O', 'n': 'N',
    'k': 'K', 'c': 'C'
}

def main():
    print(f"Reading data from {data_file}")
    
    # Read all data from file
    all_data = []
    with open(data_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Skip header row
        
        for row in reader:
            # Convert strings to floats, but only take the first 12 values (IMU data)
            try:
                # Only use the IMU data (first 12 columns), ignore timestamp
                data = [float(x) for x in row[:12]]
                all_data.append(data)
            except Exception as e:
                print(f"Error processing row: {e}")
    
    print(f"Loaded {len(all_data)} data points")
    
    # Process data in groups of 8 rows
    data_buffer = deque(maxlen=window_size)
    # Pre-fill buffer with zeros
    for _ in range(window_size):
        data_buffer.append(np.zeros(12))
    
    batch_count = 0
    for i in range(0, len(all_data), batch_size):
        batch = all_data[i:i+batch_size]
        batch_count += 1
        
        # Skip if batch is incomplete
        if len(batch) < batch_size:
            print(f"Skipping incomplete batch {batch_count}")
            continue
        
        # Update buffer with new data
        for row in batch:
            data_buffer.append(np.array(row))  # This should be just the 12 IMU values
        
        # Make prediction using current window
        data_array = np.array(list(data_buffer))  # Now this should work with consistent shapes
        prediction_input = data_array.reshape(1, window_size, 12)
        raw_prediction = model.predict(prediction_input, verbose=0)
        prediction_index = np.argmax(raw_prediction)
        prediction = label_encoder.inverse_transform([prediction_index])[0]
        
        # Get corresponding key
        key = prediction_to_key.get(prediction, "Unknown")
        
        print(f"Batch {batch_count}: Rows {i+1}-{i+batch_size} → Prediction: {prediction}, Key: {key}")
    
    print("Classification complete.")

if __name__ == "__main__":
    main()

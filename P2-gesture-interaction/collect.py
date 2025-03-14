import serial
from collections import deque
import numpy as np
import pickle
import time
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os  # for creating the data directory
import matplotlib as mpl  # if you need to adjust rcParams

# You might need to change this (you can find it by looking at the port in the Arduino IDE)
# ARDUINO_PORT = '/dev/cu.usbmodem1401' # Mac-style port
ARDUINO_PORT = 'COM7' # Windows-style port
ARDUINO_PORT = '/dev/cu.usbmodem113401' # Mac-style port

# Open the serial port
ser = serial.Serial(ARDUINO_PORT, 9600)

# Global variables for recording
recording = {"active": False, "letter": None, "file": None}
recording_lock = threading.Lock()

# Create a data folder for the current run using a timestamp.
# Replace the "." in the timestamp with a "-" for the folder name.
run_timestamp = str(time.time()).replace(".", "-")
data_folder_path = os.path.join("./data", run_timestamp)
os.makedirs(data_folder_path, exist_ok=True)

# Create a fixed-length buffer for 100 arrays of size 6
buffer = deque(maxlen=100)
# Initialize the buffer with zeros
for _ in range(buffer.maxlen):
    buffer.append(np.zeros(6))

def read_serial():
    """
    Function to continuously read data from the serial port.
    It decodes the incoming line, splits the values, normalizes them,
    and appends to the global buffer.
    Also records data to file if recording is active.
    
    NOTE: The timestamp is obtained via time.time()
    """
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:  # Only process non-empty lines
                # Convert the comma-separated string into a numpy array of floats
                values = np.array(line.split(',')).astype(np.float32)
                if len(values) != 6:
                    continue  # skip lines that don't have exactly 6 values
                # Normalize the values as in your original code
                values[:3] = values[:3] / 8
                values[3:] = values[3:] / 4000
                # Update the fixed-length buffer with new data
                buffer.append(values)

                # Record data if recording is active.
                # Timestamp is now simply time.time() (a float)
                timestamp = time.time()
                with recording_lock:
                    if recording["active"] and recording["file"] is not None:
                        csv_line = ",".join(map(str, values))
                        recording["file"].write(csv_line + f",{timestamp}\n")
                        recording["file"].flush()
        except Exception as e:
            print("Error reading serial data:", e)

# Start the serial reading in a background thread so the animation can run in the main thread.
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

# Set up the figure for live plotting
fig, ax = plt.subplots()
x = np.arange(buffer.maxlen)  # x-axis represents the index in the buffer

# Define different colors for each of the six channels
colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
labels = ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]

# Create a list to hold the line objects for each channel
lines = []
for i in range(6):
    line, = ax.plot(x, np.zeros(buffer.maxlen), color=colors[i], label=labels[i])
    lines.append(line)

ax.legend(loc='upper right')
ax.set_title("Real-time Data Visualization", color='black')
ax.set_xlabel("Buffer Index")
ax.set_ylabel("Normalized Sensor Values")

def animate(frame):
    """
    This animation function is called periodically.
    It converts the current buffer to a numpy array and updates each line.
    Then, it recalculates the axis limits to adjust for new data.
    """
    # Convert the current buffer to a numpy array of shape (100, 6)
    data_array = np.array(buffer)
    # Update each line with new y-data from the corresponding channel
    for i, line in enumerate(lines):
        line.set_ydata(data_array[:, i])
    
    # Recalculate limits and update the view
    ax.relim()              # Recalculate limits based on current data
    ax.autoscale_view()     # Autoscale the view to the new limits
    return lines

def on_key_press(event):
    """
    Handle key press events.
    
    When a letter key is pressed:
      - If the key is 'q': quit the application immediately without creating a file.
      - If not recording: start recording to a file. The file is created within the
        data folder (created once per run) and a CSV header is written.
      - If already recording with the same key: stop recording, close the file, and revert the title.
      - If already recording with a different key: the key press is ignored.
    """
    global recording
    key = event.key.lower()

    # If the key is 'q', quit the application.
    if key == 'q':
        print("Quit key pressed. Exiting application.")
        plt.close()
        return

    # Only process single alphabetical characters
    if len(key) != 1 or not key.isalpha():
        return
    
    with recording_lock:
        if not recording["active"]:
            # Start recording for this gesture
            recording["active"] = True
            recording["letter"] = key
            # Create the CSV file inside the data folder for this run.
            filename = os.path.join(data_folder_path, f"{key}.csv")
            recording["file"] = open(filename, "w")
            # Write CSV header
            recording["file"].write("acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z,timestamp\n")
            ax.set_title(f"RECORDING Gesture {key}", color='red')
            fig.canvas.draw_idle()  # Force the canvas to update the title.
            print(f"Started recording for gesture '{key}' in file: {filename}")
        else:
            if recording["letter"] == key:
                # Stop recording
                recording["active"] = False
                if recording["file"] is not None:
                    recording["file"].close()
                    recording["file"] = None
                ax.set_title("Real-time Data Visualization", color='black')
                fig.canvas.draw_idle()  # Force the canvas to update the title.
                print(f"Stopped recording for gesture '{key}'")
            else:
                print(f"Ignored key press '{key}' because recording gesture '{recording['letter']}' is active.")

# Connect our key press event handler.
fig.canvas.mpl_connect('key_press_event', on_key_press)

# Disconnect Matplotlib's default key press handler to prevent built-in key bindings (like "l")
# from interfering with our custom behavior.
if hasattr(fig.canvas.manager, 'key_press_handler_id'):
    fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)

# Create an animation that updates every 10ms.
ani = animation.FuncAnimation(fig, animate, interval=10, blit=True)

# Start the Matplotlib event loop.
plt.show()
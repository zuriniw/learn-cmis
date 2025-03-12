
# CMIS P2: Gesture-based Interaction


## Environments

### Python
Recommend using a virtual environment. Conda for example:
```bash
conda create -n cmis_P2 python=3.11
conda activate cmis_P2
python -m pip install -r requirements.txt
```
### Arduino

Install the [Arduino IDE](https://www.arduino.cc/en/software) to collect data from the Arduino boards. The boards you have are  **Arduino Nano 33 BLE Rev2**. See the 
- User Manual for **Installation and Setup**: https://docs.arduino.cc/tutorials/nano-33-ble-rev2/cheat-sheet/
- The board's **documentation**: https://docs.arduino.cc/hardware/nano-33-ble-rev2#tutorials 

Open `arduino_stream/arduino_stream.ino` in the Arduino IDE and upload it to the Arduino board, as described in the user manual. You only have to do this once. This will continuously stream the Accelerometer and Gyroscope data from the board to the serial port, which will be read by `collect.py`.

### Processing

The UI is built in Processing. Install Processing from https://processing.org/download/. 

The UI is in `UI.pde` which you can run from the Processing IDE. It will also print the statistics of the performance of your interaction in the console, i.e., average completion time, error rate, etc.


## Collect data
Press any letter key to start recording. Press the same key again to stop recording. "q" to quit. Data is saved in the `data` folder, with a timestamp in the folder name.

```bash
python collect.py
```
Remember to set the correct port for your Arduino boards.

## Train the model

Load your collected data in the `data` folder. The notebooks provide starter to train different models. 

1. Training sklearn models - `train_sklearn.ipynb`
2. Training keras models - `train_keras.ipynb`


## Predict live
Run the following to predict live for the respective models. Remember to set the correct port for your Arduino boards. 

```bash
python live_sklearn.py # for sklearn model
python live_keras.py # for keras model
```
This code contains an example of sending the predicted class to the Processing UI. Simply run `UI.pde` in Processing simultaneously with the live prediction code.


## Examples

We provide example data in `example_data` folder. You can use this data to run the model training starter code and test the prediction.

We also provide example models in `example_models` folder. You can use these models to test the live prediction without running the training yourself.
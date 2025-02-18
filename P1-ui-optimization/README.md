# P1: UI optimization

## Setup
To run this code, setup an environment with all dependencies 
installed. 

Create a new conda environment using Python 3.11.11. In the Anaconda prompt, run:
```
conda create -n cmis_P1 python=3.11.11
```

Activate the environment:
```
conda activate cmis_P1
```

The dependencies for this project are listed in the `requirements.txt` file. To install them, navigate (`cd`) into the 
folder where `requirements.txt` is located and execute:
```
pip install -r requirements.txt
```

This will install numpy, gurobipy, sklearn and PIL if you don't have the libraries installed already.

Make sure that your project is using the correct Python interpreter. In PyCharm, you can set the Python interpreter 
by going to `File > Settings > Project:[NAME] > Python Interpreter`. Select the `cmis_P1` environment as your 
Python interpreter.

If your development environment is set up correctly, you should be able to run `main.py`, which will open a window as follows: 

![run](run.PNG)


## Code structure
- `main.py` is the file that includes the **final formulation** of the optimization algorithm. The scene, auto calculation of relevance and weights of each term can be switched or tweaked in a handy way here. They are set as default parameters which have been tested and can behave good.
- `ui.py` contains the code for the user interface. The viusal has been adjusted in this file.


### Data structure
The `scene` folder contains the data that is rendered. 
- `scene-N.json` defines the questions, path to the applications and the relevance.
- `apps/apps-N.json` defines the contents for the applications that you will optimize.


## Data analysis
in the `data_analysis` folder there are scripts to visualize user test data and to compare the auto-calculated relevance and manually-labeled relevance.

## Initial Formulation
in the `initial_formulation` folder there are 3 version of legacy formulation for user tests.
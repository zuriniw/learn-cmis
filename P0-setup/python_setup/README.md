# Python setup


## Install Conda
Download and install Anaconda Distribution (https://docs.anaconda.com/anaconda/install/) 


### Create a conda environment
Start a command prompt with conda access

- **MacOS:** use the regular terminal
- **Windows:** use “Anaconda prompt”

Create a new conda environment
```
conda create -n cmu_cmis python=3.9
```

Activate th new conda environment
```
conda activate cmu_cmis 
```

### Test the environment
Create a new Python project using the [PyCharm](https://www.jetbrains.com/pycharm/) IDE. The interpreter is `<conda cmu_cmis>`.
Run `01-interpreter_test.py` to make sure environment is working.
The output should be `“Interpreter is working”`.



## Install python packages

Install python packages in conda environment (in command prompt or IDE)

### Gurobi
In the conda environment run: 
```
conda config --add channels https://conda.anaconda.org/gurobi
```

In conda environment run: 
```
conda install gurobi
```
Run `04-gurobi-test.py` in IDE to make sure this was successful. Output should be somethingt like `“Restricted license - for non-production use only - expires yyy”`


## Useful hints
Open conda prompt and type `conda info --envs` to figure out which environments you have already created


Credits: Thanks to David Lindlbauer for the example and instructions


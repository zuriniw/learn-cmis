from ui import UI 
import gurobipy as gp 
from gurobipy import GRB
import itertools
import random
import sys
import numpy as np

# Check if an argument is provided
scene_path = "scenes/scene-1.json"
if len(sys.argv) >= 2:
    scene_path = sys.argv[1]

# Loads target scene
# default: scene.json
scene_UI = UI(scene_path)

# Gets available applications
app_ids = list(scene_UI.apps.keys())

# Creates a model
m = gp.Model("ui_optimizer")

# Creates the decision variables
x = {}
for app in app_ids:
    for lod, xIdx, yIdx in itertools.product(range(scene_UI.LODS), range(scene_UI.COLS), range(scene_UI.ROWS)):
        x[app, lod, xIdx, yIdx] = m.addVar(vtype=GRB.BINARY, name="x_%s_%s_%s_%s" % (app, lod, xIdx, yIdx))

##### TODO: DEFINE OBJECTIVES AND CONSTRAINTS #####
'''
Input into interface.init_app() should be as follows:
optimal_results (list of dict): A list where each dictionary contains:
            - "name" (str): The name of the app (e.g., "weather", "time").
            - "lod" (int): Level of detail (e.g., 0 or 1).
            - "placement" (list of int): A list of two integers indicating the placement slot (e.g., [4, 4]; NOTE: This specifies the placement slot rather than the exact placement position)

Potentially relevant information can be obtained by calling scene_UI.get_info(), which returns a dictionary containing:
- "columns" (int): Number of columns in the UI grid.
- "rows" (int): Number of rows in the UI grid.
- "block_size" (int): Size of each block in the grid.
- "questions_pos" (numpy.ndarray): Position of the question panel in the UI.
- "questions_size" (numpy.ndarray): Width and height of the question panel.
- "btn_all_pos" (numpy.ndarray): Position of the "Apps" button.
- "btn_all_size" (numpy.ndarray): Width and height of the "Apps" button.
- "roi_pos" (numpy.ndarray): Position of the Region of Interest (ROI) in the UI.
- "roi_rad" (int): Radius of the Region of Interest (ROI).
- "relevance" (dict[str, float]): A dictionary mapping application names to their relevance scores.
'''

print(scene_UI.get_info())

# TODO: This is just a random term. You need to define the objective function (see comment above) and remove this.
# Clearly, this is a terrible version as it does not account for overlaps of the elements with other elements, the "Apps" button or the questions panel.
# It is only here show a simple example of how to set up the model and run the optimization.
randomTerm = 0.0
for app in app_ids:
    for lod, xIdx, yIdx in itertools.product(range(scene_UI.LODS), range(scene_UI.COLS), range(scene_UI.ROWS)):
        randomTerm += random.uniform(-1,1) * x[app, lod, xIdx, yIdx]

# Setting up the model in Gurobi and optimizing it
m.ModelSense = GRB.MAXIMIZE # depending on your objective function formulation, you may want to use GRB.MINIMIZE
m.setObjectiveN(randomTerm, index=0, weight=1)
m.update()
m.optimize() 

# Retrieving optimization results
optimal_results = []
for app in app_ids:
    for lod, xIdx, yIdx in itertools.product(range(scene_UI.LODS), range(scene_UI.COLS), range(scene_UI.ROWS)):
        if x[app, lod, xIdx, yIdx].X == 1: 
            optimal_results.append({
                "name": app, 
                "lod": lod, 
                "placement": [xIdx, yIdx] # This specifies a row and column for placement, rather than a pixel value
            })
            break 

# Starts an application with the optimized interface
# The UI knows how to display the optimal_results it receives
scene_UI.init_app(optimal_results)

import itertools
import cv2
import numpy as np
import math
import gurobipy as gp 
from gurobipy import GRB

from ui import UI

def main():
    scene = "kitchen-3.json"

    scene_UI = UI(scene)

    ui_placements = {
        "ingredients": [150, 150],
        "directions": [300, 300],
        "video": [450, 0]
    }

    # decision variables
    rows, cols = int(height/ app.size), int(width/ app_size)
    x = {}
    for app in apps:
        for xi in range(cols):
            for yi in range(rows):
                x[app, xi, yi] = m.addVar(RGB.BINARY, "x_OWEIDH",% (app, xi, yi))

    # constrain: set each element to one possition
    
    
    
    scene_UI.init_app(ui_placements)

if __name__ == "__main__":
    main()
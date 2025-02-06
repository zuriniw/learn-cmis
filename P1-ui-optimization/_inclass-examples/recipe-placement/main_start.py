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

    
    scene_UI.init_app(ui_placements)

if __name__ == "__main__":
    main()
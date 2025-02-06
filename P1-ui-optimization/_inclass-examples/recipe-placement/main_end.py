import itertools
import cv2
import numpy as np
import math
import gurobipy as gp 
from gurobipy import GRB

from ui import UI

def obj_dist(obj, x, y):
    return math.sqrt((obj[0] - x)**2 + (obj[1] - y)**2)

def get_grid_pos(app_size, x, y):
    return int((x + .5) * app_size), int((y + .5) * app_size)

def normalize_array(arr):
    min_val = np.min(arr)
    max_val = np.max(arr)
    return (arr - min_val) / (max_val - min_val) if max_val != min_val else np.zeros_like(arr)

def main2():
    scene = "kitchen-3.json"

    scene_UI = UI(scene)

    width, height, app_size, objects, apps, gaze = scene_UI.get_info()
    poi_rad = 200

    # Formulate as a grid assignment problem 
    # Compute grid
    cols, rows = int(width / app_size), int(height / app_size)

    # Calculate distance to salmon
    salmon_dist = np.zeros((cols, rows))
    for xi in range(cols): 
        for yi in range(rows):
            x, y = get_grid_pos(app_size, xi, yi)
            salmon_dist[xi,yi] = obj_dist(objects["salmon"], x, y)
    salmon_poi = salmon_dist < poi_rad
    salmon_dist = normalize_array(salmon_dist)
    #scene_UI.debug_grid(salmon_dist)

    # Calculate distance to pasta
    pasta_dist = np.zeros((cols, rows))
    for xi in range(cols): 
        for yi in range(rows):
            x, y = get_grid_pos(app_size, xi, yi)
            pasta_dist[xi,yi] = obj_dist(objects["pasta"], x, y)
    pasta_poi = pasta_dist < poi_rad
    pasta_dist = normalize_array(pasta_dist)
    #scene_UI.debug_grid(pasta_dist)

    # Calculate distance to gaze 
    gaze_dist = np.zeros((cols, rows))
    for xi in range(cols): 
        for yi in range(rows):
            x, y = get_grid_pos(app_size, xi, yi)
            gaze_dist[xi,yi] = obj_dist(gaze, x, y)
    gaze_dist = normalize_array(gaze_dist)
    #scene_UI.debug_grid(gaze_dist)

    m = gp.Model("UI Placement")

    # Add decision variables 
    x = {} 
    for app in apps: 
        for xi in range(cols):
            for yi in range(rows):
                x[app, xi, yi] = m.addVar(vtype=GRB.BINARY, name=f"{app}_{xi}_{yi}")
    m.update()

    # Add constraints 
    # Each element should be assigned once 
    for app in apps: 
        m.addConstr(sum(x[app, xi, yi] for xi in range(cols) for yi in range(rows)) == 1, f"assignment_constr_{app}")
    # Each slot can contain at most one element
    for xi in range(cols):
        for yi in range(rows):
            m.addConstr(sum(x[app, xi, yi] for app in apps) <= 1, f"capacity_constr_{xi}_{yi}")
    # Avoid getting too close to points of interest
    for xi in range(cols):
        for yi in range(rows):
            if salmon_poi[xi, yi]: 
                m.addConstr(sum(x[app, xi, yi] for app in apps) == 0, f"salmon_poi_constr_{xi}_{yi}")
            if pasta_poi[xi, yi]: 
                m.addConstr(sum(x[app, xi, yi] for app in apps) == 0, f"pasta_poi_constr_{xi}_{yi}")

    # Objectives
    # Minimize distance of salmon to recipe and ingredients
    salmonTerm = 0.0
    salmonTerm += sum(salmon_dist[xi, yi] * x["directions", xi, yi] for xi in range(cols) for yi in range(cols))
    salmonTerm += sum(salmon_dist[xi, yi] * x["ingredients", xi, yi] for xi in range(cols) for yi in range(cols))

    # Minimize distance of pasta to video
    pastaTerm = sum(pasta_dist[xi, yi] * x["video", xi, yi] for xi in range(cols) for yi in range(cols))

    # Minimize distance to gaze 
    gazeTerm = sum(gaze_dist[xi, yi] * x[app, xi, yi] for app in apps for xi in range(cols) for yi in range(cols))

    cost = salmonTerm + pastaTerm + gazeTerm

    m.setObjective(cost, GRB.MINIMIZE)
    m.optimize()

    ui_placements = {
    }
    for app in apps:
        for xi in range(cols):
            for yi in range(rows):
                if x[app, xi, yi].X == 1: 
                    ui_placements[app] = app_size * np.array([xi, yi])

    scene_UI.init_app(ui_placements)

if __name__ == "__main__":
    main2()
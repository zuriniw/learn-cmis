import json
import itertools
from PIL import Image
import cv2
import matplotlib.pyplot as plt
import numpy as np
import math
import gurobipy as gp 
from gurobipy import GRB

class UI: 
    WINDOW_WIDTH, WINDOW_HEIGHT = 750, 750
    BLOCK_SIZE = 150
    APP_WIDTH, APP_HEIGHT = 150, 150

    def __init__(self, env_path="kitchen-1.json"): 
        self.load_window()
        self.load_env(env_path) 
        self.load_apps()

    def load_window(self):
        self.window = Image.new("RGBA", (self.WINDOW_WIDTH, self.WINDOW_HEIGHT), (255, 255, 255, 0))

    def load_env(self, env_path="kitchen-1.json"):
        with open(env_path, 'r') as file:
            scene = json.load(file)

        # Environment background img
        env = Image.open(scene["img_path"])
        env = env.resize((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        self.window.paste(env, (0, 0))

        # Environment objects 
        self.objects = scene["objects"]

        # gaze
        self.gaze = scene["gaze"]

    def load_apps(self):
        self.apps = {} 

        # Directions 
        directions_path = "directions.jpg"
        app_directions = Image.open(directions_path)
        app_directions = app_directions.resize((self.APP_WIDTH, self.APP_HEIGHT))
        self.apps["directions"] = app_directions

        ingredients_path = "ingredients.jpg"
        app_ingredients = Image.open(ingredients_path)
        app_ingredients = app_ingredients.resize((self.APP_WIDTH, self.APP_HEIGHT))
        self.apps["ingredients"] = app_ingredients

        video_path = "video.jpg"
        app_video = Image.open(video_path)
        app_video = app_video.resize((self.APP_WIDTH, self.APP_HEIGHT))
        self.apps["video"] = app_video

    def place_ui(self, app_id, x, y):
        position = (x * self.BLOCK_SIZE, y * self.BLOCK_SIZE)
        self.window.paste(self.apps[app_id], position)

    def init_app(self, placements=[]):
        for placement in placements:
            self.place_ui(placement["name"], placement["placement"][0], placement["placement"][1])
        plt.imshow(self.window)
        plt.show()

def debug_circle(img, center, radius, color=(0,255,0), thickness=2):
    cv2.circle(img, center, radius, color, thickness)
    return img

def main():
    # TODO: Update scene
    scene = "kitchen-2.json"
    POI_RADIUS = 150

    interface = UI(scene)
    app_ids = list(interface.apps.keys())
    cols, rows = int(interface.WINDOW_WIDTH / interface.BLOCK_SIZE), int(interface.WINDOW_HEIGHT / interface.BLOCK_SIZE)

    m = gp.Model("ui_optimnizer")
    x = {}

    for app in app_ids:
        for xIdx, yIdx in itertools.product(range(cols), range(rows)):
            x[app, xIdx, yIdx] = m.addVar(vtype=GRB.BINARY, name="x_%s_%s_%s" % (app, xIdx, yIdx))
    
    # Constraints
    # Slot capacity 
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        lhs = 0.0
        for app in app_ids:
            lhs += x[app, xIdx, yIdx]
        m.addConstr(lhs <= 1, "c_slot_%s_%s" % (xIdx, yIdx))
    # Each element assigned once 
    for app in app_ids:
        lhs = 0.0
        for xIdx, yIdx in itertools.product(range(cols), range(rows)):
            lhs += x[app, xIdx, yIdx]
        m.addConstr(lhs == 1, "c_assignment_%s" % (app))
    # Overlap with points of interest 
    obj_ids = list(interface.objects.keys())
    ##### DEBUG: Visualize points of interest #####
    '''
    debug_img = np.array(interface.window).copy()
    for obj in obj_ids:
        pos = interface.objects[obj]
        debug_img = debug_circle(debug_img, (pos[0], pos[1]), POI_RADIUS)
    plt.imshow(debug_img)
    plt.show()
    '''
    ##########
    overlapping_poi = np.zeros((cols, rows))
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        pos_x, pos_y = (xIdx + 0.5) * interface.BLOCK_SIZE, (yIdx + 0.5) * interface.BLOCK_SIZE
        min_dist = math.inf
        for obj in obj_ids:
            pos_obj  = interface.objects[obj]
            dist = math.sqrt((pos_x - pos_obj[0]) ** 2 + (pos_y - pos_obj[1]) ** 2)
            min_dist = min(min_dist, dist)
        overlapping_poi[xIdx, yIdx] = min_dist
    ##### DEBUG: Visualize overlapping points of interest #####
    '''
    debug_img = np.array(interface.window).copy()
    debug_overlapping_poi = overlapping_poi.copy() 
    debug_overlapping_poi = np.kron(debug_overlapping_poi, np.ones((int(interface.WINDOW_WIDTH / overlapping_poi.shape[0]), 
                                                                    int(interface.WINDOW_HEIGHT / overlapping_poi.shape[1]))))
    debug_overlapping_poi = np.transpose(debug_overlapping_poi)
    # Distance from POI
    overlay = debug_overlapping_poi / debug_overlapping_poi.max()
    overlay = (overlay * 255).astype(np.uint8)
    plt.imshow(debug_img)  # Display the base image
    plt.imshow(overlay, cmap="viridis", alpha=0.6)
    plt.show()
    # Within POI_RADIUS
    overlay = debug_overlapping_poi < POI_RADIUS
    overlay = overlay / overlay.max()
    overlay = (overlay * 255).astype(np.uint8)
    plt.imshow(debug_img)  # Display the base image
    plt.imshow(overlay, cmap="viridis", alpha=0.6)
    plt.show()
    '''
    ##########
    # Constrain to avoid overlaps
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        if overlapping_poi[xIdx, yIdx] < POI_RADIUS:
            for app in app_ids:
                m.addConstr(x[app, xIdx, yIdx] <= 0, "c_poi_%s_%s_%s" % (app, xIdx, yIdx))    

    # Objectives 
    # Proximity to relevant objects 
    # Behavior: directions and ingredients should be placed in close proximity to the salmon 
    salmon_dist = np.zeros((cols, rows)) 
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        pos_x, pos_y = (xIdx + 0.5) * interface.BLOCK_SIZE, (yIdx + 0.5) * interface.BLOCK_SIZE
        salmon_pos = interface.objects["salmon"]
        salmon_dist[xIdx, yIdx] = math.sqrt((pos_x - salmon_pos[0]) ** 2 + (pos_y - salmon_pos[1]) ** 2)
    salmon_dist_min, salmon_dist_max = salmon_dist.min(), salmon_dist.max()
    salmonTerm = 0.0
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        cost = (salmon_dist[xIdx, yIdx] - salmon_dist_min) / (salmon_dist_max - salmon_dist_min)
        salmonTerm += x["directions", xIdx, yIdx] * cost
        salmonTerm += x["ingredients", xIdx, yIdx] * cost
    salmonTerm /= 2
    ##### DEBUG: Visualize distance to salmon #####
    '''
    debug_salmon_dist = salmon_dist.copy()
    debug_salmon_dist = np.kron(debug_salmon_dist, np.ones((int(interface.WINDOW_WIDTH / debug_salmon_dist.shape[0]), 
                                                                    int(interface.WINDOW_HEIGHT / debug_salmon_dist.shape[1]))))
    overlay = (debug_salmon_dist - debug_salmon_dist.min()) / (debug_salmon_dist.max() - debug_salmon_dist.min())
    overlay = (overlay * 255).astype(np.uint8)
    overlay = np.transpose(overlay)
    debug_img = np.array(interface.window).copy()
    plt.imshow(debug_img)  # Display the base image
    plt.imshow(overlay, cmap="viridis", alpha=0.6)
    plt.colorbar()
    plt.show()
    '''
    ##########
    # Behavior: video should be placed in close proximity to the pasta
    pasta_dist = np.zeros((cols, rows)) 
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        pos_x, pos_y = (xIdx + 0.5) * interface.BLOCK_SIZE, (yIdx + 0.5) * interface.BLOCK_SIZE
        pasta_pos = interface.objects["pasta"]
        pasta_dist[xIdx, yIdx] = math.sqrt((pos_x - pasta_pos[0]) ** 2 + (pos_y - pasta_pos[1]) ** 2)
    pasta_dist_min, pasta_dist_max = pasta_dist.min(), pasta_dist.max()
    pastaTerm = 0.0
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        cost = (pasta_dist[xIdx, yIdx] - pasta_dist_min) / (pasta_dist_max - pasta_dist_min)
        pastaTerm += x["video", xIdx, yIdx] * cost

    # Behavior: Minimize proximity to gaze
    gaze_dist = np.zeros((cols, rows)) 
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        pos_y = (yIdx + 0.5) * interface.BLOCK_SIZE
        gaze = interface.gaze
        gaze_dist[xIdx, yIdx] = (pos_y - gaze) ** 2
    gaze_dist_min, gaze_dist_max = gaze_dist.min(), gaze_dist.max()
    gazeTerm = 0.0
    for xIdx, yIdx in itertools.product(range(cols), range(rows)):
        cost = (gaze_dist[xIdx, yIdx] - gaze_dist_min) / (gaze_dist_max - gaze_dist_min)
        for app in app_ids: 
            gazeTerm += x[app, xIdx, yIdx] * cost
    gazeTerm /= 3


    m.ModelSense = GRB.MINIMIZE
    m.setObjectiveN(salmonTerm, index=0, weight=1)
    m.setObjectiveN(pastaTerm, index=1, weight=1)
    m.setObjectiveN(gazeTerm, index=2, weight=1)

    m.update()
    m.optimize() 

    placements = []
    for app in app_ids:
        for xIdx, yIdx in itertools.product(range(cols), range(rows)):
            if x[app, xIdx, yIdx].X > 0: 
                placements.append({
                    "name": app, 
                    "placement": (xIdx, yIdx)
                })
                break 
      
    interface.init_app(placements)

if __name__ == "__main__":
    main()
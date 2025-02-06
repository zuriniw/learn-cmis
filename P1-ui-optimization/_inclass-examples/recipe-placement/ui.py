from PIL import Image
import json
import matplotlib.pyplot as plt
import cv2
import numpy as np
import matplotlib.colors as mcolors


class UI: 
    WINDOW_WIDTH, WINDOW_HEIGHT = 750, 750
    APP_SIZE = 150

    def __init__(self, env_path="kitchen-1.json"): 
        self.load_window()
        self.load_env(env_path) 
        self.load_apps()

    def get_info(self):
        return self.WINDOW_WIDTH, self.WINDOW_HEIGHT, self.APP_SIZE, \
            self.objects, self.apps, self.gaze

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
        app_directions = app_directions.resize((self.APP_SIZE, self.APP_SIZE))
        self.apps["directions"] = app_directions

        ingredients_path = "ingredients.jpg"
        app_ingredients = Image.open(ingredients_path)
        app_ingredients = app_ingredients.resize((self.APP_SIZE, self.APP_SIZE))
        self.apps["ingredients"] = app_ingredients

        video_path = "video.jpg"
        app_video = Image.open(video_path)
        app_video = app_video.resize((self.APP_SIZE, self.APP_SIZE))
        self.apps["video"] = app_video

    def place_ui(self, app_id, x, y):
        position = (x, y)
        self.window.paste(self.apps[app_id], position)

    def debug_gaze(self, color=(255,0,0,255), thickness=2):
        img_arr = np.array(self.window)
        img_arr = cv2.circle(img_arr, self.gaze, 10, color=color, thickness=thickness)
        plt.imshow(img_arr)
        plt.show()

    def debug_grid(self, grid_values):
        overlay = grid_values.copy()
        overlay = np.kron(overlay, np.ones((int(self.WINDOW_WIDTH / overlay.shape[0]), 
                                            int(self.WINDOW_HEIGHT / overlay.shape[1]))))
        #overlay = (overlay * 255).astype(np.uint8)
        overlay = np.transpose(overlay)
        debug_img = np.array(self.window).copy() / 255.
        
        plt.imshow(debug_img) 
        plt.imshow(overlay, cmap="viridis", alpha=0.6)
        plt.colorbar()
        plt.show()

    def init_app(self, placements=[]):
        for placement in placements:
            pos = placements[placement]
            self.place_ui(placement, pos[0], pos[1])

        plt.imshow(self.window)
        plt.show()
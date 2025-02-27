import sys 
import json
import numpy as np
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk, ImageDraw
import csv
from datetime import datetime
import time
import random
import re
import os
from app import App
from PIL import Image, ImageDraw, ImageFilter

# Constants for delay. Do not change
DELAY_LOD = 150
DELAY_ALL = 1000

def gamma_correction(color, gamma=2.2, target_saturation=1.1):
    corrected = np.power(color / 255.0, 1.0 / gamma) * 255
    gray = np.mean(corrected)
    final_color = gray + (corrected - gray) * target_saturation
    return np.clip(final_color, 0, 255).astype(int)

class ListAppUI:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.i = 0
        
        self.container = tk.Frame(
            self.parent, 
            borderwidth=0,
            highlightthickness=1, highlightcolor='darkgrey', highlightbackground='darkgrey',
            width=300,
            relief="solid"
        )

        self.container.pack(pady=2, padx=10, fill="x", expand=True)
        self.container.grid_columnconfigure(0, weight=1) 
        
        self.title_label = tk.Label(
            self.container,
            text=f"{self.app.name}:",
            font=("Arial", 10, "bold"),
            fg='blue',
            background='lightgrey',
            anchor="w",
            justify="left",
            padx=5,
            pady=10
        )
        self.title_label.grid(row=0, column=0, sticky="ew") 

        self.content_label = tk.Label(
            self.container,
            text=self.app.info[self.i],
            font=("Arial", 10),
            anchor="w",
            justify="left",
            padx=5,
            pady=10
        )
        self.content_label.grid(row=1, column=0, sticky="ew")
        
        self.container.bind("<Button-1>", self.delayed_toggle_info)
        self.title_label.bind("<Button-1>", self.delayed_toggle_info)
        self.content_label.bind("<Button-1>", self.delayed_toggle_info)


    def delayed_toggle_info(self, event):
        self.container.unbind("<Button-1>")
        self.title_label.unbind("<Button-1>")
        self.content_label.unbind("<Button-1>")
        self.container.after(DELAY_ALL, self.toggle_info)

    def toggle_info(self):
        self.i = (self.i + 1) % len(self.app.info)
        self.content_label.config(text=self.app.info[self.i])
        self.container.bind("<Button-1>", self.delayed_toggle_info)
        self.title_label.bind("<Button-1>", self.delayed_toggle_info)
        self.content_label.bind("<Button-1>", self.delayed_toggle_info)

# class ListAppUI:
#     def __init__(self, parent, app):
#         self.parent = parent
#         self.app = app
#         self.i = 0 
#         self.frame = tk.Label(self.parent, text=f"{self.app.name}: {self.app.info[self.i]}", height=5, anchor="w", justify="left", borderwidth=1.5, relief="solid")
#         self.frame.pack(pady=2, padx=10, fill="x", expand=True)

#         #self.frame.bind("<Button-1>", self.toggle_info)
#         self.frame.bind("<Button-1>", self.delayed_toggle_info)

#     def delayed_toggle_info(self, event):
#         self.frame.unbind("<Button-1>") 
#         self.frame.after(DELAY_ALL, self.toggle_info)

#     #def toggle_info(self, event):
#     def toggle_info(self):
#         self.i = (self.i + 1) % len(self.app.info)
#         self.frame.config(text=f"{self.app.name}: {self.app.info[self.i]}")

#         # re-bind click
#         self.frame.bind("<Button-1>", self.delayed_toggle_info)

class MainAppUI:
    def __init__(self, parent, app, lod, placement, ui):
        self.ui = ui
        self.parent = parent
        self.app = app
        self.lod = lod
        self.placement = placement
        self.panel_dark_color = self.ui.panel_dark_color
        self.panel_lighter_color = self.ui.panel_lighter_color
        self.panel_mid_color = self.ui.panel_mid_color



        # Determine initial rowspan and colspan
        rowspan = 1 if lod < 2 else 2
        colspan = 1 if lod < 1 else 2

        self.frame = tk.Frame(self.parent, background=self.panel_lighter_color, borderwidth=0, highlightthickness=1, highlightcolor='darkgrey', highlightbackground='darkgrey', relief="solid")
        self.frame.grid(
            column=self.placement[0], 
            row=self.placement[1], 
            rowspan=rowspan, 
            columnspan=colspan, 
            sticky="nsew",
            padx=2,
            pady=2
        )

        # TITLE
        self.title_label = tk.Label(
            self.frame,
            text=f"{self.app.name}:",
            font=("Arial", 12, "bold",),
            fg = self.panel_dark_color,
            background=self.panel_mid_color,
            anchor="w",
            justify="left",
            padx=7,
        )

        self.title_label.grid(row=0, column=0, sticky="ew")

        # CONTENT
        wrap = (colspan * UI.BLOCK_SIZE) * 0.9

        self.content_label = tk.Label(
            self.frame,
            text=self.format_content(self.app.get_lod(self.lod)), 
            font=("Arial", 9),
            wraplength=wrap,
            fg = self.panel_dark_color,
            background=self.panel_lighter_color, 
            anchor="w",
            justify="left",
            padx=4,
        )
        self.content_label.grid(row=1, column=0, sticky="nsew")

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.frame.bind("<Button-1>", self.delayed_update_lod)
        self.title_label.bind("<Button-1>", self.delayed_update_lod)
        self.content_label.bind("<Button-1>", self.delayed_update_lod)


    def format_content(self, content):
        lines = content.split('\n')
        formatted_lines = []
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                formatted_lines.append(f"◍ {parts[0]}:\n└——{parts[1]}")
            else:
                formatted_lines.append(line)
        return '\n'.join(formatted_lines)

    def delayed_update_lod(self, event):
        self.frame.unbind("<Button-1>")

        # add delay before updating LoD
        self.frame.after(DELAY_LOD, self.update_lod)


    def update_lod(self):

        self.lod = (self.lod + 1) % len(self.app.info)
        
        # Update grid configuration
        rowspan = 1 if self.lod < 2 else 2
        colspan = 1 if self.lod < 1 else 2
        wrap = (colspan * UI.BLOCK_SIZE) * 0.9
        
        # Update content with same formatting as init
        self.content_label.config(
            text=self.format_content(self.app.get_lod(self.lod)), 
            wraplength=wrap
        )
            
        # Update frame grid
        self.frame.grid(
            column=self.placement[0], 
            row=self.placement[1], 
            rowspan=rowspan, 
            columnspan=colspan, 
            sticky="nsew"
        )
    
        # Lift elements
        self.frame.lift()
        self.ui.btn_all.lift()




class UILogger:
    def __init__(self):
        self.start_time = time.time()
        self.trial_end = self.start_time
        timestamp = datetime.now().strftime("%d-%H-%M")
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        self.filename = os.path.join("logs", f"{timestamp}.csv")

        with open(self.filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["QI", "Question", "Answer", "User Answer", "Correct?", "Trial Time (s)"])

        self.total_trials = 0
        self.correct_answers = 0

    def log_answer(self, qi, question, answer, user_answer):
        # Please DO NOT modify the code below

        trial_start = self.trial_end
        self.trial_end = time.time()
        trial_time = self.trial_end - trial_start

        # compare answer and user_answer, keep only numbers in the string
        numeric_answer = re.sub(r'\D', '', answer)
        numeric_user_answer = re.sub(r'\D', '', user_answer)

        is_correct = numeric_answer == numeric_user_answer
        if is_correct:
            self.correct_answers += 1

        self.total_trials += 1

        with open(self.filename, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([qi, question, answer, user_answer, is_correct, trial_time])
            # writer.writerow([qi, question, answer, user_answer, elapsed_time])

        print(f"Submit: QI={qi}, Question={question}, Answer={answer}, User Answer={user_answer}, Correct? {is_correct}, Trial Time={trial_time:.2f}s")

    def log_summary(self, questions, overlapping_poi):
        time_elapsed = time.time() - self.start_time
        summary = f"Total time elapsed: {time_elapsed:.2f}s\n"

        average_trial_time = time_elapsed / len(questions)
        summary += f"Average time per question: {average_trial_time:.2f}s\n"

        accuracy = self.correct_answers / len(questions)
        summary += f"Accuracy: {accuracy:.{2}%}\n"

        penalty = (95 - (accuracy * 100)) * 0.2
        summary += f"Penalty: {penalty:.2f}s\n"

        summary += f"Visually obstructed point of interest: {overlapping_poi}\n"
        # Additional 5 second penalty for each overlapping interface
        poi_penalty = 5 * overlapping_poi
        summary += f"Additional Penalty: {poi_penalty}s"

        average_trial_time_penalty = average_trial_time + penalty + poi_penalty
        score = f"Average time per question + penalty: {average_trial_time_penalty:.2f}s"

        with open(self.filename, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Summary", summary])
            writer.writerow(["Final Score", score])

        print("\nAll questions answered. ")
        print("\n======== SUMMARY ========")
        print(summary)
        print("\n=== FINAL SCORE ===")
        print(score)

class UI:
    LODS = 3
    WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
    BLOCK_SIZE = 100
    COLS, ROWS = 8, 6
    QUESTIONS_WIDTH, QUESTIONS_HEIGHT = 200, 200
    BTN_ALL_POS = [10, 10]
    BTN_ALL_WIDTH, BTN_ALL_HEIGHT = 80, 80

    ALL_WIDTH, ALL_HEIGHT = 150, 500
    # ALL_WIDTH, ALL_HEIGHT = 600, 500
    
    POI_RADIUS_MIN, POI_RADIUS_MAX = 50, 200
    POI_PLACEMENT_PADDING = 100
    ALL_BORDER = 1

    def __init__(self, path="scene-3.json"):
        self.load_scene(path)
        self.qi = 0 
        self.overlapping_poi = 0
        self.opening_all = False

    # Retrieves key UI-related attributes used for layout, rendering, and optimization.
    # Returns a dictionary containing:
    # - "columns" (int): Number of columns in the UI grid.
    # - "rows" (int): Number of rows in the UI grid.
    # - "block_size" (int): Size of each block in the grid in pixels.
    # - "questions_pos" (numpy.ndarray): X and Y position of the question panel in the UI in pixels.
    # - "questions_size" (numpy.ndarray): Width and height of the question panel in pixels.
    # - "btn_all_pos" (numpy.ndarray): Position of the "Apps" button to its top left corner in pixels.
    # - "btn_all_size" (numpy.ndarray): Width and height of the "Apps" button in pixels.
    # - "roi_pos" (numpy.ndarray): Position of the Region of Interest (ROI) in the UI in pixels.
    # - "roi_rad" (int): Radius of the Region of Interest (ROI) in pixels.
    # - "relevance" (dict[str, float]): A dictionary mapping application names to their relevance scores.
    def get_info(self):
        return {
            "columns": self.COLS,
            "rows": self.ROWS,
            "block_size": self.BLOCK_SIZE, 
            "questions_pos": self.q_pos,
            "questions_size": np.array([self.QUESTIONS_WIDTH, self.QUESTIONS_HEIGHT]),
            "btn_all_pos": self.BTN_ALL_POS,
            "btn_all_size": np.array([self.BTN_ALL_WIDTH, self.BTN_ALL_HEIGHT]),
            "roi_pos": self.poi_pos,
            "roi_rad": self.poi_size, 
            "relevance": self.relevance
        }

    def init_app(self, optimal_main=[], debug_poi=True):
        # Initialize the user interface window
        self.root = tk.Tk()
        self.root.geometry(f"{UI.WINDOW_WIDTH}x{UI.WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        self.root.wm_attributes('-topmost', True)

        # Initialize background image 
        self.init_background()

        # Initialize grid layout
        self.init_grid()

        # Initialize questions
        self.init_question()

        self.main_apps = {}
        self.list_apps = {}

        # Initialize main applications 
        self.init_main_apps(optimal_main)

        # Initialize all application panel
        self.init_all_panel()

        # Logging the results
        self.logging = UILogger()

        if debug_poi:
            self.debug_draw_poi()

        self.root.mainloop()

    def init_grid(self):
        # Configure the grid layout
        for r in range(UI.ROWS):
            self.root.grid_rowconfigure(r, weight=1, minsize=UI.BLOCK_SIZE)
        for c in range(UI.COLS):
            self.root.grid_columnconfigure(c, weight=1, minsize=UI.BLOCK_SIZE)

    def init_main_apps(self, main_apps):
        for main_app in main_apps:
            name = main_app["name"]
            lod = main_app["lod"]
            placement = main_app["placement"]
            if name in self.apps:
                self.main_apps[name] = MainAppUI(self.root, self.apps[name], lod, placement, self)
                self.is_ui_overlap(name, placement, lod)

    def open_all(self):
        try:
            if not self.frame_all.winfo_ismapped():
                self.frame_all.place(relx=0.5, rely=0.5, anchor="center")
            self.frame_all.lift()
        except Exception as e:
            print(f"Error opening apps panel: {e}")
            self.opening_all = False
            self.btn_all.config(state="normal")
        finally:
            self.opening_all = False
            self.btn_all.config(state="normal")

    def close_all(self):
        try:
            if self.frame_all.winfo_exists():
                self.frame_all.place_forget()
                self.frame_all.destroy()
        except Exception as e:
            print(f"Error closing apps panel: {e}")
        finally:
            self.init_all_panel()
            self.opening_all = False
            self.btn_all.config(state="normal")



    def delayed_open_all(self):
        try:
            if not self.opening_all:
                self.opening_all = True
                self.btn_all.config(state="disabled")
                self.root.after(DELAY_ALL, self.open_all)
        except Exception as e:
            print(f"Error in delayed_open_all: {e}")
            self.opening_all = False
            self.btn_all.config(state="normal")


    def init_all_panel(self):
        self.frame_all = tk.Frame(self.root, width=UI.ALL_WIDTH, height=UI.ALL_HEIGHT, borderwidth = 0, highlightthickness=1, highlightbackground='darkgrey', relief="solid", )
        # self.frame_all.pack_propagate(False)
        
        # Close button
        self.btn_close_all = tk.Button(self.frame_all, text="Close", command=self.close_all)
        self.btn_close_all.pack(pady=10)

        # title label
        self.title_label = tk.Label(self.frame_all, text="All Applications")
        self.title_label.pack(pady=0.1)

        # List Applications
        self.canvas_all_list = tk.Canvas(self.frame_all)
        self.frame_all_list = tk.Frame(self.canvas_all_list)
        self.scrollbar = tk.Scrollbar(self.frame_all, orient="vertical", command=self.canvas_all_list.yview)
        self.canvas_all_list.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas_all_list.pack(side="left", fill="both", expand=True)
        self.canvas_all_list.create_window((0, 0), window=self.frame_all_list, anchor="nw")
        def on_frame_configure(event):
            self.canvas_all_list.configure(scrollregion=self.canvas_all_list.bbox("all"))
        self.frame_all_list.bind("<Configure>", on_frame_configure)
        for name in self.apps:
            if name not in self.main_apps:
                self.list_apps[name] = ListAppUI(self.frame_all_list, self.apps[name])

        # Open button 
        #self.btn_all = tk.Button(self.root, text="Apps", command=self.open_all)
        self.btn_all = tk.Button(self.root, text="Apps", command=self.delayed_open_all)
        self.btn_all.place(x=self.BTN_ALL_POS[0], y=self.BTN_ALL_POS[1], width=self.BTN_ALL_WIDTH, height=self.BTN_ALL_HEIGHT, anchor="nw") 


    
    def init_background(self):
        img = Image.open(self.env_path)
        img = img.resize((UI.WINDOW_WIDTH, UI.WINDOW_HEIGHT), Image.LANCZOS)
        
        img_array = np.array(img)
        average_color = np.mean(img_array, axis=(0,1))
        normalized_color = gamma_correction(average_color, gamma=2.2)
        
        brightened_color = np.minimum(normalized_color * 1.2, 255).astype(int)
        darkened_color = np.maximum(normalized_color * 0.45, 2).astype(int)
        lighter_color = np.minimum(normalized_color * 1.4, 255).astype(int)
        mid_color = np.minimum(normalized_color * 1, 255).astype(int)
        
        self.panel_bg_color = '#{:02x}{:02x}{:02x}'.format(*brightened_color)
        self.panel_dark_color = '#{:02x}{:02x}{:02x}'.format(*darkened_color)
        self.panel_lighter_color = '#{:02x}{:02x}{:02x}'.format(*lighter_color)
        self.panel_mid_color = '#{:02x}{:02x}{:02x}'.format(*mid_color)


        self.env_img = ImageTk.PhotoImage(img)
        self.env_canvas = tk.Canvas(self.root, width=UI.WINDOW_WIDTH, height=UI.WINDOW_HEIGHT)
        self.env_canvas.place(x=0, y=0)
        self.env_canvas.create_image(0, 0, anchor="nw", image=self.env_img)


    def update_question(self): 
        result = self.entry_answer.get()
        self.logging.log_answer(self.qi, self.questions[self.qi]["q"], self.questions[self.qi]["a"], result)
        
        self.entry_answer.delete(0, tk.END)

        self.qi += 1
        if self.qi >= len(self.questions):
            self.logging.log_summary(self.questions, self.overlapping_poi)
            sys.exit(0)

        self.label_question.config(text=self.questions[self.qi]["q"])


    def init_question(self):
        self.frame_question = tk.Frame(self.root, width=UI.QUESTIONS_WIDTH, height=UI.QUESTIONS_HEIGHT, bg=self.panel_bg_color)
        self.frame_question.pack_propagate(False)
        self.label_question = tk.Label(self.frame_question, 
                text=self.questions[self.qi]["q"], 
                wraplength=180,
                fg = self.panel_dark_color,
                bg=self.panel_bg_color,
                padx=10, 
                pady=10)
        self.entry_answer = tk.Entry(self.frame_question, width=18,)
        self.btn_submit = tk.Button(self.frame_question, text="Submit", bg=self.panel_bg_color, command=self.update_question)
        
        self.label_question.pack(fill="x")
        self.entry_answer.pack()
        self.btn_submit.pack()
        self.frame_question.place(x=self.q_pos[0], y=self.q_pos[1], anchor="nw")
        self.color = self.panel_dark_color
        self.label_question.config(bg=self.panel_bg_color)
        # self.entry_answer.config(bg=self.panel_bg_color)
        self.btn_submit.config(bg=self.panel_bg_color, pady=0, padx=0)






    def load_scene(self, path="scene.json", shuffle_questions=True):
        try:
            with open(path, 'r') as file:
                scene = json.load(file)
            self.apps = self.load_apps(scene["app_path"])
            self.env_path = scene["env_path"]
            
            if "poi_pos" in scene: 
                self.poi_pos = np.array(scene["poi_pos"])
            else: 
                self.poi_pos = np.array([
                    random.randint(self.POI_PLACEMENT_PADDING,self.WINDOW_WIDTH - self.POI_PLACEMENT_PADDING),
                    random.randint(self.POI_PLACEMENT_PADDING,self.WINDOW_HEIGHT - self.POI_PLACEMENT_PADDING)
                ])
            if "poi_size" in scene:
                self.poi_size = scene["poi_size"]
            else: 
                self.poi_size = random.randint(self.POI_RADIUS_MIN, self.POI_RADIUS_MAX)
            
            if "q_pos" in scene: 
                self.q_pos = np.array(scene["q_pos"])
            else: 
                valid_placements = self.get_valid_question_placements()
                self.q_pos = self.BLOCK_SIZE * np.array(valid_placements[
                    random.randint(0, len(valid_placements) - 1)
                ])
                #self.q_pos = self.BLOCK_SIZE * np.array([
                #    random.randint(0,self.COLS - 2),
                #    random.randint(0,self.ROWS - 2)
                #])
                print(self.q_pos)
            
            self.init_relevance(scene["relevance"])
            
            self.questions = self.load_questions(scene["questions"])
            if shuffle_questions:
                random.shuffle(self.questions)
        
        except FileNotFoundError:
            print(f"File not found: {path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {path}")
            sys.exit(1)

    def load_questions(self, questions):
        num_questions = len(questions)
        for qi in range(num_questions):
            app = self.apps[questions[qi]["app"]]
            a = app.info[questions[qi]["lod"]]
            questions[qi]["a"] = a
        return questions
        
    def load_apps(self, path="apps.json"):
        try:
            apps = {}
            with open(path, 'r') as file:
                data = json.load(file)
                for entry in data: 
                    apps[entry["app"]] = App(entry["app"], entry["info"])
            return apps
        except FileNotFoundError:
            print(f"File not found: {path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {path}")
            sys.exit(1)
        
    def init_relevance(self, relevance):
        self.relevance = relevance
        for app in self.apps.keys():
            if app not in self.relevance:
                self.relevance[app] = 0.0

    def debug_draw_poi(self): 
        img = Image.open(self.env_path)
        img = img.resize((UI.WINDOW_WIDTH, UI.WINDOW_HEIGHT), Image.LANCZOS)

        blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
        
        mask = Image.new('L', (UI.WINDOW_WIDTH, UI.WINDOW_HEIGHT), 0)
        draw = ImageDraw.Draw(mask)
        
        x0 = self.poi_pos[0] - self.poi_size
        y0 = self.poi_pos[1] - self.poi_size
        x1 = self.poi_pos[0] + self.poi_size
        y1 = self.poi_pos[1] + self.poi_size
        
        draw.ellipse([x0, y0, x1, y1], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=30)) 
        
        # merge
        final = Image.composite(img, blurred, mask)
        
        # transform to photoimage and display
        self.env_img = ImageTk.PhotoImage(final)
        self.env_canvas.create_image(0, 0, anchor="nw", image=self.env_img)

        self.env_canvas.create_oval(x0, y0, x1, y1, outline="grey", width=0.5, dash=5)


    def circle_rectangle_overlap(self, circle_x, circle_y, circle_radius, rect_x, rect_y, rect_width, rect_height):
        # Find the closest point on the rectangle to the circle's center
        closest_x = max(rect_x, min(circle_x, rect_x + rect_width))
        closest_y = max(rect_y, min(circle_y, rect_y + rect_height))

        # Calculate the distance between the circle's center and the closest point
        distance_x = circle_x - closest_x
        distance_y = circle_y - closest_y
        distance_squared = distance_x**2 + distance_y**2

        # Check if the distance is less than or equal to the circle's radius
        return distance_squared <= circle_radius**2

    def is_ui_overlap(self, name, placement, lod):
        circle_x, circle_y, circle_radius = self.poi_pos[0], self.poi_pos[1], self.poi_size
        rect_x, rect_y = placement[0] * self.BLOCK_SIZE, placement[1] * self.BLOCK_SIZE
        rect_width, rect_height = self.BLOCK_SIZE, self.BLOCK_SIZE
        if lod > 0:
            rect_width = 2 * self.BLOCK_SIZE
        if lod > 1: 
            rect_height = 2 * self.BLOCK_SIZE
        is_overlap = self.circle_rectangle_overlap(circle_x, circle_y, circle_radius, rect_x, rect_y, rect_width, rect_height)
        if is_overlap:
            self.overlapping_poi += 1
        #print(name, "overlapping poi:", is_overlap)

    def is_question_overlap(self, placement):
        # Check if the question panel overlaps with the "All Apps" button at position [0,0]
        if placement == [0, 0]:
            return True

        # Check if the question panel overlaps with the point of interest
        circle_x, circle_y, circle_radius = self.poi_pos[0], self.poi_pos[1], self.poi_size
        rect_x, rect_y = placement[0] * self.BLOCK_SIZE, placement[1] * self.BLOCK_SIZE
        rect_width = 2 * self.BLOCK_SIZE
        rect_height = 2 * self.BLOCK_SIZE
        return self.circle_rectangle_overlap(circle_x, circle_y, circle_radius, rect_x, rect_y, rect_width, rect_height)

    def get_valid_question_placements(self):
        valid_pos = []
        for xIdx in range(self.COLS - 2):
            for yIdx in range(self.ROWS - 2):
                if not self.is_question_overlap([xIdx, yIdx]):
                    valid_pos.append([xIdx, yIdx])
        return valid_pos
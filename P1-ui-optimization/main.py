from ui import UI 
import gurobipy as gp 
from gurobipy import GRB
import itertools
import random
import sys
import numpy as np
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.preprocessing import MinMaxScaler  # 归一化工具

########################################################
#############   objective func weights   ###############
########################################################

rewards = [1, 3, 1]
poi_pan = 0.3 
is_auto_rele = True

'''
 m.setObjective(
    rewards[0]*relevanceTerm + 
    rewards[1]*questionProximityTerm +
    rewards[2]*lodRewardTerm +
    roiAvoidanceTerm,
    GRB.MAXIMIZE
)
'''
########################################################
#############    some todos and hints    ###############
########################################################
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

os.chdir(os.path.dirname(os.path.abspath(__file__)))
scene_path = "scenes/scene-2.json"
if len(sys.argv) >= 2:
    scene_path = sys.argv[1]

scene_UI = UI(scene_path)
app_ids = list(scene_UI.apps.keys())


########################################################
#############           helper         ################# 
########################################################


def calculate_automated_relevance(scene):
    custom_stop_words = ['current', 'today']
    all_stop_words = list(ENGLISH_STOP_WORDS) + custom_stop_words

    relevance = {}
    scores_list = []
    for app_name, app in scene.apps.items():
        app_infos = []
        seen = set()
        for i in range(len(app.info)):
            # retrieve raw
            raw_info = app.get_lod(i)
            # split
        for line in raw_info.split('\n'):
            clean_info = re.sub(r'\([^)]*\)|\d|:', '', line).strip()
            if clean_info not in seen:
                app_infos.append(clean_info)
                seen.add(clean_info)
                
        app_info = " ".join(app_infos) + " " + app_name
        # print(f'{app_name}\n  {app_info} \n---------')
        all_questions = [q["q"] for q in scene.questions] + [q["app"] for q in scene.questions]
        questions_text = " ".join(all_questions)
        ##  calculate similarity ##
        all_texts = [app_info, questions_text]
        vectorizer = TfidfVectorizer(stop_words=all_stop_words)
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2]).flatten()[0]
        scores_list.append((app_name, similarity_score))
    # normalization
    if scores_list:
        scaler = MinMaxScaler()
        normalized_scores = scaler.fit_transform([[score] for _, score in scores_list])
        for i, (app_name, _) in enumerate(scores_list):
            relevance[app_name] = normalized_scores[i, 0]
    return relevance

def normalize_terms():
    # 1// question proximity: max and min distance
    all_distances = []
    for xIdx in range(scene_UI.COLS):
        for yIdx in range(scene_UI.ROWS):
            for lod in range(scene_UI.LODS):
                if lod == 0:
                    pos = np.array([(xIdx + 0.5) * grid_a, 
                                  (yIdx + 0.5) * grid_a])
                elif lod == 1:
                    pos = np.array([(xIdx + 1.0) * grid_a, 
                                  (yIdx + 0.5) * grid_a])
                else:
                    pos = np.array([(xIdx + 1.0) * grid_a, 
                                  (yIdx + 1.0) * grid_a])
                dist = np.sqrt(np.sum((pos - q_center)**2))
                all_distances.append(dist)
    
    max_dist = max(all_distances)
    min_dist = min(all_distances)
    
    # 2// ROI: max distance
    max_roi_dist = np.sqrt(scene_UI.COLS**2 + scene_UI.ROWS**2) * grid_a   
    return {
        'q_max_dist': max_dist,
        'q_min_dist': min_dist,
        'max_roi_dist': max_roi_dist
    }

########################################################
#############        init some info      ###############
########################################################

info = scene_UI.get_info()


q_center = np.array([
    info["questions_pos"][0] + info["questions_size"][0]/2, 
    info["questions_pos"][1] + info["questions_size"][1]/2  
])
grid_a = info["block_size"]
circle_x, circle_y = info["roi_pos"][0], info["roi_pos"][1]
circle_radius = info["roi_rad"]
bpos = info["btn_all_pos"]
bsize = info["btn_all_size"]
qpos = info["questions_pos"]
qsize = info["questions_size"] 

rele = calculate_automated_relevance(scene_UI) if is_auto_rele else info["relevance"]
sorted_rele = dict(sorted(rele.items(), key=lambda item: item[1], reverse=True))
print(sorted_rele)  


########################################################
#############        init model      ################### 
########################################################

m = gp.Model("ui_optimizer")

# Creates the decision variables
x = {}
for app in app_ids:
    for lod, xIdx, yIdx in itertools.product(range(scene_UI.LODS), range(scene_UI.COLS), range(scene_UI.ROWS)):
        x[app, lod, xIdx, yIdx] = m.addVar(vtype=GRB.BINARY, name="x_%s_%s_%s_%s" % (app, lod, xIdx, yIdx))

########################################################
#############     set constrains     ################### 
########################################################

for app in app_ids:
    for lod in range(scene_UI.LODS):
        for xIdx in range(scene_UI.COLS):
            for yIdx in range(scene_UI.ROWS):
                # 计算组件占用的所有格子的位置
                positions = []
                if lod == 0:
                    positions = [(xIdx, yIdx)]
                elif lod == 1:
                    positions = [(xIdx, yIdx), (xIdx+1, yIdx)]
                elif lod == 2:
                    positions = [(xIdx, yIdx), (xIdx+1, yIdx), 
                               (xIdx, yIdx+1), (xIdx+1, yIdx+1)]
                
                # 对于每个位置，如果任何一个格子与面板/按钮重叠，就禁止这个放置
                for pos_x, pos_y in positions:
                    pos = np.array([pos_x*grid_a, pos_y*grid_a])
                    
                    # Check overlap with questions panel
                    
                    if (pos[0] < qpos[0] + qsize[0] and pos[0] + grid_a > qpos[0] and
                        pos[1] < qpos[1] + qsize[1] and pos[1] + grid_a > qpos[1]):
                        m.addConstr(x[app, lod, xIdx, yIdx] == 0)
                        break  # 一旦发现重叠就可以停止检查其他位置
                    
                    # Check overlap with Apps button
                    
                    if (pos[0] < bpos[0] + bsize[0] and pos[0] + grid_a > bpos[0] and
                        pos[1] < bpos[1] + bsize[1] and pos[1] + grid_a > bpos[1]):
                        m.addConstr(x[app, lod, xIdx, yIdx] == 0)
                        break  # 一旦发现重叠就可以停止检查其他位置

#  4 elements placed
m.addConstr(sum(x[app, lod, xIdx, yIdx] 
           for app in app_ids
           for lod in range(scene_UI.LODS)
           for xIdx in range(scene_UI.COLS)
           for yIdx in range(scene_UI.ROWS)) == 4)

#  Each element can only be displayed in one level of detail and one position
for app in app_ids:
    m.addConstr(sum(x[app, lod, xIdx, yIdx]
               for lod in range(scene_UI.LODS)
               for xIdx in range(scene_UI.COLS) 
               for yIdx in range(scene_UI.ROWS)) <= 1)

# No overlapping elements considering LoD size
for xIdx in range(scene_UI.COLS):
    for yIdx in range(scene_UI.ROWS):
        overlap_sum = (
            # LoD 0: 1x1
            sum(x[app, 0, xIdx, yIdx] for app in app_ids) +
            # LoD 1: 1x2, check current and right cell
            sum(x[app, 1, xi, yIdx] for app in app_ids 
                for xi in range(max(0, xIdx-1), xIdx+1) if xi < scene_UI.COLS) +
            # LoD 2: 2x2, check current and surrounding cells
            sum(x[app, 2, xi, yi] for app in app_ids 
                for xi in range(max(0, xIdx-1), xIdx+1) if xi < scene_UI.COLS
                for yi in range(max(0, yIdx-1), yIdx+1) if yi < scene_UI.ROWS)
        )
        m.addConstr(overlap_sum <= 1)

########################################################
############# set reward and panelty ################### 
########################################################

norm_params = normalize_terms()

# 1. Reward proximity to question panel
questionProximityTerm = 0
for app in app_ids:
    for lod in range(scene_UI.LODS):
        for xIdx in range(scene_UI.COLS):
            for yIdx in range(scene_UI.ROWS):
                # widget center
                if lod == 0:  # 1x1
                    pos = np.array([
                        (xIdx + 0.5) * grid_a,  
                        (yIdx + 0.5) * grid_a
                    ])
                elif lod == 1:  # 1x2
                    pos = np.array([
                        (xIdx + 1.0) * grid_a,  # center of 2 grids
                        (yIdx + 0.5) * grid_a
                    ])
                else:  # lod 2, 2x2
                    pos = np.array([
                        (xIdx + 1.0) * grid_a,  
                        (yIdx + 1.0) * grid_a
                    ])
                
                dist_to_questions = np.sqrt(np.sum((pos - q_center)**2))
                normalized_dist = ((dist_to_questions - norm_params['q_min_dist']) / 
                                (norm_params['q_max_dist'] - norm_params['q_min_dist']))
                # questionProximityTerm += (1 - normalized_dist) * x[app, lod, xIdx, yIdx]
                questionProximityTerm += rele[app] * (1 - normalized_dist) * x[app, lod, xIdx, yIdx]


# 2. Penalty for overlapping with red dot (ROI)
roiAvoidanceTerm = 0
for app in app_ids:
    for lod in range(scene_UI.LODS):
        for xIdx in range(scene_UI.COLS):
            for yIdx in range(scene_UI.ROWS):
                # rect zone
                rect_x, rect_y = xIdx * grid_a, yIdx * grid_a
                rect_width, rect_height = grid_a, grid_a
                if lod > 0:
                    rect_width = 2 * grid_a
                if lod > 1:
                    rect_height = 2 * grid_a  
                # check overlapping: * use methods in "UI.py" about line 440ish (search: self.overlapping += 1)
                if scene_UI.circle_rectangle_overlap(circle_x, circle_y, circle_radius, 
                                                   rect_x, rect_y, rect_width, rect_height):
                    roiAvoidanceTerm -= poi_pan * x[app, lod, xIdx, yIdx]

# 3. Relevance term
relevanceTerm = sum(rele[app] * x[app, lod, xIdx, yIdx]
                   for app in app_ids
                   for lod in range(scene_UI.LODS)
                   for xIdx in range(scene_UI.COLS)
                   for yIdx in range(scene_UI.ROWS))

# 4. LoD reward
lodRewardTerm = sum(rele[app] * (lod + 1) / 3 * x[app, lod, xIdx, yIdx]
                   for app in app_ids
                   for lod in range(scene_UI.LODS)
                   for xIdx in range(scene_UI.COLS)
                   for yIdx in range(scene_UI.ROWS))


########################################################
########################################################
########################################################

print(scene_UI.get_info())

randomTerm = 0.0
for app in app_ids:
    for lod, xIdx, yIdx in itertools.product(range(scene_UI.LODS), range(scene_UI.COLS), range(scene_UI.ROWS)):
        randomTerm += random.uniform(-1,1) * x[app, lod, xIdx, yIdx]

m.ModelSense = GRB.MAXIMIZE
m.setObjective(
    rewards[0]*relevanceTerm + 
    rewards[1]*questionProximityTerm +
    rewards[2]*lodRewardTerm +
    roiAvoidanceTerm,
    GRB.MAXIMIZE
)
m.update()
m.optimize() 

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

scene_UI.init_app(optimal_results)
import sys
from ui import UI 


# Check if an argument is provided
scene_path = "scenes/scene-1.json"
if len(sys.argv) >= 2:
    scene_path = sys.argv[1]

# Loads target scene
scene = UI(scene_path)

interface = [
    {
        "name": "weather", 
        "lod": 0, 
        "placement": [1, 1] # This specifies a row and column for placement, rather than a pixel value
    },
    {
        "name": "stocks", 
        "lod": 2, 
        "placement": [3, 3] # This specifies a row and column for placement, rather than a pixel value
    },
]

# Starts application with interface
scene.init_app(interface)



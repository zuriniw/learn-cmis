import tkinter as tk
from PIL import Image, ImageTk

# Initialize the main application window
root = tk.Tk()
root.title("Grid GUI")

# Define the grid dimensions
rows, cols = 6, 8
block_size = 100

# Set window size
window_width = 800 
window_height = 600 
root.geometry(f"{window_width}x{window_height}")

# Load and display environment image
img_path = "nsh.jpg" 
img = Image.open(img_path)
img = img.resize((window_width, window_height), Image.LANCZOS)
env_img = ImageTk.PhotoImage(img)
env_label = tk.Label(root, image=env_img)
env_label.place(x=0, y=0, relwidth=1, relheight=1)

# Configure the grid layout
for r in range(rows):
    root.grid_rowconfigure(r, weight=1, minsize=block_size)
for c in range(cols):
    root.grid_columnconfigure(c, weight=1, minsize=block_size)

# Question frame 
def placeQuestion(x, y): 
    frame = tk.Frame(root)
    q1 = tk.Label(frame, 
                text="What is the current temperature in New York?", 
                wraplength=180,
                padx=10, 
                pady=10)
    q2 = tk.Label(frame, 
                text="How many windows are there in the hall?", 
                wraplength=180,
                padx=10, 
                pady=10)
    a1 = tk.Entry(frame, width=20)
    a2 = tk.Entry(frame, width=20)
    submit = tk.Button(frame, text="Submit")
    q1.pack(fill="x")
    a1.pack()
    q2.pack(fill="x")
    a2.pack()
    submit.pack()
    frame.grid(row=y, column=x, rowspan=2, columnspan=2, sticky="nsew")

def placeApplication(name, lod, x, y):
    label = tk.Label(root, text=str(name) + "-" + str(lod), font=("Arial", 12), bg="lightblue", borderwidth=1, relief="solid")
    rowspan = 1
    colspan = 1 
    if lod >= 1: 
        colspan = 2 
    if lod >= 2:
        rowspan = 2 
    label.grid(row=y, column=x, rowspan=rowspan, columnspan=colspan, sticky="nsew")

placeQuestion(4, 0)
placeApplication("weather", 1, 2, 2)
placeApplication("clock", 0, 2, 3)
placeApplication("translation", 2, 0, 0)
placeApplication("order_food", 1, 7, 5)

# Bring the grid to the foreground
root.lift()

# Run the application
root.mainloop()

# TODO: 
# - Give inputs --> JSON, examples, functions for reading data, timing code
# - Examples: 
# -- Cookie optimization 
# -- David's code
# -- Application 
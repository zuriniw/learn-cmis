import gurobipy as gp  # import the installed package
from gurobipy import *

import random
import math

# Calculates distance in a 1D menu
def calculate_distance(i, j):
    return abs(i - j)

# Exponential penalty on word length
def calculate_reading_cost(element):
  return (len(element)**math.e)

# Normalizes a list such that the values are mapped between 0+e and 1
def normalize_list(data, e=0.001):
  min_val = min(data)
  max_val = max(data)
  return [e + (x - min_val) / (max_val - min_val) for x in data]

# Normalizes a dictionary such that values are mapped between 0+e and 1
def normalize_dict(dictionary, e=0.001):
  values = normalize_list(list(dictionary.values()))
  keys = list(dictionary.keys())
  for i in range(len(keys)):
    dictionary[keys[i]] = values[i]
  return dictionary

# Define elements and positions
elements = ['Open', 'About','Quit','Help','Close', 'Save','Edit','Insert','Delete']
positions = list(range(len((elements))))

# Define usage frequency
frequency = {e:random.random() for e in elements}
frequency = normalize_dict(frequency)

# Define readings costs
reading_costs = {e:calculate_reading_cost(e) for e in elements}
reading_costs = normalize_dict(reading_costs)

# Define distances 
distances = [calculate_distance(0, p) for p in positions]
distances = normalize_list(distances)
#distances = [1 - distance for distance in distances]

m = Model("linear_menu")
x = {}

# Define decision variables 
for e in elements:
    for p in positions: 
       x[e,p] = m.addVar(vtype=GRB.BINARY, name="x_%s_%i" %(e, p))

# Define constraints
# Each position must be assigned one element 
for p in positions: 
   m.addConstr(sum(x[e,p] for e in elements) == 1, "uniqueness_constraint_%i"%p)
# Each element can only be assigned to one position 
for e in elements:
   m.addConstr(sum(x[e,p] for p in positions) == 1, "uniqueness_constraint_%s"%e)

# Define objective
w_f = 0.5
w_r = 0.5
cost = sum((w_f * frequency[e] + w_r * reading_costs[e]) * distances[p] * x[e, p]
                for e in elements 
                for p in positions)

m.update()
m.setObjective(cost, GRB.MINIMIZE)

m.optimize()

layout = {}
for v in m.getVars():
    if v.X == 1:
        element = v.VarName.split("_")[1]
        position = int(v.VarName.split("_")[2])
        layout[position] = element

print("Frequency")
#print(frequency)
print(dict(sorted(frequency.items(), key=lambda item: item[1])))
print()

print("Reading cost")
print(dict(sorted(reading_costs.items(), key=lambda item: item[1])))
#print(reading_costs)
print()

print("Distance")
print(distances)
print()

print("Cost")
print(m.getObjective().getValue())

print("Layout")
#print(layout)
print(dict(sorted(layout.items())))

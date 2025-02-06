import gurobipy as gp  # import the installed package
from gurobipy import *

import random
import math

def calculate_distance (i, j):
    return abs(i - j)

# Exponential penalty on word length
def calculate_reading_cost(element):
  return (len(element)**math.e)


# Normalizes a list such that the values are mapped between 0+e and 1
def normalize_list(data, e=0.001):
  min_val = min(data)
  max_val = max(data)
  return [e + (x - min_val) / (max_val - min_val) for x in data]

def normalize_dict(dictionary, e=0.001):
  values = normalize_list(list(dictionary.values()))
  keys = list(dictionary.keys())
  for i in range(len(keys)):
    dictionary[keys[i]] = values[i]
  return dictionary

# define elements and positions
elements = ['Open', 'About','Quit','Help','Close', 'Save','Edit','Insert','Delete']
positions = list(range(len((elements))))
sizes = [1,2]

# define usage frequency
frequency = {e:random.random() for e in elements}
frequency = normalize_dict(frequency)

# define readings costs
reading_costs = {e:calculate_reading_cost(e) for e in elements}
reading_costs = normalize_dict(reading_costs)

# define distances 
distances = [calculate_distance(0, p) for p in positions]
distances = normalize_list(distances)

m = Model("linear_menu")
x = {}

for e in elements:
    for s in sizes:
       for p in positions:
          x[e, s, p] = m.addVar(vtype=GRB.BINARY, name="%s_%i_%i" %(e, s, p))

# Constraint: Sum of element sizes should be less than total positions
m.addConstr(
    sum(s * x[e, s, p] for e in elements for s in sizes for p in positions) == len(positions),
    "SizeLimit"
)
# Constraint: Each element can be assigned at most one size
for e in elements:
    m.addConstr(
        sum(x[e, s, p] for s in sizes for p in positions) <= 1,
        f"UniqueSize_{e}"
    )
# Constraint: Each position can contain at most one element at a particular size
for p in positions:
   m.addConstr(
      sum(x[e,s,p] for e in elements for s in sizes) <= 1, f"UniquePos_{p}"
   )
for p in positions:
   if p == 0:
      continue
   m.addConstr(
      sum(x[e, 2, p-1] for e in elements) + 
      sum(x[e, s, p] for e in elements for s in sizes) <= 1, 
      f"overlap_{p}"
   )
# Constraint: Last element cannot be occupied with size 2 element 
m.addConstr(
   sum(x[e,2,positions[-1]] for e in elements) == 0, "last_element"
)

w_f = 1
w_r = 0 

objective = quicksum(s * (w_f * frequency[e] + w_f * reading_costs[e]) * distances[p] * x[e,s,p] 
                   for e in elements
                   for s in sizes
                   for p in positions)

m.setObjective(objective, GRB.MINIMIZE)
m.optimize()

print(frequency)
for e in elements:
    for s in sizes:
       for p in positions:
          if x[e,s,p].X == 1:
             print(e,s,p)
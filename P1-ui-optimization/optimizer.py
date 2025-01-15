import gurobipy as gp 
from gurobipy import GRB
import itertools
import numpy as np
import matplotlib.pyplot as plt

m = gp.Model("ui_optimnizer")

rows, cols = 8, 6
maxDist = rows ** 2 + cols ** 2
lods = 3 
questionPos = (4, 4)
pointsOfInterest = [(4,4), (0,0), (0,5)] # (0, 5), (1, 5), (2, 5)]
elements = [1, 2, 3]
relevance = [
    [0, 0, 1],
    [0, 0, 0],
    [0, 0, 0]
]
numElements = len(elements)

# x_e,c  = (0,1) element e --> container c
# lod = 1: 1, 1
# lod = 2: 2, 1 
# lod = 3: 2, 2
x = {}
for eIdx in range(numElements):
    # lod = 1 
    for xIdx, yIdx in itertools.product(range(rows), range(cols)):
        x[eIdx, 0, xIdx, yIdx] = m.addVar(vtype=GRB.BINARY, name="x_%s_%s_%s_%s" % (eIdx, 0, xIdx, yIdx))
    # lod = 2
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols)):
        x[eIdx, 1, xIdx, yIdx] = m.addVar(vtype=GRB.BINARY, name="x_%s_%s_%s_%s" % (eIdx, 1, xIdx, yIdx))
    # lod = 3 
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols - 1)):
        x[eIdx, 2, xIdx, yIdx] = m.addVar(vtype=GRB.BINARY, name="x_%s_%s_%s_%s" % (eIdx, 2, xIdx, yIdx))

# Constraints 
# Each LoD assigned at most once
for eIdx in range(numElements):
    lhs = 0 
    for xIdx, yIdx in itertools.product(range(rows), range(cols)):
        lhs += x[eIdx, 0, xIdx, yIdx]
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols)):
        lhs += x[eIdx, 1, xIdx, yIdx]
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols - 1)):
        lhs += x[eIdx, 2, xIdx, yIdx]
    m.addConstr(lhs <= 1, "c_lod_%s" % (eIdx))
# Slot capacity
for xIdx, yIdx in itertools.product(range(rows), range(cols)):
    lhs = 0
    for eIdx in range(numElements):
        lhs += x[eIdx, 0, xIdx, yIdx]
        if xIdx < rows - 1:
            lhs += x[eIdx, 1, xIdx, yIdx]
        if xIdx - 1 >= 0:
            lhs += x[eIdx, 1, xIdx - 1, yIdx]
        for xOffset, yOffset in itertools.product(range(2), range(2)):
            if xIdx - xOffset >= 0 and \
                xIdx - xOffset < rows - 1 and \
                yIdx - yOffset >= 0 and \
                yIdx - yOffset < cols - 1:
                lhs += x[eIdx, 2, xIdx - xOffset, yIdx - yOffset]
    m.addConstr(lhs <= 1, "c_slot_%s_%s" % (xIdx, yIdx))
# Overlap with questions
for qxOffset, qyOffset in itertools.product(range(2), range(2)):
    xIdx, yIdx = questionPos[0] + qxOffset, questionPos[1] + qyOffset
    lhs = 0 
    for eIdx in range(numElements):
        lhs += x[eIdx, 0, xIdx, yIdx]
        if xIdx < rows - 1:
            lhs += x[eIdx, 1, xIdx, yIdx]
        if xIdx - 1 >= 0:
            lhs += x[eIdx, 1, xIdx - 1, yIdx]
        for xOffset, yOffset in itertools.product(range(2), range(2)):
            if xIdx - xOffset >= 0 and \
                xIdx - xOffset < rows - 1 and \
                yIdx - yOffset >= 0 and \
                yIdx - yOffset < cols - 1:
                lhs += x[eIdx, 2, xIdx - xOffset, yIdx - yOffset]
    m.addConstr(lhs <= 0, "c_question_%s_%s" % (xIdx, yIdx))    

# Objective 
# Maximize application relevancy
relevanceTerm = 0.0 
for eIdx in range(numElements):
    for xIdx, yIdx in itertools.product(range(rows), range(cols)):
        relevanceTerm += relevance[eIdx][0] * x[eIdx, 0, xIdx, yIdx]
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols)):
        relevanceTerm += relevance[eIdx][1] * x[eIdx, 1, xIdx, yIdx]
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols - 1)):
        relevanceTerm += relevance[eIdx][2] * x[eIdx, 2, xIdx, yIdx]
# Minimize proximity to questions 
def calcDist(x1, y1, x2, y2):
    return (x2 - x1) ** 2 + (y2 - y1) ** 2  
proximity = np.zeros((rows, cols))
for xIdx, yIdx in itertools.product(range(rows), range(cols)):
    proximity[xIdx, yIdx] = 1 - calcDist(xIdx, yIdx, questionPos[0], questionPos[1]) / maxDist

proximityTerm = 0.0 
for eIdx in range(numElements):
    for xIdx, yIdx in itertools.product(range(rows), range(cols)):
        proximityTerm += proximity[xIdx, yIdx] * x[eIdx, 0, xIdx, yIdx]
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols)):
        proximityTerm += proximity[xIdx, yIdx] * x[eIdx, 1, xIdx, yIdx]
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols - 1)):
        proximityTerm += proximity[xIdx, yIdx] * x[eIdx, 2, xIdx, yIdx]
# Minimize overlap with regions of interest
regionsOfInterest = np.zeros((rows, cols))
for poi in pointsOfInterest:
    for xIdx, yIdx in itertools.product(range(rows), range(cols)):
        regionsOfInterest[xIdx, yIdx] = max(regionsOfInterest[xIdx, yIdx], 1 - calcDist(xIdx, yIdx, poi[0], poi[1]) / maxDist)

roiTerm = 0.0 
for eIdx in range(numElements):
    for xIdx, yIdx in itertools.product(range(rows), range(cols)):
        roiTerm += regionsOfInterest[xIdx, yIdx] * x[eIdx, 0, xIdx, yIdx]
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols)):
        roiTerm += regionsOfInterest[xIdx, yIdx] * x[eIdx, 1, xIdx, yIdx]
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols - 1)):
        roiTerm += regionsOfInterest[xIdx, yIdx] * x[eIdx, 2, xIdx, yIdx]


m.ModelSense = GRB.MAXIMIZE
m.setObjectiveN(relevanceTerm, index=0, weight=2)
m.setObjectiveN(proximityTerm, index=1, weight=1)
m.setObjectiveN(roiTerm, index=2, weight=-1)

m.update()
m.optimize() 

for eIdx in range(numElements):
    for xIdx, yIdx in itertools.product(range(rows), range(cols)):
        if x[eIdx, 0, xIdx, yIdx].X > 0: 
            print(eIdx, 0, xIdx, yIdx)
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols)):
        if x[eIdx, 1, xIdx, yIdx].X > 0: 
            print(eIdx, 1, xIdx, yIdx)
    for xIdx, yIdx in itertools.product(range(rows - 1), range(cols - 1)):
        if x[eIdx, 2, xIdx, yIdx].X > 0: 
            print(eIdx, 2, xIdx, yIdx)
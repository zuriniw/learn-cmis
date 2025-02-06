import gurobipy as gp 
from gurobipy import GRB

m = gp.Model("cookie_optimizer")

##### INPUTS #####
# Proportion of white to brown sugar 
# x_sugar = [0, 1]
x_sugar = m.addVar(0, 1, vtype=GRB.CONTINUOUS, name="x_sugar")

# Flour gluten 
# Different amounts of gluten give different results 
# lowest to highest gluten content: cake, all purpose, bread
# x_cake = (0, 1)
# x_ap = (0, 1)
# x_bread = (0, 1)
x_cake = m.addVar(vtype=GRB.BINARY, name="x_cake")
x_ap = m.addVar(vtype=GRB.BINARY, name="x_ap")
x_bread = m.addVar(vtype=GRB.BINARY, name="x_bread")

# Fat 
# x_shortening = (0, 1)
# x_butter = (0, 1)
x_shortening = m.addVar(vtype=GRB.BINARY, name="x_shortening")
x_butter = m.addVar(vtype=GRB.BINARY, name="x_butter")

# Melted 
# x_melted = (No, Yes) = (0, 1)
x_melted = m.addVar(vtype=GRB.BINARY, name="x_melted")

# Baking powder 
# x_baking = [0, 2]
x_baking = m.addVar(0, 2, vtype=GRB.CONTINUOUS, name="x_baking")

##### OBJECTIVES + CONSTRAINTS #####
# Helper function: Acidity 
# (x_baking + (1 - x_sugar)) / 3.0
def acidity(x_baking, x_sugar): 
    return (x_baking + 1 - x_sugar) / 3.0

# Objetive: chewiness 
# brown sugar traps moisture: Maximize brown to white sugar ratios
# high gluten traps moisture: Use bread flour
# melted butter adds water content and moisture: Use melted butter
# (1 - x_sugar) + x_bread + x_butter + x_melted
def chewiness(x_sugar, x_bread, x_butter, x_melted):
    return 1.0 - x_sugar + x_bread + x_butter + x_melted

# Objective: crispiness 
# butter melts fast, promotes spread: Use butter
# lower acidity raises setting temperature allowing time to spread: Minimize acidity
# white sugar is crispy: Maximize white to brown sugar ratio
# A balanced amount of flour helps maximize crispiness: Use all purpose flour 
# x_butter + (1 - acidity) + x_sugar +  x_ap
def crispiness(x_butter, x_baking, x_sugar, x_ap):
    return x_butter + 1 - acidity(x_baking, x_sugar) + x_sugar + x_ap

# Objective: cakiness 
# shortening melts at a higher temperature giving batter time to rise: Use shortening
# flour protein absorbs water which needs to be turned to steam to make a batter that rises: Use bread flour
# Higher acidity lowers the spread of batter, includes need to keep some brown sugar: maximize acidity, balance white to brown sugar ratio
# cookie.acidity
# x_shortening + x_bread + acidity + t_sugar
# constraint: t >= x_sugar - 0.5 
# constraint: t >= 0.5 - x_sugar
# t_sugar = |x_sugar - 0.5|
t_sugar = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="t_sugar") # auxiliary variable t_sugar
m.addConstr(t_sugar >= x_sugar - 0.5, "constr_t_sugar_1")
m.addConstr(t_sugar >= 0.5 - x_sugar, "constr_t_sugar_2")

def cakiness(x_shortening, x_bread, x_baking, x_sugar, t_sugar):
    return x_shortening + x_bread + acidity(x_baking, x_sugar) + 2 * t_sugar

# Constraints
# constraint: x_cake + x_ap + x_bread <= 1
m.addConstr(x_cake + x_ap + x_bread <= 1, "constr_flour")

# constraint: x_butter + x_shortening <= 1
m.addConstr(x_butter + x_shortening <= 1, "constr_fat")


m.ModelSense = GRB.MAXIMIZE
chewinessTerm = chewiness(x_sugar, x_bread, x_butter, x_melted)
crispinessTerm = crispiness(x_butter, x_baking, x_sugar, x_ap)
cakinessTerm = cakiness(x_shortening, x_bread, x_baking, x_sugar, t_sugar)
m.setObjectiveN(chewinessTerm, index=0, weight=1)
m.setObjectiveN(crispinessTerm, index=1, weight=0)
m.setObjectiveN(cakinessTerm, index=2, weight=1)
m.update()
m.optimize() 

print("OPTIMIZED RESULTS:")
print("White to brown sugar ratio:", x_sugar.X)
if x_cake.X > 0:
    print("Flour: cake")
if x_ap.X > 0:
    print("Flour: all purpose")
if x_bread.X > 0:
    print("Flour: bread")
if x_butter.X > 0:
    print("Fat: butter")
if x_shortening.X > 0:
    print("Fat: shortening")
print("Melted fat:", x_melted.X)
print("Baking powder:", x_baking.X)
m.dispose()

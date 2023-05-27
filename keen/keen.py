
board = """
abbc
adbc
edff
eggf"""

Add = lambda a,b: a+b
Sub = lambda a,b: a-b
Mul = lambda a,b: a*b

key = dict(
    a=(1,Sub),
    b=(9,Add),
    c=(2,Sub),
    d=(1,Sub),
    e=(4,Mul),
    f=(16,Mul),
    g=(4,Add)
)


rows = board_str.split("\n")
if len(rows[0])==0:
    rows = rows[1:]
if len(rows[-1])==0:
    rows = rows[:-1]

N = len(rows)
Vars = 

Var = lambda name: pulp.LpVariable(name, cat='Integer')
assert all(N == len(row) for row in rows)
for ri, row in enumerate(rows):
    for ci, val in enumerate(row):



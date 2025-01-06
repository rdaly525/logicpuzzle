
import pulp

#Need a way to read in a board





board = """
000000
005000
03d003
300050
000000
005d03
400000
000d00
02d300"""


board="""
d00502d2
d0300040
30d0d04d
032d3dd3
0000d000
0602d3dd
d00dd30d
3d00d30d
d00d5d0d
0002dd04
40000000"""

board = """
200d
3004
0000
d000"""

board = """
d03d00
320060
005000
000000
030000
000000
004000
030400
00d300"""



def parse(board_str):
    rows = board_str.split("\n")
    if len(rows[0])==0:
        rows = rows[1:]
    if len(rows[-1])==0:
        rows = rows[:-1]

    num_rows = len(rows)
    num_cols = len(rows[0])
    assert all(num_cols == len(row) for row in rows)
    points = {}
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            if val == '0':
                continue
            try:
                val = int(val)
            except:
                pass
            points.setdefault(val, []).append((ri,ci))
    return points, num_rows, num_cols


points, nr, nc = parse(board)


board = [[[] for _ in range(nc)] for _ in range(nr)]
Vars = {} #(r,c,h(1) or v(0), hi/vi): var
Var = lambda name: pulp.LpVariable(name, cat='Binary')

pvars = {}
for v, lst in points.items():
    if v is 'd':
        continue
    print(v)
    for ri, ci in lst:
        print("",ri,ci)
        pvars[(ri,ci)] = []
        for hi,cii in enumerate(range(ci-v+1, ci+1)):
            if cii >=0 and cii+v-1 <nc:
                t = (ri,ci,1,hi)
                var = Var(str(t))
                Vars[t] = var
                pvars[(ri,ci)].append(var)
                print(f"   h{hi}",cii,cii+v-1)
                for ciii in range(cii,cii+v):
                    board[ri][ciii].append(var)
        for vi,rii in enumerate(range(ri-v+1, ri+1)):
            if rii >=0 and rii+v-1 < nr:
                t = (ri,ci,0,vi)
                var = Var(str(t))
                Vars[t] = var
                pvars[(ri,ci)].append(var)
                print(f"   v{hi}",rii,rii+v-1)
                for riii in range(rii,rii+v):
                    board[riii][ci].append(var)



#Mijk is a sparse list of binary variables

p = pulp.LpProblem("BS", pulp.LpMinimize)

#Objective
p += (1)
#Constraints
for ri, row in enumerate(board):
    for ci, vlist in enumerate(row):
        if (ri,ci) in points['d']:
            print("DOT", (ri,ci))
            p += (sum(vlist)==1)
        else:
            p += (sum(vlist)<=1)
for v, vlist in pvars.items():
    p += (sum(vlist)==1)
print(p)

p.solve()
print(pulp.LpStatus[p.status])
for v in p.variables():
    print(f"{v.name} = {v.varValue}")

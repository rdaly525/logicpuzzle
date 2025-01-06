


#Things to do:
#For a single row, I should keep a count of how many possi

def rids(r):
    assert r in range(9)
    return range(9*r,9*(r+1))

def ridx(i):
    assert i in range(81)
    return i//9

def cids(c):
    assert c in range(9)
    return range(c,81,9)

def cidx(i):
    assert i in range(81)
    return i%9


def bids(b):
    assert b in range(9)
    rr = b//3
    cc = b%3
    ids = []
    for r in range(3*rr,3*rr+3):
        for c in range(3*cc,3*cc+3):
            ids.append(9*r+c)
    return ids

def bidx(i):
    rr = (i//9)//3
    cc = (i%9)//3
    return rr*3+cc

class Board:
    def __init__(self, init):
        self.solved = [False for i in range(81)]
        assert len(init) == 81
        for v in init:
            assert v >=0 and v <10
        self.poss = [set(range(1,10)) for i in range(81)]
        for i,v in enumerate(init):
            if v != 0:
                print(f"I! setting {i} to {v}")
                self.set_spot(i,v)

        self.solve("unique_number","spot_pair","naked_pair")
        self.run_strat("unique_number")
        s1 = self.score()
        #self.chunk_strat("naked_pair")
        self.run_strat("spot_pair",True)
        s2 = self.score()

        if self.won():
            print("Won!")
        else:
            print("Lost :(")
            for bi in range(9):
                print("bi",bi)
                for i in bids(bi):
                    if not self.solved[i]:
                        print("  ",i,self.poss[i])
        print(self)

        print(s1,s2)

    def won(self):
        ret = all(self.solved)
        if ret:
            self.verify()
        return ret

    def score(self):
        missing = 81-sum(self.solved)
        poss_left = sum(len(p) for p in self.poss)
        return missing, poss_left

    def solve(self,*strats):
        changed = True
        while (True):
            if self.won() or not changed:
                break
            changed = False
            for strat in strats:
                changed |= self.run_strat(strat)

    def run_strat(self,strat,b_only=False):
        if b_only:
            ids_list = (bids,)
        else:
            ids_list = (rids,cids,bids)
        changed = False
        for ids in ids_list:
            for i in range(9):
                changed |= getattr(self,strat)(ids(i))
        return changed

    ##Possible other strats:
    #(spot_pair): if within a box there is a pair of spots (in a row or col) which a number has to be in you can remove that number from all other spots in the col

    #secret_pair

    #Strat 1: check if there is a number that has to go somewhere
    #independnly on all ids
    def unique_number(self,ids):
        changed = False
        nums = {i:[] for i in range(1,10)}
        for i in ids:
            for p in self.poss[i]:
                nums[p].append(i)
        for p,_ids in nums.items():
            if len(_ids)==1 and not self.solved[_ids[0]]:
                changed = True
                print(f"C! setting {_ids[0]} to {p}")
                self.set_spot(_ids[0],p)
        return changed

    def spot_pair(self,ids):
        def colinear(ids,is_col):
            ids = list(ids)
            f = cidx if is_col else ridx
            rcidx = f(ids[0])
            for i in ids[1:]:
                idx = f(i)
                if rcidx != idx:
                    return False, None
            return True, rcidx

        #ids contains bids
        changed = False
        nums = {i:[] for i in range(1,10)}
        for i in ids:
            for p in self.poss[i]:
                nums[p].append(i)
        #I am looking for colinear ids
        for v,_ids in nums.items():
            if len(_ids)==1:
                continue
            in_col, col = colinear(_ids,is_col=True)
            if in_col:
                for i in (set(cids(col))-set(_ids)):
                    c = self.remove(i,v)
                    if c:
                        print(f"Rem,c, {i} {v}")
                    changed |= c
            in_row, row = colinear(_ids,is_col=False)
            if in_row:
                for i in (set(rids(row))-set(_ids)):
                    c = self.remove(i,v)
                    if c:
                        print(f"Rem,r, {i} {v}")
                    changed |= c

        return changed


    #Strat 2: check if n spots contain identical entries within a box
    def naked_pair(self,ids):
        changed = False
        sets = {}
        for i in ids:
            p = tuple(self.poss[i])
            if len(p)==1:
                continue
            sets.setdefault(p,[]).append(i)
        for p,_ids in sets.items():
            if len(p) == len(_ids):
                print("!!",p,_ids)
                for i in (set(ids) - set(_ids)):
                    for v in p:
                        changed |= self.remove(i,v)
        return changed

    def secret_pair(self,ids):
        pass


    def set_spot(self,i,v):
        assert v in self.poss[i]
        self.poss[i].clear()
        self.poss[i].add(v)
        #remove from row
        self.solved[i] = True
        for ids in (rids(ridx(i)),cids(cidx(i)),bids(bidx(i))):
            for j in ids:
                if j != i:
                    self.remove(j,v)

    def remove(self,i,v):
        changed = False
        if v in self.poss[i]:
            nleft = len(self.poss[i])
            assert nleft > 1
            self.poss[i].remove(v)
            changed = True
            if nleft == 2:
                print(f"R! setting {i} to {v}")
                self.set_spot(i,list(self.poss[i])[0])
        return changed

    def verify(self):
        cmp = set(range(1,10))
        for i in range(9):
            for ids in (rids,cids,bids):
                pset = set()
                for idx in ids(i):
                    p = self.poss[idx]
                    assert len(p)==1
                    pset.add(next(iter(p)))
                assert len(pset)==9

    def __str__(self):
        b = [" " if len(p)>1 else str(list(p)[0]) for p in self.poss]
        mid = "\n" + "+".join("-"*3 for _ in range(3)) + "\n"
        big = []
        for r in range(0,9,3):
            row3 = []
            for rr in range(3):
                o = 9*(r+rr)
                row = "|".join("".join(b[o+c:o+c+3]) for c in range(0,9,3))
                row3.append(row)
            big.append("\n".join(row3))
        return "\n"+mid.join(big)






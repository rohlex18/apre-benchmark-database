def COM(T, P):
    return len([p for p in P.intervals if T.covers(p)])/P.field_num

def CON(T, P):
    return len([t for t in T.intervals if P.covers(t)])/T.field_num

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def COR(T, P):
    Right = [P.covers(t) for t in T.intervals if P.covers(t)]
    Left = [p for p in P.intervals if T.covers(p)]
    return len(intersection(Left, Right))/P.field_num

def PER(T, P):
    #Perfection
    return len([p for p in P.intervals if p in T.intervals])/P.field_num

import math
def FMS(T, P, gamma=2):
    res = 0
    for t in T.b:
        delta = min([abs(p-t) for p in P.b])
        res += math.exp(-(delta/gamma)**2)
    coeff = math.exp( - ((len(T.b) - len(P.b))/len(T.b))**2 ) / len(T.b)
    return coeff*res

def WAR(T, P):
    res = 0
    for t,p in zip(T.bb, P.bb):
        if t==p:
            res +=1
    return res / min(len(T.bb), len(P.bb))

import itertools
def PS_n(T, P, n=4):
    n_grams = set([''.join(x) for x in itertools.combinations(P.bbs,n)])
    res, denom = 0, 0
    for s in n_grams:
        res += min(P.bbs.count(s) ,T.bbs.count(s))
        denom += P.bbs.count(s)
    if denom == 0:
        return 0
    return res/denom

def bleu(T, P, k=8):
    res = 1
    for i in range(1,k+1):
        PS = PS_n(T, P, n=i)
        if PS > 0:
            res *= math.pow(PS, 1/(2**i)) 
    return math.exp(min(0, 1 - len(T.bb)/len(P.bb))) * res

import Levenshtein as L
def Lev(T,P):
    return 1-L.distance(T.ebbs, P.ebbs)/max(len(T.ebbs),len(P.ebbs))
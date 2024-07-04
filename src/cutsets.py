import networkx as nx
from itertools import combinations, islice
import numpy as np


def successpaths(H, source, target, weight='weight'):
    return list(nx.shortest_simple_paths(H, source, target, weight=weight))


# Function for Finding Minimal cuts
def minimalcuts(H, src_, dst_, order=6):
    paths = list(islice(nx.shortest_simple_paths(H, src_, dst_, weight='weight'), 2))
    minimal = []

    if [src_, dst_] in paths:
        minimal.append(src_)
        minimal.append(dst_)
    else:
        paths = successpaths(H, src_, dst_)
        pairs = np.array(H.nodes)
        pairs = pairs.tolist()

        pairs = [pair for pair in pairs if pair != src_ and pair != dst_]

        incidence = np.zeros([len(paths), len(pairs)])
        incidence_cols_name = pairs

        for x in range(len(paths)):
            for comp in pairs:
                if comp in paths[x]:
                    incidence[x, pairs.index(comp)] = 1

        firstpairs = []
        for k in range(1, order + 1):
            if incidence.shape[1] == 0:
                break

            all_ones = [i for i in range(incidence.shape[1]) if incidence[:, i].all()]
            if k == 1:
                firstpairs = [k for k in incidence_cols_name if k not in all_ones]
            for c in all_ones:
                minimal.append(incidence_cols_name[c])

            if k >= order:
                continue

            pairs = firstpairs
            newpairs = list(combinations(pairs, k + 1))

            newpairstodelete = []
            for i in newpairs:
                for j in minimal:
                    if isinstance(j, tuple):
                        if set(j).issubset(i):
                            newpairstodelete.append(i)
                            break
            newpairs = [i for i in newpairs if i not in newpairstodelete]

            incidence_ = np.zeros([len(paths), len(newpairs)])
            incidence_cols_name = newpairs
            for x in range(len(paths)):
                for y in range(len(newpairs)):
                    for comp in newpairs[y]:
                        if comp in paths[x]:
                            incidence_[x, y] = 1
                            break
            incidence = np.copy(incidence_)

    return minimal
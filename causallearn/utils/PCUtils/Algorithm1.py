import numpy as np
from causallearn.graph.GraphClass import CausalGraph
from causallearn.utils.PCUtils.Helper import append_value
from itertools import permutations, combinations



def skeleton_discovery(data, alpha, indep_test, stable=True, background_knowledge=None):
    '''
    Perform skeleton discovery

    Parameters
    ----------
    data : data set (numpy ndarray)
    alpha: desired significance level in (0, 1) (float)
    indep_test : name of the independence test being used
           - "Fisher_Z": Fisher's Z conditional independence test
           - "Chi_sq": Chi-squared conditional independence test
           - "G_sq": G-squared conditional independence test
    stable : run stabilized skeleton discovery if True (default = True)

    Returns
    -------
    cg : a CausalGraph object

    '''

    assert type(data) == np.ndarray
    assert 0 < alpha < 1

    no_of_var = data.shape[1]
    cg = CausalGraph(no_of_var)
    cg.data = data
    cg.set_ind_test(indep_test)

    node_ids = range(no_of_var)
    pair_of_variables = list(permutations(node_ids, 2))

    depth = -1
    while cg.max_degree() - 1 > depth:
        depth += 1
        edge_removal = []
        for (x, y) in pair_of_variables:
            Neigh_x = cg.neighbors(x)
            if y not in Neigh_x:
                continue
            else:
                Neigh_x = np.delete(Neigh_x, np.where(Neigh_x == y))

            if len(Neigh_x) >= depth:
                for S in combinations(Neigh_x, depth):
                    p = cg.ci_test(x, y, S)
                    if p > alpha or (background_knowledge is not None and (background_knowledge.is_forbidden(cg.G.nodes[x], cg.G.nodes[y]) and background_knowledge.is_forbidden(cg.G.nodes[y], cg.G.nodes[x]))):
                        if p > alpha:
                            print('%d ind %d | %s with p-value %f\n' % (x, y, S, p))
                        else:
                            print('%d ind %d | %s with background knowledge\n' % (x, y, S))

                        if not stable:  # Unstable: Remove x---y right away
                            edge1 = cg.G.get_edge(cg.G.nodes[x], cg.G.nodes[y])
                            if edge1 is not None:
                                cg.G.remove_edge(edge1)
                            edge2 = cg.G.get_edge(cg.G.nodes[y], cg.G.nodes[x])
                            if edge2 is not None:
                                cg.G.remove_edge(edge2)
                        else:  # Stable: x---y will be removed only
                            edge_removal.append((x, y))  # after all conditioning sets at
                            edge_removal.append((y, x))  # depth l have been considered
                            append_value(cg.sepset, x, y, S)
                            append_value(cg.sepset, y, x, S)
                        break

        for (x, y) in list(set(edge_removal)):
            edge1 = cg.G.get_edge(cg.G.nodes[x], cg.G.nodes[y])
            if edge1 is not None:
                cg.G.remove_edge(edge1)

    return cg

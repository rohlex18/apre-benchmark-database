from anytree.exporter import DictExporter
from anytree import findall, PreOrderIter
import networkx as nx

def ins_del(x):
    #inserts weighted as 0.001 and dels weighted as 1 to keep track
    return int((round(x*1000)%1000)//1), int(x//1)



def convert_anytree_to_nx(root, node_attrs):
    # convert the anytree tree to a dictionary
    exporter = DictExporter()
    tree_dict = exporter.export(root)

    # create an empty networkx graph
    G = nx.DiGraph()
    
    attr_dicts = [{} for i in range(len(node_attrs))]

    # iterate over the tree_dict to add the nodes and their attributes to the graph
    for node in PreOrderIter(root):
        name = node.id
        G.add_node(name)
        #n = list(G.nodes())[-1]
        for i,attr in enumerate(node_attrs):
            val = getattr(node, attr)
            attr_dicts[i][name] = val

    # iterate over the tree_dict to add the edges to the graph
    for node in PreOrderIter(root):
        parent = node.id
        for child in node.children:
            G.add_edge(parent, child.id)
     
    for attrs,name in zip(attr_dicts, node_attrs):
        #print(attrs)
        nx.set_node_attributes(G, attrs, name)
            
    return G

def nm(n1, n2):
    print('nm', n1, n2)
    return n1['name'] == n2['name']

def em(e):
    #print(e)
    return True

def nsc(n1, n2):
    if n1['name']==n2['name']:
        return 0
    else:
        #print(n1,n2)
        return 1.001

def ndc(n):
    #print('del', n)
    return 1

def nic(n):
    #print('ins', n)
    return 0.001

def esc(e1, e2):
    return 0

def edc(e):
    #print(e, type(e))
    return 0

def eic(e):
    return edc(e)

def FieldTreeScore(PFT, TFT):
    #TFT uses the name param
    for node in PreOrderIter(PFT):
        node.name = node.type

    Gpred = convert_anytree_to_nx(PFT, ['name'])
    Gtest = convert_anytree_to_nx(TFT, ['name'])
    
    TN = Gtest.number_of_nodes()
    
    PN = Gpred.number_of_nodes()
    
    true_branches = len([no for no,nu in Gtest.degree() if nu>2])
    
    pred_branches = len([no for no,nu in Gpred.degree() if nu>2])
    
    dist = nx.graph_edit_distance(Gpred, Gtest, node_match=nm, edge_match=None, 
                       node_subst_cost=nsc, node_del_cost=ndc, node_ins_cost=nic, 
                       edge_subst_cost=esc, edge_del_cost=edc, edge_ins_cost=eic)
    
    print(f'{dist=}')

    TNI, PND = ins_del(dist)
    
    w1 = 1/2
    
    score = round(1 - w1*PND/PN - (1-w1)*TNI/TN, 2)

    assert PN - PND + TNI == TN, f'{(PN, TN, PND, TNI)=}'

    return PN, TN, PND, TNI, score
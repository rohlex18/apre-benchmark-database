import numpy as np
import pandas as pd
from anytree import AnyNode, PreOrderIter
from anytree.search import findall


def avg_bit_from_pairs(time_byte_pairs):
    data_ints = np.array([[int.from_bytes(x[1], byteorder='big')] for x in time_byte_pairs], dtype=np.uint8)
    try:
        bit_array = np.unpackbits(data_ints, axis=1)
    except Exception as e:
        print(e, data_ints)
    return np.average(bit_array, axis=0).astype(np.float64).tolist()


def get_paths_with_n_nodes(root, n):
    paths = []

    def dfs(node, path):
        nonlocal paths
        if len(path) == n:
            paths.append(path)
        else:
            for child in node.children:
                dfs(child, path + [child])

    dfs(root, [root])
    return paths


def count_nodes_to_leaf(node):
    # If the node is a leaf, return 0
    if not node.children:
        return 1

    # Keep track of the minimum number of nodes to a leaf
    min_count = float('inf')

    # Traverse the tree to find the minimum number of nodes to a leaf
    for child in node.children:
        count = 1 + count_nodes_to_leaf(child)
        min_count = min(count, min_count)

    return min_count


def label_bytes_uniform(node, type):
    if node.id == 'root':
        node.type = None
    else:
        node.type = type
    for c in node.children:
        label_bytes_uniform(c, type)


def label_bytes_with_model(node, model, lengths_dict):
    node.type = 'UINT8'

    if node.id == 'root':
        # root case
        node.features = None
        node.probas = None
        node.best_prob = None
        node.type = None
    else:
        trans = node.trans
        trans = [x/sum(trans) if sum(trans) > 0 else x for x in trans]
        avgs = avg_bit_from_pairs(node.time_byte_pairs)

        features = pd.DataFrame(columns=[f'Bit {i} TP' for i in range(8)] + [f'Bit {i} AV' for i in range(8)])
        try:
            features.loc[0] = trans + avgs
        except Exception as e:
            print(f'{e=}, {features=}, {trans + avgs=}')
        node.features = features
        node.probas = model.predict_proba(node.features)
        node.best_prob = 0
    # keep going down tree
    for c in node.children:
        label_bytes_with_model(c, model, lengths_dict)

    # now we are going back up!
    if node.id == 'root':
        # back at the top, reconcile types
        return node

    for i, dic in enumerate(sorted(lengths_dict.items())):
        f, flen = dic
        if count_nodes_to_leaf(node) - flen < 0:
            continue
        paths = get_paths_with_n_nodes(node, flen)

        if len(paths) == 1:
            if paths[0][0].nc != paths[0][-1].nc:
                continue

        total_prob = 1
        total_pkts = node.nc
        for path in paths:
            for n in path:
                total_prob *= n.probas[0, i]
            # times by the weight of the path
            # total_prob *= n.nc/total_pkts
            total_prob *= 1/3  # penalty factor
            for n_prev in path[-1].children:
                total_prob *= n_prev.best_prob
        # print(total_prob)
        if total_prob > node.best_prob:
            node.best_prob = total_prob
            node.type = f


def fill_attribute(source_tree, target_tree, source_attribute, target_attribute):
    for tnode in PreOrderIter(target_tree):
        source_node = findall(source_tree, lambda node: node.id == tnode.id)[0]
        if source_node:
            # print(source_node)
            # source_node = source_nodes[0]
            setattr(tnode, target_attribute, getattr(source_node, source_attribute))


def fill_sib_count(source_tree, target_tree):
    for tnode in PreOrderIter(target_tree):
        source_node = findall(source_tree, lambda node: node.id == tnode.id)[0]
        if source_node:
            # print(source_node)
            # source_node = source_nodes[0]
            setattr(tnode, 'sibs', len(source_node.siblings))

def consolidate_types(pkt_hex, pft, length_dict):
    branch = pft.transform([(pkt_hex, 'ts')])[0]
    fill_attribute(pft.tree, branch, 'type', 'type')
    types = [node.type for node in branch.descendants]

    pkt_len = len(pkt_hex)//2-1
    assert len(types) == pkt_len, f'{len(types)=} {pkt_len=}'
    res = []
    i = 0
    while i < pkt_len:
        t = types[i]
        l = length_dict[t]
        if i > 0 and res[-1] == 'STRING' and t == 'STRING':
            res[-1] = (res[-1][0]+1, t)
        else:
            res.append((l, t))
        i += l
        # print(res)

    '''we have the same problem as before, if a packet extends another by a byte but its been labelled as UINT32, we have a 1 byte field being labelled as such...'''
    # assert sum([x[0] for x in res]) == pkt_len, f'{res=} {sum([x[0] for x in res])} , {pkt_len=}'

    return res


def fontcolor(node):
    return 'black'
    # if true(node):
    #     return 'darkgreen'
    # else:
    #     return 'black'


def node_colour(node, pred):
    if not pred:
        return 'green'
    else:
        return 'red'


def edgecolor(node):
    if node.name == 'START':
        return


def style(node, pred):
    if not pred:
        return 'solid'
    else:
        return 'dashed'


def build_tree(pft_lengths, offsets=False):
    root = AnyNode(id='START', name='START')
    root.leaf = False
    formats = []
    for i, pft_format in enumerate(pft_lengths):

        # print(i)
        new_format = False
        syntaxes = [x[1] for x in pft_format]
        if 'field_0' == syntaxes[0]:
            continue

        if offsets:
            syntaxes = [f'{k+1}, {syntaxes[k]}' for k in range(len(syntaxes))]
        branch_id = 'START'
        current_node = root
        for syn in syntaxes:
            next_children = current_node.children
            branch_id += '/'+syn
            if branch_id in [c.id for c in next_children]:
                # child match
                current_node = findall(current_node, lambda node: node.id == branch_id)[0]
            else:
                # no children or no child match
                new_format = True
                new_node = AnyNode(id=branch_id, name=syn, parent=current_node)
                # print(new_node.id)
                current_node = new_node
                new_node.leaf = False

        assert len(formats) == len([node.id for node in findall(root, lambda node: node.leaf)]), f'{len(formats)=}, {len([node.id for node in findall(root, lambda node: node.leaf)])=}, {new_format, syntaxes==formats[-1]}'

        if not current_node.leaf:
            # branch finished halfway through existing branch. so make new leaf
            new_format = True
            current_node.leaf = True

        if new_format:
            assert (syntaxes not in formats)
            formats.append(syntaxes)
            # current_node.counter +=1

        assert len(formats) == len([node.id for node in findall(root, lambda node: node.leaf)]), f'{len(formats)=}, {len([node.id for node in findall(root, lambda node: node.leaf)])=}, {new_format, syntaxes==formats[-1]}'

    root = root.children[0]

    return root

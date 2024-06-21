import pickle

from anytree import RenderTree
from anytree.search import findall

from .anytree_vis import tree_vis
from .my_field_node import MyFieldNode
from .labelling_bytes import label_bytes_with_model, label_bytes_uniform


def byte_str_to_bytes(byte_str):
    return bytes.fromhex(byte_str.lower())


class PacketFieldTreeV2:
    """ doc string"""

    FIELD_LENGTHS = {
        'UINT8': 1,
        'UINT32': 4,
        'UINT16': 2,
        'IPv4': 4,
        'ABSOLUTE_TIME': 8,
        'ETHER': 6,
        'STRING': 81
    }

    def __init__(self, numeric_thresh=8, depth=32, sk_model=None):
        self.tree = None
        self.numeric_thresh = numeric_thresh
        self.depth = depth
        self.sk_model = sk_model

    def __str__(self):
        """ASCII-art representation of tree"""
        return str(RenderTree(self.tree))

    def __repr__(self):
        return f"Feature_Tree({self.numeric_thresh=}, {self.depth=})"

    def vis(self, filename: str):
        tree_vis(self.tree, filename)

    def show(self):
        from IPython.display import Image, display
        vis_tree = self.tree.children[0]
        new_leaves = findall(self.tree, filter_=lambda node: node.depth == self.depth)
        for leaf in new_leaves:
            leaf.children = []
        tree_vis(vis_tree, "tree", edges=False)
        display(Image(filename="tmp/tree.png"))

    def save(self, filename: str):
        with open(f"{filename}.pkl", "wb",) as file:
            pickle.dump(self, file, -1)

    def load_model(self, file_path):
        with open(file_path, "rb") as file:
            self.sk_model = pickle.load(file)

    def fit_optimise_and_show(self, X):
        self.fit(X)
        self.label_bytes()
        self.fit_optimal_pft()
        self.show()

    def create_one_byte_tree_inf_threshold(self, timestamp_packets):
        # 1byte-tree
        if self.tree is None:
            # create root node
            self.tree = MyFieldNode(id="root")

        # process remaining packets
        for time, packet_str in timestamp_packets:
            packet_bytes = byte_str_to_bytes(packet_str)
            parent = self.tree
            last_id = ''
            for i, byte in enumerate(packet_bytes):
                for node_option in parent.children:
                    if byte in [pair[1] for pair in node_option.time_byte_pairs]:
                        # Valid node exists
                        node_option.time_byte_pairs.append((time, byte))
                        parent = node_option
                        last_id = node_option.id
                        break
                else:
                    num_sibs = len(parent.children)
                    if num_sibs == 0:
                        # continue branch
                        new_id = last_id + 'A'
                    else:
                        # new branch
                        new_id = last_id + chr(65 + num_sibs)

                    new_node = MyFieldNode(id=new_id, parent=parent)
                    new_node.time_byte_pairs = [(time, byte)]
                    parent = new_node
                    last_id = new_id

    def fit(self, timestamp_packets):
        self.create_one_byte_tree_inf_threshold(timestamp_packets)
        self.tree.merge_with_siblings(self.numeric_thresh)

    def label_bytes(self):
        # label nodes with types
        if self.sk_model is not None:
            label_bytes_with_model(
                self.tree, self.sk_model, self.depth, self.FIELD_LENGTHS
            )
        else:
            label_bytes_uniform(self.tree, 'UINT8')

    def build_optimal_pft(self, node):
        length = self.FIELD_LENGTHS[node.type]

        while node.nbl < length:
            node.merge_with_children()

        for n in node.children:
            self.build_optimal_pft(n)

    def merge_dup_types(self, node):
        # merge duplicate children based on time_byte_pairs values and not leaf
        types = [c.type for c in node.children]
        uniq_values = set(types)
        if len(types) > len(uniq_values):
            for value in uniq_values:
                children_of_same_value = [c for c in node.children if c.type == value]
                for is_leaf in [True, False]:
                    children_of_same_value_leaf_state = [c for c in children_of_same_value if c.is_leaf is is_leaf]
                    if len(children_of_same_value_leaf_state) > 1 :
                        children_of_same_value_leaf_state[0].collect_childrenof_tbpairsfrom_and_delete_siblings(sibling_subset=children_of_same_value_leaf_state[1:])
        for n in node.children:
            self.merge_dup_types(n)

    # Build optimal type-tree
    def fit_optimal_pft(self):
        for n in self.tree.children:
            self.build_optimal_pft(n)
        # merge duplicates
        self.merge_dup_types(self.tree)

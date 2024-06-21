from .BasePFT import BasePFT
import pickle
from .labelling_bytes import label_bytes_with_model, label_bytes_uniform
from .transition_profile import get_trans
from copy import deepcopy

class LabelledPFT(BasePFT):
    """ doc string"""

    FIELD_LENGTHS = {
        'UINT8': 1,
        'UINT32': 4,
        'UINT16': 2,
        'IPv4': 4,
        'ABSOLUTE_TIME': 8,
        'ETHER': 6,
        'STRING': 18
    }

    def __init__(self, one_byte_tree, sk_model):
        self.one_byte_tree = one_byte_tree
        self.tree = deepcopy(one_byte_tree).tree #this will be transformed to the new labelled tree
        self.sk_model = self.load_model(sk_model)

    def fit(self):
        self.label_bytes()
        self.fit_optimal_pft()

    def load_model(self, file_path):
        with open(file_path, "rb") as file:
            return pickle.load(file)

    def label_bytes(self):
        # label nodes with types
        if self.sk_model is not None:
            label_bytes_with_model(
                self.tree, self.sk_model, self.FIELD_LENGTHS
            )
        else:
            label_bytes_uniform(self.tree, 'UINT8')

    def build_optimal_pft(self, node):
        self.sub_byte_nodes = [node.id] #list of ids that map from the one-byte

        length = self.FIELD_LENGTHS[node.type]

        while node.nbl < length:
            node.merge_with_children()
            node.trans = get_trans(node)

        for n in node.children:
            self.build_optimal_pft(n)

    def merge_dup_types(self, node):
        # merge duplicate children based on time_byte_pairs values
        types = [c.type for c in node.children]
        uniq_values = set(types)
        if len(types) > len(uniq_values):
            for value in uniq_values:
                children_of_same_value = [c for c in node.children if c.type == value]
                for is_leaf in [True, False]:
                    children_of_same_value_leaf_state = [c for c in children_of_same_value if c.is_leaf is is_leaf]
                    if len(children_of_same_value_leaf_state) > 1 :
                        children_of_same_value_leaf_state[0].collect_childrenof_tbpairsfrom_and_delete_siblings(sibling_subset=children_of_same_value_leaf_state[1:], track_ids=True)
        for n in node.children:
            self.merge_dup_types(n)

    # Build optimal type-tree
    def fit_optimal_pft(self):
        for n in self.tree.children:
            self.build_optimal_pft(n)

        # merge duplicates
        self.merge_dup_types(self.tree)

    def _transform_packet_sub_ids(self, list_of_ids):
        types, lengths = [], []
        current_idx = 0
        node_options = self.tree.children
        while current_idx < len(list_of_ids):
            id = list_of_ids[current_idx]
            for node in node_options:
                if id in node.node_contains:
                    types.append(node.type)
                    lengths.append(node.nbl*8)
                    current_idx += node.nbl
                    node_options = node.children
                    break
            else:
                print("node id not found??")
                print([n.node_contains for n in node_options], id)
                break
        return types, lengths

    def transform(self, timestamp_packets):
        byte_ids = self.one_byte_tree.transform(timestamp_packets)
        all_types, all_lengths = [], []
        for list_of_ids in byte_ids:
            types, lengths = self._transform_packet_sub_ids(list_of_ids)
            all_types.append(types)
            all_lengths.append(lengths)
        return all_types, all_lengths
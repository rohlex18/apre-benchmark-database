from anytree.node.anynode import AnyNode
from .transition_profile import get_trans


class MyFieldNode(AnyNode):
    """bespoke class to add properties for PFTv2"""

    def __init__(
        self, id=None, parent=None
    ):
        super().__init__(parent)
        self.id = id
        self.time_byte_pairs = []
        self.nbl = 1
        self.type = 'None' #syntax type
        self._1b_type = -1 #infer this from time_byte_pairs????
        self.nc = 0
        self.node_contains = [id] #the sub-bytes of the labelled tree

    def bytes_to_leaf(self):
        #assuming all descendents are 1-byte nodes
        if self.is_leaf:
            return 0
        assert set([d.nbl for d in self.descendants]) == (1), 'not 1 byte tree'
        return self.height
    
    def get_uniq_bytes(self):
        return set([tb[1] for tb in self.time_byte_pairs])

    def collect_childrenof_tbpairsfrom_and_delete_siblings(self, sibling_subset=None, track_ids=False):
        # merges node with its siblings (but duplicates children)
        if sibling_subset is None:
            sibling_subset = self.siblings
        for sib in sibling_subset:
            self.children += sib.children
            self.time_byte_pairs += sib.time_byte_pairs
            if track_ids:
                self.node_contains += sib.node_contains
            sib.parent = None

    #needed for labelled PFT
    def merge_with_children(self):
        merging_child = self.children[0]

        merging_child.collect_childrenof_tbpairsfrom_and_delete_siblings(track_ids=True)

        assert len(self.children)<2, "collect_childrenof_tbpairsfrom_and_delete_siblings didnt work?"

        # merges immediate children
        self.time_byte_pairs = self.merge_tb_pairs(merging_child)
        self.node_contains += merging_child.node_contains
        self.children = merging_child.children
        self.nbl += 1

    #needed for 1 byte pft
    def merge_with_siblings(self, thresh):
        if len(self.siblings) >= thresh: #so thresh is the total number of siblings allowed
            # merging to be done
            # gather all children and remove siblings
            self.collect_childrenof_tbpairsfrom_and_delete_siblings()

        # merge duplicate children based on time_byte_pairs values
        values = [c.get_uniq_bytes().pop() for c in self.children]
        uniq_values = set(values)
        for value in uniq_values:
            children_of_same_value = [c for c in self.children if c.get_uniq_bytes().pop() == value]
            if len(children_of_same_value)>1:
                children_of_same_value[0].collect_childrenof_tbpairsfrom_and_delete_siblings(sibling_subset=children_of_same_value[1:])

        # Build Transition Profile and Count Packets
        if self.id != 'root':
            self.trans = get_trans(self)
            ## add histogram?
            
            self.nc = len(self.time_byte_pairs) #node count

        # check no duplicates
        values = [c.time_byte_pairs[0][1] for c in self.children]
        assert len(set(values)) == len(values), print([c.get_uniq_bytes() for c in self.children])

        # continue merging
        for n in self.children:
            n.merge_with_siblings(thresh)

    def merge_tb_pairs(self, node2):
        n1_tbs = self.time_byte_pairs
        n1_tbs.sort()
        n2_tbs = node2.time_byte_pairs
        n2_tbs.sort()
        i = 0
        j = 0
        while i < len(n1_tbs) and j < len(n2_tbs):
            if n1_tbs[i][0] == n2_tbs[j][0]:
                #times match
                n1_tbs[i] = (n1_tbs[i][0], n1_tbs[i][1] + n2_tbs[j][1])
                i += 1
            #dont match so try next time in n2_tbs
            j += 1
        return n1_tbs
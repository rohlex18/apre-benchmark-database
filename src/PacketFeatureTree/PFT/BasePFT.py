from anytree import RenderTree
import pickle
from anytree.search import findall
from .anytree_vis import tree_vis

class BasePFT:
    def __str__(self):
        """ASCII-art representation of tree"""
        return str(RenderTree(self.tree))

    def __repr__(self):
        return f"Feature_Tree({self.numeric_thresh=}, {self.depth=})"

    def vis(self, filename: str):
        tree_vis(self.tree, filename)

    def show(self, attr='type'):
        from IPython.display import Image, display
        vis_tree = self.tree
        #new_leaves = findall(self.tree, filter_=lambda node: node.depth == self.depth)
        #for leaf in new_leaves:
            #leaf.children = []
        tree_vis(vis_tree, "tree", attr=attr, edges=False)
        display(Image(filename="tmp/tree.png"))

    def save(self, filename: str):
        with open(f"{filename}.pkl", "wb",) as file:
            pickle.dump(self, file, -1)
from anytree import AnyNode, RenderTree
from anytree.search import findall
from anytree.exporter import DotExporter, UniqueDotExporter
from IPython.display import Image, display

class FieldTree():
    
    def __init__(self, y_syntaxes, proto='unknown'):
        self.proto = proto
        self.y_syntaxes = [list(x) for x in set(tuple(x) for x in y_syntaxes)]
        self.tree = self.build_tree()
        self.filename = f'img/tmp_tree_{proto}.png' #self.y_syntaxes[0][0].replace(" ","")}.png'

    def __str__(self):
        return RenderTree(self.tree).__str__()

    def build_tree(self):
        root = AnyNode(id='START', name='START')
        root.leaf = False
        formats = []
        for i, syntaxes in enumerate(self.y_syntaxes):
            branch_id = 'START'
            current_node = root
            for syn in syntaxes:
                next_children = current_node.children
                branch_id += '/'+syn
                if branch_id in [c.id for c in next_children]:
                    #child match
                    current_node = findall(current_node, lambda node: node.id == branch_id)[0]
                else:
                    #no children or no child match
                    new_format = True
                    new_node = AnyNode(id=branch_id, name = syn, parent = current_node)
                    current_node = new_node
                    new_node.leaf = False
            assert len(formats)==len([node.id for node in findall(root, lambda node: node.leaf)]), f'{len(formats)=}, {len([node.id for node in findall(root, lambda node: node.leaf)])=}, {new_format, syntaxes==formats[-1]}'

            if not current_node.leaf:
                #branch finished halfway through existing branch. so make new leaf
                new_format = True
                current_node.leaf = True

            if new_format:
                assert (syntaxes not in formats)
                formats.append(syntaxes)

            assert len(formats)==len([node.id for node in findall(root, lambda node: node.leaf)]), f'{len(formats)=}, {len([node.id for node in findall(root, lambda node: node.leaf)])=}, {new_format, syntaxes==formats[-1]}' 
        return root.children[0]
    

    def visualise_tree(self):
        UniqueDotExporter(
            self.tree,
            nodeattrfunc=lambda node: f'color=green;label={node.name}',
            options=[f"rankdir=LR"],
        ).to_picture(f"{self.filename}")
        #color={node_colour(node, pred)};fontcolor={fontcolor(node)};style={style(node, pred)};label={node.name}',

    def display(self):
        self.visualise_tree()
        display(Image(filename=self.filename))

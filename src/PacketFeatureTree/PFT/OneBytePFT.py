from .BasePFT import BasePFT
from .my_field_node import MyFieldNode


def byte_str_to_bytes(byte_str):
    return bytes.fromhex(byte_str.lower())


class OneBytePFT(BasePFT):
    """ doc string"""

    def __init__(self, numeric_thresh=8, depth=32, sk_model=None):
        self.tree = None
        self.numeric_thresh = numeric_thresh
        self.depth = depth

    def create_one_byte_tree_inf_threshold(self, timestamp_packets):
        # 1byte-tree but NO numeric nodes are made here.
        if self.tree is None:
            # create root node
            self.tree = MyFieldNode(id="root")

        # process remaining packets
        for time, packet_str in timestamp_packets:
            #no 0x in packet string
            packet_bytes = byte_str_to_bytes(packet_str)[:self.depth]
            parent = self.tree
            last_id = ''
            #print(packet_str)
            for i, byte in enumerate(packet_bytes):
                #print(i, byte)
                byte = byte.to_bytes(1, byteorder='big') #big or small shouldnt matter here
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

                    #print(parent.id, new_id)
                    new_node = MyFieldNode(id=new_id, parent=parent)
                    #new_node._1b_type=byte ##Type will be inferred from time_byte_pairs
                    new_node.time_byte_pairs = [(time, byte)]
                    parent = new_node
                    last_id = new_id

    def fit(self, timestamp_packets):
        self.create_one_byte_tree_inf_threshold(timestamp_packets)
        #self.show()
        self.tree.merge_with_siblings(self.numeric_thresh)

    def _transform_packet(self, packet_str):
        packet_bytes = byte_str_to_bytes(packet_str)[:self.depth]
        result = []
        parent = self.tree
        for i, byte in enumerate(packet_bytes):
                #print(i, byte)
                byte = byte.to_bytes(1, byteorder='big') #big or small shouldnt matter here
                for node_option in parent.children:
                    #check node is enum or matches the value, time_byte_pairs takes care of this?
                    if byte in [pair[1] for pair in node_option.time_byte_pairs]:
                        # Valid node exists
                        #node_option.time_byte_pairs.append((time, byte)) append info
                        result.append(node_option.id)
                        parent = node_option
                        break
                else:
                    print('no valid path?')
        return result
    
    def transform(self, timestamp_packets):
        result = []
        for time, packet_str in timestamp_packets:
            result.append(self._transform_packet(packet_str))
        return result
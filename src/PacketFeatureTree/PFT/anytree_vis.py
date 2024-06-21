from anytree.exporter import DotExporter, UniqueDotExporter
from anytree.node.anynode import AnyNode
from anytree.search import findall


def create_tree(splits, counts, N, condense=True):
    global count_dict
    count_dict = {}
    header = splits[0][0]
    ROOT = AnyNode(name=header, id=header)
    pairs = []  # list of (parent,node) pairs

    # loop through each split and add if its a new split
    for hex_split, count in zip(splits, counts):
        print("hex_split", hex_split)
        for i in range(min(len(hex_split) - 1, N)):
            parent_str = "".join(hex_split[: i + 1])
            node_str = hex_split[i + 1]
            if (parent_str, node_str) in pairs:
                count_dict[parent_str + node_str] += count
                continue
            else:
                pairs.append((parent_str, node_str))
            # print(parent_str, node_str)
            parent = findall(ROOT, filter_=lambda node: node.id == parent_str)[0]
            # print(len(node_str))
            if (
                len(node_str) > 10 and "0x" in node_str and condense
            ):  # more than 4 bytes and is hexadecimals
                node_name = node_str[:10] + "..." + str((len(node_str) - 2) // 2) + "b"
            else:
                node_name = node_str

            new_node = AnyNode(name=node_name, parent=parent, id=parent_str + node_str)
            count_dict[parent_str + node_str] = count
    return ROOT


def tree_vis(tree, filename, attr='type', isUnique=True, edges=True, names=[]):
        print(attr)
        UniqueDotExporter(
            tree,
            nodeattrfunc=lambda node: 'color=red;style=dashed;label="%s"' % (str(getattr(node, attr))), #+ '_' + str(len(node.time_byte_pairs))),
            options=["rankdir=LR;"],
        ).to_picture(f"tmp/{filename}.png")



def get_max_dim(img_names):
    import cv2
    import numpy as np

    MAX_image_height, MAX_image_width = 0, 0
    for img in img_names:
        # read image
        img = cv2.imread(img)
        a, b, c = img.shape
        if a > MAX_image_height:
            MAX_image_height = a
        if b > MAX_image_width:
            MAX_image_width = b
    return MAX_image_height, MAX_image_width


def resize_images(img_names, MAX_image_height, MAX_image_width, H_loc):
    import cv2
    import numpy as np

    for img_name in img_names:
        img = cv2.imread(img_name)
        old_image_height, old_image_width, channels = img.shape

        # find y-axis coord of first nonewhite cell
        for i in range(old_image_width):
            col = img[:, i]
            if col.sum() != old_image_height * (255 * 3):
                vals = np.array([x.sum() for x in col])
                h = np.argmin(vals)
                break
        # create new image of desired size and color (white) for padding
        color = (255, 255, 255)
        result = np.full(
            (MAX_image_height, MAX_image_width, channels), color, dtype=np.uint8
        )

        # copy img image into top center of result image
        # compute center offset
        # we want to put h in the H_loc
        y_bottom = H_loc - h
        print(y_bottom, old_image_height, MAX_image_height, H_loc, h)
        result[y_bottom : y_bottom + old_image_height, :old_image_width] = img

        # save result
        cv2.imwrite(img_name, result)

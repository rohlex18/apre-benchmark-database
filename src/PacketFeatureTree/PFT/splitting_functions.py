"""This module contains functions useful for the manipulation of packet byte substrings."""

from itertools import groupby
from typing import Any, Iterable, Optional, Sequence, Tuple

from anytree.node.anynode import AnyNode

def ordered(obj):
    """Order the resulting PFT object to ensure consistency"""
    if isinstance(obj, dict):
        return {k: ordered(v) for k, v in sorted(obj.items(), reverse=True)}

    if isinstance(obj, list):
        lst = [ordered(x) for x in obj]
        try:
            lst.sort(key=lambda x: x["id"], reverse=True)
        except TypeError:
            pass
        except AttributeError:
            pass  # Not a valid list type
        return lst

    return obj


def all_equal(iterable: Iterable[Any]) -> bool:
    """check all equal"""
    grp = groupby(iterable)
    return next(grp, True) and not next(grp, False)  # type: ignore


def ints_to_hex(word: Sequence[int]) -> Optional[str]:
    """
    Convert sequence of integers to hex string prefixed by "0x"
    """
    if len(word) == 0:
        return None
    return "0x" + "".join([f"{x:02X}" for x in word])


def hex_to_ints(word: str) -> bytes:
    """Convert string like 0x..... to bytes"""
    return bytes.fromhex(word[2:])


def split_packet_str(packet_str: str, byte_index: int):
    """Split hex string like 0xABCD into 0xAB and 0xCD"""
    assert not (
        "NUM" in packet_str[:10] and byte_index < 4
    ), f"Splitting, {packet_str=}, {byte_index=}"
    return packet_str[: 2 + 2 * byte_index], "0x" + packet_str[2 + 2 * byte_index :]


def merge_packet_str(packet_str: str, packet_str_2: str, max_inf_byte_len: int):
    """given two byte strings append one to the other"""
    assert not (
        "NUM" in packet_str or "NUM" in packet_str_2
    ), f"Merging {packet_str=}, {packet_str_2=}, {max_inf_byte_len=}"
    string, string_2 = packet_str[2:], packet_str_2[2:]
    merge_index = max_inf_byte_len - len(string) // 2
    string += string_2[: 2 * merge_index]
    return "0x" + string, "0x" + string_2[2 * merge_index :]


def split_node(new_name, node_names, min_inf_byte_len, max_inf_byte_len):
    """Find at which information length the node needs to be split"""
    for i in range(max_inf_byte_len, min_inf_byte_len - 1, -1):
        nodes = []  # contain the nodes that must be split
        for node_name in node_names:
            if node_name[2 : 2 + 2 * i] == new_name[2 : 2 + 2 * i]:
                # match found
                nodes.append(node_name)
        if nodes:  # != []:
            return i, nodes
    return 0, []


def common_str_bytes(str1, str2):
    """gets the common byte substring"""
    res = ""
    for i in range(0, min([len(str1), len(str2)]), 2):
        if str1[i : i + 2] == str2[i : i + 2]:
            res += str1[i : i + 2]
        else:
            return res
    return res


def find_node(
    name: str, nodes: Sequence[AnyNode]
) -> Tuple[bool, Optional[AnyNode], str]:
    """Search for the node by its name"""
    best_match = ""
    for node in nodes:
        # check head matches node
        if node.name == name:
            assert (
                node.id == node.parent.id + name
            ), f"{node.parent=}, {node=}, {node.children=}"
            return True, node, name
        else:
            match = common_str_bytes(node.name, name)
            if len(match) > len(best_match):
                best_match = match
    return False, None, best_match


def edit_node(node, new_name, new_id, new_nbl):
    """Updates node properties"""
    node.name = new_name
    node.id = new_id
    node.nbl = new_nbl
    assert node.nbl > 0, f"{node=}"
    return node


def nbl(name):
    """Gets the node byte length from its name"""
    assert name[:2] == "0x", f"{name[:2]=} {name=}"
    value = (len(name) - 2) // 2
    if value == 0:
        raise ValueError(f"nbl TOO SMALL {name}")
    return value


def union(tree1, tree2):
    """Return the union of two trees"""
    if tree1 is None:
        return tree2
    if tree2 is None:
        return tree1
    # we dont care about the originals anymore!
    children = tree1.children
    children_ids = [c.id for c in children]
    for chil in tree2.children:
        if chil.id not in children_ids:
            children += (chil,)
    tree1.children = children
    return tree1


def split_dict(node, split_index):
    # when a numerical node splits we have to correct the dictionary
    assert node.name == "0xBYTE_NUM", f"{node=}"
    dict1 = {}
    dict2 = {}
    for packet_str in node.hist.keys():
        count = node.hist[packet_str]
        word1, word2 = split_packet_str(packet_str, split_index)
        dict1[word1] = dict1.get(word1, 0) + count
        dict1[word2] = dict1.get(word2, 0) + count
    return dict1, dict2


def merge_hist_dicts(dict1, dict2):
    """Given two histogram dictionaries, merges these into one"""
    if dict1 == {}:
        return dict2
    if dict2 == {}:
        return dict1
    lengths = [len(k) for k in dict1.keys()]
    assert max(lengths) == min(lengths), f"{dict1=}"
    lengths2 = [len(k) for k in dict2.keys()]
    assert max(lengths2) == min(lengths2), f"{dict2=}"
    assert max(lengths) == min(lengths2), f"{dict1=}, {dict2=}"
    for k in dict2.keys():
        assert k != "0xBY", f"{dict1=}, {dict2=}"
        if len(k) == max(lengths):
            dict1[k] = dict1.get(k, 0) + dict2[k]
    lengths = [len(k) for k in dict1.keys()]
    assert max(lengths) == min(lengths), f"{dict1=}"
    return dict1


def is_num_ts(ts):
    """Check if the nts is in the form [(byte_val, time)...]"""
    return type(ts[0]) != float


def merge_ts(ts1, ts2):
    """Given two times series merge together into one"""
    if ts1 == []:
        return ts2
    if ts2 == []:
        return ts1

    assert not (is_num_ts(ts1) ^ is_num_ts(ts2)), f"{ts1=}, {ts2=}"

    if is_num_ts(ts1):
        lengths = [len(x[0]) for x in ts1]
        assert min(lengths)==max(lengths)
        lengths2 = [len(x[0]) for x in ts2]
        assert min(lengths)==max(lengths)
        assert min(lengths) == min(lengths2), (ts1, ts2)
        try:
            return sorted(ts1 + ts2, key=lambda x: x[1])
        except Exception as e:
            print(e,ts1,ts2)
    
    return sorted(ts1 + ts2)

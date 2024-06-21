import numpy as np
from struct import *
from .splitting_functions import nbl


def bitwise_xor_bytes(a, b):
    result_int = int.from_bytes(a, byteorder="big") ^ int.from_bytes(b, byteorder="big")
    return result_int.to_bytes(max(len(a), len(b)), byteorder="big")

def bitwise_xor_ints(a, b, byte_length):
    result_int = a ^ b
    return result_int.to_bytes(byte_length, byteorder="big")

def byte_list_to_transition(byte_list):
    xor_ints = np.array([[unpack('B', x)[0]] for x in byte_list], dtype=np.uint8)
    bit_array = np.unpackbits(xor_ints, axis=1)
    return bit_array.sum(axis=0).tolist()

def get_trans(node):
        """get transition profile of the node"""
        points = len(node.time_byte_pairs)
        result = []
        size = node.nbl
        data = [int.from_bytes(x[1], byteorder='big') for x in node.time_byte_pairs]
        if len(set(data))==1:
            return [0]*(8*size)
        xor = [bitwise_xor_ints(data[i], data[i+1], size) for i in range(points-1)]
        for byte_index in range(0, size):
            result += byte_list_to_transition([x[byte_index:byte_index+1] for x in xor])
        return result

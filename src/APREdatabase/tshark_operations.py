import pandas as pd
import subprocess
from APREdatabase import touch_file


from json import JSONDecoder

def list_is_raw_tshark_val(my_list):
    try:
        conditions = [
             type(my_list) is list,
             len(my_list) == 5,
             type(my_list[0]) is str,
            ]
        for i in range(1,5):
            conditions.append(type(my_list[i]) is int)
        return all(conditions)
    except Exception as e:
        return False

def get_all_pairs(d):
    for pairs in d:
        #print('here',pairs)
        if type(pairs) is tuple:
            if list_is_raw_tshark_val(pairs[1]):
                #if list_is_raw_tshark_val(pairs[1]):
                yield pairs
            elif type(pairs[1]) is list:
                yield from get_all_pairs(pairs[1])
        elif type(pairs) is list:
            try:
                yield from get_all_pairs(pairs)
            except Exception as e:
                #print(e, pairs)
                x=1
            #print(pairs)

def sort_pyshark_pairs(pairs):
    try:
        pairs = sorted(pairs, key = lambda val: val[1][1] - val[1][3]/(2**(8*val[1][2])))
    except Exception as e:
        print(e, [len(v[1]) for v in pairs])
        
    #values should also be unique
    new_pairs = []
    vals = []
    for p in pairs:
        v = p[1]
        if v[1:] not in vals:
            vals.append(v[1:])  #weird case in modbus we have different seen values (v[0] for the same value list????
            new_pairs.append(p)
    return new_pairs
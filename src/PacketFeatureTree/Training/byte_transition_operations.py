import numpy as np
from APREdatabase import parse_df_to_X_y, load_formats, get_capture_csvs
from struct import *
import pandas as pd

def bitwise_xor_bytes(a, b):
    result_int = int.from_bytes(a, byteorder="big") ^ int.from_bytes(b, byteorder="big")
    return result_int.to_bytes(max(len(a), len(b)), byteorder="big")

def byte_list_to_transition(byte_list):
    xor_ints = np.array([[unpack('B', x)[0]] for x in byte_list], dtype=np.uint8)
    bit_array = np.unpackbits(xor_ints, axis=1)
    return bit_array.sum(axis=0).tolist()

def transition_profile_1byte(data):
    size = len(data[0])
    points = len(data)
    assert size == 1
    if points == 1 or len(set(data))==1:
        return [0]*8
    #if points == 1 and size 
    result = []
    xor = [bitwise_xor_bytes(data[i], data[i+1]) for i in range(points-1)]
    for byte_index in range(0, size):
        result += byte_list_to_transition([x[byte_index:byte_index+1] for x in xor])
    return result  

def avg_bit(data):
    assert  len(data[0]) == 2
    try:
        data_ints = np.array([[int(x,16)] for x in data],  dtype=np.uint8)
        bit_array = np.unpackbits(data_ints, axis=1)
    except Exception as e:
        print(e,data)
    return np.average(bit_array, axis=0).astype(np.float64)

def get_powers_of_two(n):
    res = [32]
    while res[-1] <= n//2:
        res.append(res[-1]*2)
    return res

def build_transition_profiles(protocol_dict, protocols, rel_to_root='', start_dir='../src/APREdatabase/Protocols/'):
    ''' BUILD TRANSITION CSV '''
    all_syntaxes = []
    #[f'Bit {i} AV' for i in range(8)]
    FULL_DF = pd.DataFrame(columns=[f'Bit {i} TP' for i in range(8)] + [f'Bit {i} AV' for i in range(8)] + ['Class', 'Index', 'Length', 'Protocol', 'Trace ID', '# Trace Fields'])
    for protocol in protocols:
        print(protocol)
        formatDF = load_formats(protocol_dict, protocol, rel_to_root=rel_to_root)
        for cap_id, capture_csv in enumerate(get_capture_csvs(protocol, rel_to_root=rel_to_root)):
            print(f'{cap_id=}')
            for format_id in capture_csv['FormatID'].unique():
                #print(capture_csv[capture_csv['FormatID']==format_id])
                X, y_lengths, y_syntaxes, _ = parse_df_to_X_y(capture_csv[capture_csv['FormatID']==format_id], formatDF)
                f_lengths = y_lengths[0]
                f_syntaxes = y_syntaxes[0]
                cur_ind = 0
                #print(f_lengths, f_syntaxes)
                for leng, syn in zip(f_lengths, f_syntaxes):
                    byte_l = leng//8
                    #print(byte_l, cur_ind, X[0], X[-1])
                    #for data in X:
                    #    print(data[cur_ind: cur_ind + byte_l].zfill(byte_l*2))
                    data_strings = [data[1][cur_ind: cur_ind + byte_l].zfill(byte_l*2) for data in X]
                    for b in range(byte_l):
                        cur_ind += 1
                        byte_strings = [x[b*2:(b+1)*2] for x in data_strings]
                        for sub_len in get_powers_of_two(len(byte_strings)):
                            sub_byte_strings = byte_strings[:sub_len]
                            if set(sub_byte_strings) != {'00'}:
                                try:
                                    tp = transition_profile_1byte([bytes.fromhex(x) for x in sub_byte_strings])
                                except Exception as e:
                                    print(e, 'Couldnt compute TP', sub_byte_strings, 'breaking')
                                    break
                            else:
                                tp = [0]*8
                            if sum(tp) != 0:
                                tp = [x/sum(tp) for x in tp]
                            try:
                                av = avg_bit(sub_byte_strings).tolist()
                            except Exception as e:
                                print(e, sub_byte_strings)
                                print(e, 'Couldnt compute AVG', sub_byte_strings, 'breaking')
                            FULL_DF.loc[len(FULL_DF)] = tp + av + [syn, cur_ind, byte_l, protocol, f'{cap_id}_{format_id}_{sub_len}', len(f_syntaxes)]
    return FULL_DF


'''






            for file_num, header_file in enumerate(find_filenames_end_with(f"{start_dir}/{protocol}/", "_h_field_raws.csv")):
                print(header_file)
                if '-0_fields' in header_file or '-1_fields' in header_file:
                    continue
                name_file = header_file[:-8]+'names.csv'
                try:
                    names = pd.read_csv(name_file, header=None).iloc[0].values
                except Exception as e:
                    print(e, 'continuing')
                    continue
                syntax_file = header_file[:-8]+'syntaxes.csv'
                syntaxes = pd.read_csv(syntax_file, header=None).iloc[0].values
                byte_syntax = []
                try:
                    file_len = int(header_file.split('fields')[0].split('-')[-1][:-1])
                    assert len(syntaxes) == file_len, f"{len(syntaxes)=} {file_len=}"
                except Exception as e:
                    print(e, 'number of syntaxes doesnt match filename')
                    continue
                    
                bit_length_file = header_file[:-14]+'bit_lengths.csv'
                bit_lengths = pd.read_csv(bit_length_file, header=None).iloc[0].values
                data = pd.read_csv(header_file, header=None, dtype=str)
                byte_index = -1
                for i, name in enumerate(syntaxes):
                    l =  bit_lengths[i]//4
                    data_strings = [str(x).zfill(l) for x in data[i].values]
                    for b in range(l//2):
                        byte_index += 1
                        byte_syntax.append(syntaxes[i])
                        byte_strings = [x[b*2:(b+1)*2] for x in data_strings]
                        for sub_len in get_powers_of_two(len(byte_strings)):
                            sub_byte_strings = byte_strings[:sub_len]
                            uniq_sub_byte_strings = set(sub_byte_strings)
                            if set(sub_byte_strings) != {'00'}:
                                try:
                                    tp = transition_profile_1byte([bytes.fromhex(x) for x in sub_byte_strings])
                                except Exception as e:
                                    print(e, 'Couldnt compute TP', sub_byte_strings, 'breaking')
                                    break
                            else:
                                tp = [0]*8
                                
                            if sum(tp) != 0:
                                tp = [x/sum(tp) for x in tp]
                            try:
                                av = avg_bit(sub_byte_strings).tolist()
                            except Exception as e:
                                print(e, sub_byte_strings)
                                print(e, 'Couldnt compute AVG', sub_byte_strings, 'breaking')
                            FULL_DF.loc[len(FULL_DF)] = tp + av + [syntaxes[i], byte_index, l//2, protocol, f'{file_num}_{sub_len}', len(syntaxes)]
    return FULL_DF'''
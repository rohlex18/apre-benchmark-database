import pandas as pd
from .tshark_operations import list_is_raw_tshark_val
from .WiresharkField import WiresharkField, UnknownField

class WiresharkPacket():
    def __str__(self):
        return f"{self.layer_name=}, {self.raw_hex=}, {self.pkt_len=}, {len(self.pkt_fields)=}, {self.pkt_fields=}, {self.byte_lengths=}, {self.ws_syntaxes}, {self.ws_semantics}"
    
    def __init__(self, protocol, json_time, json_packet, syntaxes, semantics):
        self.json_packet = json_packet
        self.layer_name = protocol
        self.datetime = json_time["_source"]["layers"]["frame.time"][0]
        self.time = pd.Timestamp(self.datetime, tz=None).timestamp()
        self.raw_field, *self.pkt_fields = [WiresharkField(self.layer_name, field_pair, syntaxes, semantics) 
                                    for field_pair in self.get_all_pairs(self.json_packet)]
        self.raw_bytes = self.raw_field.raw_bytes
        self.raw_hex = self.raw_field.raw_hex
        self.pkt_len = len(self.raw_bytes)

        #print('before', self.raw_hex, self.pkt_fields)
        self.pkt_fields, self.offsets = self.get_byte_fields()

        self.bit_lengths = [f.bit_length for f in self.pkt_fields]
        self.byte_lengths = [f.byte_length for f in self.pkt_fields]
        self.ws_syntaxes = [f.ws_syntax for f in self.pkt_fields]
        self.ws_semantics = [f.ws_semantic for f in self.pkt_fields]
        
        #print('after', self)
        assert len(self.raw_bytes) == sum(self.byte_lengths), self

    def get_all_pairs(self, json_data):
        # returns pairs of field,value that match the layername.
        for i, pairs in enumerate(json_data):
            #print(pairs)
            if type(pairs) is tuple:
                if self.layer_name in pairs[0] and list_is_raw_tshark_val(pairs[1]):# and pairs[0]!=f'{self.layer_name}.frame_raw':
                    #print(i,pairs)
                    if pairs[0] == self.layer_name + '_raw':
                        yield pairs
                    elif i+1 == len(json_data):
                        yield pairs
                    elif pairs[0] != json_data[i+1][0] + '_raw':
                        yield pairs

                elif type(pairs[1]) is list:
                    yield from self.get_all_pairs(pairs[1])
            elif type(pairs) is list:
                yield from self.get_all_pairs(pairs)

    def get_byte_fields(self):
        res = []
        offsets_taken = []
        self.layer_start = self.pkt_fields[0].offset
        next_offset = self.layer_start
        last_offset = next_offset + self.pkt_len
        for f in self.pkt_fields:
            o = f.offset
            if o >= last_offset:
                #reached end of layer
                break
            if o < next_offset or f.id==f'{self.layer_name}_raw' or f.byte_length==0:
                #possible subfield
                continue
            else:
                if o > next_offset:
                    #skipped values
                    offsets_taken.append(o)
                    res.append(UnknownField(o-next_offset, next_offset-self.layer_start, self.raw_hex))

                offsets_taken.append(o)
                if f.bitmask != 0:
                    f.syntax = "FLAGS"
                res.append(f)
                next_offset = o + f.byte_length
        
        total_bytes = sum([f.byte_length for f in res])
        if len(self.raw_bytes) > total_bytes:
            offsets_taken.append(next_offset)
            #byte_length, rel_offset, layer_hex)
            res.append(UnknownField(len(self.raw_bytes)-total_bytes, next_offset-self.layer_start, self.raw_hex))
        
        
        return res, offsets_taken
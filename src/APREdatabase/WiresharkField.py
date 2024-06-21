'''
-  "881544b14f70",    # hex string
-  6,                 # position in frame
-  6,                 # length
-  0,                 # bitmask
-  29                 # type
'''

class WiresharkField():
    def __str__(self):
        return f'{self.id}-{self.bit_length}-{self.ws_syntax}-{self.ws_semantic}'
    
    def __repr__(self):
        return self.__str__()
    
    def __init__(self, protocol, field_pair, ws_syntaxes, ws_semantics):
        #print('Field Load', field_pair)
        self.id = field_pair[0]
        self.raw_hex = field_pair[1][0]
        self.offset = field_pair[1][1]
        self.byte_length = field_pair[1][2]
        self.bit_length = 8* self.byte_length
        self.bitmask = field_pair[1][3]
        self.type = field_pair[1][4]

        try:
            self.raw_bytes = bytes.fromhex(self.raw_hex.zfill(self.byte_length*2))
        except Exception as e:
            print(e, self.raw_hex, field_pair)
        
        try:
            self.ws_syntax = ws_syntaxes[self.id[:-4]][3:] #remove _raw from field id and FT_
            self.ws_semantic = ws_semantics[self.id[:-4]].replace(' ','_').replace('(','').replace(')','')
        except:
            self.ws_syntax = 'UNKNOWN'
            self.ws_semantic = 'UNKNOWN'

class UnknownField():
    def __str__(self):
        return f"{self.byte_length}ByteUnknownField"
    
    def __repr__(self):
        return self.__str__()
    
    def __init__(self, byte_length, rel_offset, layer_hex):
        self.id = "unknown"
        self.raw_hex = layer_hex[2*rel_offset:2*rel_offset+2*byte_length]
        self.offset = rel_offset
        self.byte_length = byte_length
        self.bit_length = 8* self.byte_length
        self.bitmask = 0
        self.type = 0

        self.raw_bytes = bytes.fromhex(self.raw_hex.zfill(self.byte_length*2))
        
        self.ws_syntax = "UNKNOWN"
        self.ws_semantic = "UNKNOWN"
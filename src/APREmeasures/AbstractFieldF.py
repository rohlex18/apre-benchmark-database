def convert_bit_lengths_to_byte_boundaries(bit_lengths):
    res = (0,)
    for l in bit_lengths:
        res += (l//8 + res[-1],)
    assert res[-1] == sum(bit_lengths)//8
    return res

class F:
    def __init__(self, *args, **kwargs):
        if args:
            self.b = args[0]
        if kwargs.get('F_b'):
            self.b = kwargs['F_b']
        if kwargs.get('bit_lengths'):
            self.b = convert_bit_lengths_to_byte_boundaries(kwargs['bit_lengths'])

        assert self.b[0] == 0
        self.bb = self.convert_boundaries_to_binary()
        self.bbs = ''.join([str(x) for x in self.bb])
        self.ebb = self.convert_boundaries_to_binary_extended()
        self.ebbs = ''.join([str(x) for x in self.ebb])
        self.intervals = [set(range(s,e)) for s,e in zip(self.b[0:-1],self.b[1:])]
        self.field_num = len(self.b) - 1
        
    def covers(self, G):
        for interval in self.intervals:
            if G.issubset(interval):
                return interval
        else:
            return False

    def convert_boundaries_to_binary(self):
        res = []
        for i in range(self.b[-1]+1):
            res.append(int(i in self.b))
        return res
    
    def convert_boundaries_to_binary_extended(self):
        res = []
        for i in range(self.b[-1]+1):
            res.append(int(i in self.b))
            if res[-1]==1:
                res.append(0)
        return res[:-1]
    
    
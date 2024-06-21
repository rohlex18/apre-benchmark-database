import subprocess
import json
import pandas as pd
from APREdatabase import touch_file, write_row_to_file, read_packets, read_formats, extract_csv_and_save
import os
from .WiresharkPacket import WiresharkPacket


class ParseFileWithTShark():
    def __init__(self, pcapfile: str,  layer_name: str, lua=False, t_args=''):
        self.pcapfile = pcapfile
        self.layer_name = layer_name
        self.tmp_data = "tmp/data.json"
        self.tmp_fields = "tmp/fields.csv"
        self.tmp_times = "tmp/times.json"
        self.lua_file = lua # pass to file
        self.t_args = t_args #extra args to pass to tshark
        
    def run_and_save(self):
        self.run_tshark()
        self.save_result_to_csv()
                
    def run_tshark(self):
        # get timestamp data
        p = subprocess.Popen(f"tshark -e frame.time -Tjson -r {self.pcapfile} > {self.tmp_times}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        if not self.lua_file:       
            # get packet data
            p = subprocess.Popen(f"tshark -T jsonraw  -r {self.pcapfile} {self.t_args} > {self.tmp_data}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            # get field data
            p = subprocess.Popen(f"tshark -G fields | grep -P '\t{self.layer_name}\t' | cut -f1-8 --output-delimiter=',' > {self.tmp_fields}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        else:
            print('parsing lua')
            # get packet data
            p = subprocess.Popen(f"tshark -T jsonraw -X lua_script:{self.lua_file} -r {self.pcapfile} {self.t_args} > {self.tmp_data}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            # get field data
            extract_csv_and_save(self.lua_file, self.tmp_fields)

    def read_tmp(self):
        # read packet data
        decoder = json.JSONDecoder(object_pairs_hook=lambda x: x)
        with open(self.tmp_data) as f:
            try:
                packet_data = decoder.decode(f.read()) #needed for potential duplicate keys...
            except Exception as e:
                print('failed to decode json or empty', e, f.read())

        # read timestamp data 
        with open(self.tmp_times) as f:
            json_obj_time = json.load(f)
            
        #get field data (syntax AND semantic info)
        fields_df = pd.read_csv(self.tmp_fields, header=None, names=range(20))
        semantics, FormatIDs, syntaxes = fields_df[1].values, fields_df[2].values, fields_df[3].values
       
        return zip(json_obj_time, packet_data), {i:s for i,s in zip(FormatIDs, syntaxes)}, {i:t for i,t in zip(FormatIDs, semantics)}
                
    def parse_tshark(self):
        zipped_json_obj, syntaxes, semantics = self.read_tmp()
        #now loop through each packet
        for json_time, json_pkt in zipped_json_obj:
            #print("her")
            try:
                pkt = WiresharkPacket(self.layer_name, json_time, json_pkt, syntaxes, semantics)
                #print(pkt)
                yield pkt
            except Exception as e:
                print('Error with WiresharkPacket', e)
            
    def save_result_to_csv(self):
        #create csv for pcap specific info
        result_csv_name = '.'.join(self.pcapfile.split('.')[:-1]) + '.csv'
        print(f'writing to {result_csv_name}')
        touch_file(result_csv_name)

        #load existing formats
        format_file = '/'.join(self.pcapfile.split('/')[:-2]) + '/' + self.layer_name + '_formats.csv'
        try:
            format_csv = read_formats(format_file)
        except:
            touch_file(format_file)
            format_csv = read_formats(format_file)


        #write protocol specific info
        os.environ['PYTHONHASHSEED'] = '0'  
        for pkt in self.parse_tshark():
            FormatID = abs(hash(''.join([str(l) for l in pkt.bit_lengths] + pkt.ws_syntaxes + pkt.ws_semantics)))
            if not FormatID in format_csv['FormatID'].values:
                write_row_to_file(format_file, [FormatID, pkt.bit_lengths, pkt.ws_syntaxes, pkt.ws_semantics])
                format_csv = read_formats(format_file)
            write_row_to_file(result_csv_name, [pkt.time, FormatID, pkt.raw_bytes.hex()])
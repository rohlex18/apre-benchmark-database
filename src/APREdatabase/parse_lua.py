import re
import csv

def extract_csv_and_save(lua_file, output_csv_file):
    print('extract_csv')
    # Save the CSV lines to a CSV file
    with open(output_csv_file, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        #want to parse this
        #stteTileState.colors = ProtoField.protocol("lifx.stateTileState.colors", "Colors", nil, "Colors in HSBK.") --example
        #ff.origin = ProtoField.uint8("lifx.origin", "Origin", base.DEC, nil, 0xC000, "Must be zero.") -- 0b1100000000000000

        csv_lines = []

        with open(lua_file, 'r') as file:
            lines = file.readlines()

        for line in lines:
            line = line.split('ProtoField')
            try:
                line = line[1]
                syntax = 'FT_' + line.split('(')[0][1:].upper() #ignore leading .

                if syntax == 'FT_PROTOCOL':
                    continue

                params = [f.strip()[1:-1] for f in line.split('(')[1].split(')')[0].split(',')]
                id, semantic = params[:2] #base, valuestring, mask, desc = params

            except:
                #if len(line)==1:
                continue

            csv_writer.writerow(["F", semantic, id, syntax])

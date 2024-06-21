import csv
import os
import pandas as pd

def write_row_to_file(filename, row):
    with open(filename, 'a', newline='') as myfile:
        wr = csv.writer(myfile) #quoting=csv.QUOTE_ALL)
        wr.writerow(row)
        myfile.close()
        
def touch_file(filename):
    try:
        os.remove(filename)
    except:
        pass
        with open(filename, 'w') as creating_new_csv_file:
            pass

def find_pcap_files(rel_dir):
    start_dir = os.path.abspath(rel_dir)
    # Initialize an empty list to store the paths to the PCAP files
    pcap_files = []
    for root, dirs, files in os.walk(start_dir):
        if '.ipynb' in root:
            continue
        if [dirr for dirr in dirs if dirr[0]!='.']:
            # if the current directory has subdirectories, skip it
            continue
        for file in files:
            if file.endswith('.pcap') or file.endswith('.pcapng'):
                # If the file has the .pcap extension, add it to the list
                pcap_files.append(os.path.join(root, file))
    return pcap_files

def find_format_files(rel_dir):
    start_dir = os.path.abspath(rel_dir)
    # Initialize an empty list to store the paths to the PCAP files
    formats = []
    for root, dirs, files in os.walk(start_dir):
        if '.ipynb' in root:
            continue
        for file in files:
            if file.endswith('_formats.csv'):
                # If the file has the .pcap extension, add it to the list
                formats.append(os.path.join(root, file))
    return formats

def find_filenames_end_with(rel_dir, name):
    start_dir = os.path.abspath(rel_dir)
    # Initialize an empty list to store the paths to the PCAP files
    formats = []
    for root, dirs, files in os.walk(start_dir):
        print(root,dirs,files)
        if '.' in root:
            continue
        for file in files:
            if file.endswith(name):
                # If the file has the .pcap extension, add it to the list
                formats.append(os.path.join(root, file))
    return formats

def read_formats(filename):
    return pd.read_csv(filename, header=None, names=['FormatID', 'ListOfBitLengths', 'ListOfSyntaxes', 'ListOfSemantics'])

def read_packets(filename):
    return pd.read_csv(filename, header=None, names=['Timestamp', 'FormatID', 'Bytes'])
import pandas as pd
import os
import ast
from .file_operations import read_formats, read_packets

def load_protocols(rel_to_root=''):
    protocols = pd.read_csv(rel_to_root + 'metadata/protocol_data.csv')
    return dict([(row.ProtocolName, row.WiresharkName) for i,row in protocols.iterrows() if row.ReliableParsing])


def load_formats(ProtocolsDict, protocol, rel_to_root=''):
    ws_protocol = ProtocolsDict[protocol]
    format_file = f'{rel_to_root}src/APREdatabase/Protocols/{protocol}/{ws_protocol}_formats.csv' 
    return read_formats(format_file)

def get_capture_csvs(protocol, rel_to_root=''):
    print(f'Getting capture csvs for {protocol}')
    start_dir = f'{rel_to_root}src/APREdatabase/Protocols/{protocol}'
    # Initialize an empty list to store the paths to the PCAP files
    capture_csvs = []
    for root, dirs, files in os.walk(start_dir):
        if [dirr for dirr in dirs if dirr[0]!='.']:
            # if the current directory has subdirectories, skip it
            continue
        for file in files:
            if file.endswith('.csv') and '.ipynb' not in root:
                # If the file has the .pcap extension, add it to the list
                csv_path = os.path.join(root, file)
                print(csv_path)
                capture_csvs.append(read_packets(csv_path))
    return capture_csvs

def parse_df_to_X_y(capture_df, format_df):
    X = list(zip(capture_df['Timestamp'].values, capture_df['Bytes'].values))
    full_df = capture_df.merge(format_df, on='FormatID', how='left')
    return X, full_df['ListOfBitLengths'].apply(ast.literal_eval), full_df['ListOfSyntaxes'].apply(ast.literal_eval), full_df['ListOfSemantics'].apply(ast.literal_eval)

def parse_unknown_pcap_to(capture_pcap):
    
    X = list(zip(capture_df['Timestamp'].values, capture_df['Bytes'].values))
    return X

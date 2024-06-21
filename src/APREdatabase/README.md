```python
 %load_ext autoreload
%autoreload 2
```


```python
import sys
sys.path.append("..")
from scapy.all import *
import pandas as pd
import tshark_operations as to
from ParseFileWithTShark import ParseFileWithTShark
import file_operations as fo
pd.options.display.max_rows = 4000
```


```python
protocols = pd.read_csv('../../metadata/protocol_data.csv')
ProtocolsDict = dict(zip(protocols.ProtocolName, protocols.WiresharkName))
```


```python
bin(112)
```




    '0b1110000'




```python
pcapfiles = fo.find_pcap_files('/home/ajr/apre-benchmark-database/Protocols/')
for pcap in pcapfiles:
    protocol = pcap.split('/')[-3]
    ws_protocol = ProtocolsDict[protocol]
    print(ws_protocol, pcap)
    ParseFileWithTShark(pcap, ws_protocol).run_and_save()
```


```python
pcapfile = 'Protocols/FTPv6/ws_sample/ftpv6_12.pcap'
layer_name = 'ftp'
c = ParseFileWithTShark(pcapfile, layer_name)
c.run_and_save()
```

    writing to Protocols/FTPv6/ws_sample/ftpv6_12.csv



```python
pcapfile = 'Protocols/ARP/pcap1/arp_1024.pcap'
layer_name = 'arp'
ParseFileWithTShark(pcapfile, layer_name).run_and_save()
```

    writing to Protocols/ARP/pcap1/arp_1024.csv



```python
for form in fo.find_format_files('/home/ajr/apre-benchmark-database/Protocols/'):
    print(form)
    #os.remove(form)
```


```python

```

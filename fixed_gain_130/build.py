"""Build the point simulator and local validation libraries."""
import subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
for source,destination,shared in [('network.cpp','network',False),('network.cpp','network.so',True),('point_cell.cpp','point_cell.so',True)]:
    command=['g++','-O3','-std=c++17','-ffp-contract=off']
    if shared:command+=['-shared','-fPIC']
    subprocess.run(command+[str(P/source),'-o',str(P/destination)],check=True)

from pathlib import Path
import subprocess
P=Path(__file__).resolve().parent
for source,dest,shared in [('network.cpp','network',False),('network.cpp','network.so',True),('point_cell.cpp','point_cell.so',True)]:
    args=['g++','-O3','-std=c++17','-ffp-contract=off']
    if shared:args+=['-shared','-fPIC']
    subprocess.run(args+[str(P/source),'-o',str(P/dest)],check=True)

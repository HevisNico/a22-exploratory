from pathlib import Path
import subprocess
P=Path(__file__).parent
subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC','-ffp-contract=off',str(P/'point_cell.cpp'),'-o',str(P/'point_cell.so')],check=True)
s=(P/'run.py').read_text().replace('import kernel as s','import native_kernel as s').replace("OUT=P/'output'","OUT=P/'output_native'")
(P/'native_run.py').write_text(s)

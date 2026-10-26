"""Operational helper: archive the exploratory pilot, rerun seed 0 canonically.
The main launch --start-seed 1 handles the nineteen other seeds and quiet control.
"""
import time,json
from pathlib import Path
from run import run
P=Path(__file__).parent
if __name__=='__main__':
    out=P/'output'
    while not (out/'seed_0.json').exists():time.sleep(1)
    pilot=P/'pilot_not_counted';pilot.mkdir(exist_ok=True)
    for p in out.glob('seed_0*.json'):p.replace(pilot/p.name)
    print('Pilot archived; rerunning seed 0 with the final conservative preparation check',flush=True)
    print(json.dumps(run(0)),flush=True)

from pathlib import Path
import difflib
P=Path(__file__).parent
old=(P/'previous_kernel.py').read_text()
new=old.replace('freeze_at=float("inf")):', 'freeze_at=float("inf"),probe_start=4096.):')
new=new.replace('PROBES[0]','probe_start')
assert new!=old
(P/'kernel.py').write_text(new)
(P/'kernel.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='previous_kernel.py',tofile='kernel.py')))

"""Restore exact regression inputs without launching a simulation."""
import pathlib,zipfile,hashlib,shutil,json
p=pathlib.Path(__file__).resolve().parent
source=p/'reference/REFERENCE_INPUT.zip'
assert hashlib.sha256(source.read_bytes()).hexdigest()==json.loads((p/'PROTOCOL.json').read_text())['source_archive_sha256']
with zipfile.ZipFile(source) as z:
 for n in z.namelist():assert not pathlib.Path(n).is_absolute() and '..' not in pathlib.Path(n).parts
 z.extractall(p.parent/'restored')
target=p.parent/'upload/A22_targeted_noise_selectivity_diagnostic_EN(1).zip';target.parent.mkdir(exist_ok=True)
if target.exists():assert hashlib.sha256(target.read_bytes()).hexdigest()==hashlib.sha256(source.read_bytes()).hexdigest()
else:shutil.copy2(source,target)
print('Reference inputs restored. No simulation was launched.')

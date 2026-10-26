"""Package only the completed, audited corrected campaign."""
import hashlib,json,pathlib,zipfile
P=pathlib.Path(__file__).resolve().parent
def main():
    audit=json.loads((P/'AUDIT.json').read_text());validation=json.loads((P/'VALIDATION.json').read_text())
    assert audit['dataset_count']==427 and not audit['errors'] and validation['status']=='PASS'
    assert json.loads((P/'RUN_ERRORS.json').read_text())==[]
    excluded={'experiment','fixture_bridge','MANIFEST_SHA256.json'}
    files=[p for p in sorted(P.rglob('*')) if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts and p.suffix not in ['.tmp','.pyc']]
    manifest={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    m=P/'MANIFEST_SHA256.json';m.write_text(json.dumps(manifest,indent=2));files.append(m)
    dest=P.parent/'A22_corrected_energy_matched_rerun_EN.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,'A22_corrected_energy_EN/'+str(p.relative_to(P)))
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
    print(json.dumps(dict(path=str(dest),bytes=dest.stat().st_size,files=len(files),sha256=hashlib.sha256(dest.read_bytes()).hexdigest())))
if __name__=='__main__':main()

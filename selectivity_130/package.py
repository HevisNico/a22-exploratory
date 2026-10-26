import hashlib,json,pathlib,zipfile
P=pathlib.Path(__file__).resolve().parent
def main():
    audit=json.loads((P/'AUDIT.json').read_text());assert not audit['errors'] and audit['datasets']==2562
    assert json.loads((P/'RUN_ERRORS.json').read_text())==[]
    excluded={'experiment','unit','MANIFEST_SHA256.json'}
    files=[f for f in sorted(P.rglob('*')) if f.is_file() and f.name not in excluded and '__pycache__' not in f.parts and f.suffix not in ['.tmp','.pyc','.finalizing']]
    manifest={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files};m=P/'MANIFEST_SHA256.json';m.write_text(json.dumps(manifest,indent=2));files.append(m)
    dest=P.parent/'A22_directional_selectivity_EN.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in files:z.write(f,'A22_directional_selectivity_EN/'+str(f.relative_to(P)))
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
    print(json.dumps(dict(path=str(dest),bytes=dest.stat().st_size,files=len(files),sha256=hashlib.sha256(dest.read_bytes()).hexdigest())))
if __name__=='__main__':main()

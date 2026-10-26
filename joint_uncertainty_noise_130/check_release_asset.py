"""Check publication files and, optionally, the original pilot ZIP. No simulation."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parent

def need(value, message):
    if not value:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', nargs='?', type=Path)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'PUBLISHED_FILES_SHA256.json').read_text())
    for name, expected in manifest.items():
        path = ROOT / name
        need(path.is_file() and digest(path.read_bytes()) == expected,
             'Published file mismatch: ' + name)
    print('PASS_PUBLISHED_FILES', len(manifest))
    if args.archive is None:
        return
    meta = json.loads((ROOT / 'RELEASE_ASSET.json').read_text())
    blob = args.archive.read_bytes()
    need(len(blob) == meta['bytes'] and digest(blob) == meta['sha256'],
         'Wrong or changed Release archive')
    with zipfile.ZipFile(args.archive) as z:
        names = z.namelist()
        need(len(names) == len(set(names)), 'Duplicate archive members')
        for name in names:
            part = PurePosixPath(name)
            need(not part.is_absolute() and '..' not in part.parts,
                 'Unsafe archive member: ' + name)
        prefix = meta['archive_root'] + '/'
        original = z.read(prefix + 'MANIFEST_SHA256.json')
        need(original == (ROOT / 'ARCHIVE_MANIFEST_SHA256.json').read_bytes(),
             'Original manifest differs from published copy')
        inner = json.loads(original)
        expected_names = {prefix + name for name in inner}
        expected_names.add(prefix + 'MANIFEST_SHA256.json')
        need(set(names) == expected_names, 'Unexpected or missing archive members')
        for name, expected in inner.items():
            need(digest(z.read(prefix + name)) == expected,
                 'Archive file mismatch: ' + name)
        read = lambda name: json.loads(z.read(prefix + name))
        lock = read('SOURCE_LOCK.json')
        need(digest(z.read(prefix + 'PROTOCOL.json')) == lock['protocol'], 'Protocol lock')
        for name, expected in lock['sources'].items():
            need(digest(z.read(prefix + 'src/' + name)) == expected, 'Source lock: ' + name)
        for name, expected in lock['binaries'].items():
            need(digest(z.read(prefix + 'bin/' + name)) == expected, 'Binary lock: ' + name)
        for filename, key in [('pilot.py', 'runner'), ('verify.py', 'checker')]:
            need(digest(z.read(prefix + filename)) == lock[key], key + ' lock')
        protocol = read('PROTOCOL.json')
        trains = evaluations = 0
        for seed in protocol['seeds']:
            for arm in protocol['arms']:
                stem = f'results/s{seed}_{arm}'
                train = read(stem + '_train.json')
                need(read(stem + '_JOB_STATUS.json')['status'] == 'SOLVER_COMPLETED',
                     'Incomplete solver job: ' + stem)
                field = 'fields/' + ('nominal.txt' if arm.startswith('nominal') else f's{seed}.txt')
                field_hash = digest(z.read(prefix + field))
                state_hash = digest(z.read(prefix + stem + '_train.json.states'))
                need(train['_provenance']['field_sha256'] == field_hash, 'Training field provenance')
                need(train['_provenance']['state_sha256'] == state_hash, 'Training checkpoint provenance')
                need(train['_provenance']['binary_sha256'] == lock['binaries']['train'], 'Training binary provenance')
                trains += 1
                for mode in ['baseline', 'mixed']:
                    d = read(stem + '_' + mode + '.json')
                    pr = d['_provenance']
                    need(pr['field_sha256'] == field_hash and pr['state_sha256'] == state_hash,
                         'Evaluation field/checkpoint provenance')
                    need(pr['binary_sha256'] == lock['binaries']['evaluate'], 'Evaluation binary provenance')
                    evaluations += 1
        need((trains, evaluations) == (24, 48), 'Pilot accounting mismatch')
        print('PASS_ORIGINAL_ARCHIVE', len(inner), 'hashed files')
        print('PASS_ACCOUNTING_AND_PROVENANCE', trains, 'acquisitions;', evaluations, 'evaluations')

if __name__ == '__main__':
    main()

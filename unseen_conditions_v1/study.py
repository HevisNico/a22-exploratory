"""Explicit, gated phases. Import, help, plan and build never run a simulation."""
import argparse
import concurrent.futures
import contextlib
import datetime as dt
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import threading
import time

import config as c
import scoring

OK = 'OK_POINT_NOT_CERTIFIED'
REFUSED = 'SIMULATOR_REFUSAL_NUMERICALLY_UNASSESSED'
UNAVAILABLE = 'ACQUISITION_UNAVAILABLE'
ABORT = threading.Event()


class StudyError(RuntimeError):
    pass


class GateError(StudyError):
    pass


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def source_files():
    names = ['PROTOCOL.md', 'README_EN.md', 'IMPLEMENTATION_NOTES.md', 'driver.cpp',
             'config.py', 'study.py', 'scoring.py', 'inference.py', 'analysis.py',
             'validation.py', 'requirements.txt', 'LICENSE', 'LICENSE-docs.md',
             'registration.example.json', 'selection_evidence.example.json', 'test_gates.py']
    files = [c.ROOT/name for name in names]
    files += sorted((c.ROOT/'vendor').glob('*'))
    files += sorted((c.ROOT/'reference_vendor').glob('*'))
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        raise StudyError('Missing source files: '+', '.join(missing))
    return files


def build():
    if (c.ROOT/'runs').exists() or (c.ROOT/'registration.json').exists():
        raise GateError('Build in a fresh source copy; a run/registration already exists.')
    output = c.ROOT/'build'
    output.mkdir(exist_ok=True)
    for name, flags in [('driver', []), ('driver_reference', ['-DREFERENCE_KERNEL'])]:
        subprocess.run(['g++', '-std=c++17', '-O3', *flags, 'driver.cpp', '-o', str(output/name)],
                       cwd=c.ROOT, check=True)
    sources = {str(f.relative_to(c.ROOT)): sha(f) for f in source_files()}
    write(c.ROOT/'SOURCE_LOCK.json', dict(sources=sources, binaries={name: sha(output/name)
          for name in ('driver', 'driver_reference')}, protocol_basis=c.PROTOCOL_REVISION,
          built_at=utcnow(), python=sys.version, platform=platform.platform(),
          compiler=subprocess.check_output(['g++', '--version'], text=True).splitlines()[0]))
    print('Compiled both drivers; no numerical fixture or simulation was run.')


def check_sources():
    lock = c.ROOT/'SOURCE_LOCK.json'
    if not lock.is_file():
        raise GateError('Run the compile-only build step first.')
    d = read(lock)
    for name, expected in d['sources'].items():
        if sha(c.ROOT/name) != expected:
            raise GateError('Source changed after build: '+name)
    for name, expected in d['binaries'].items():
        if sha(c.ROOT/'build'/name) != expected:
            raise GateError('Binary changed after build: '+name)
    return sha(lock)


def require_registration():
    evidence_file = c.ROOT/'registration.json'
    if not evidence_file.is_file():
        raise GateError('Registration gate closed: registration.json is absent. No simulation started.')
    lock = check_sources()
    e = read(evidence_file)
    try:
        protocol, tag, main, implementation = (e[k] for k in ('protocol', 'tag', 'main', 'implementation'))
        for revision in (protocol['commit_sha'], implementation['commit_sha']):
            if not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision):
                raise ValueError('A full protocol and implementation SHA is required')
        if protocol['sha256'] != sha(c.ROOT/'PROTOCOL.md'):
            raise ValueError('Protocol hash does not match the registered document')
        if not protocol['pull_request_url'].startswith('https://github.com/HevisNico/a22-exploratory/pull/'):
            raise ValueError('Merged protocol PR URL required')
        if not protocol['merge_event_evidence_url'].startswith('https://'):
            raise ValueError('Server-recorded merge evidence required')
        dt.datetime.fromisoformat(protocol['server_merged_at'].replace('Z', '+00:00'))
        if tag['name'] != 'prereg-unseen-conditions-v1' or tag['target_commit_sha'] != protocol['commit_sha']:
            raise ValueError('Preregistration tag target differs')
        if tag['protected'] is not True or not tag['protection_evidence_url'].startswith('https://'):
            raise ValueError('Protected tag evidence required')
        for name in ('reviewed_pr_required', 'force_pushes_blocked', 'deletions_blocked', 'required_checks_verified'):
            if main[name] is not True:
                raise ValueError('Main protection evidence incomplete: '+name)
        if not main['evidence_url'].startswith('https://') or not isinstance(main['bypass_permissions'], list):
            raise ValueError('Main rules and bypass permissions must be documented')
        if implementation['source_lock_sha256'] != lock or not implementation['evidence_url'].startswith('https://'):
            raise ValueError('Registered implementation hash/evidence differs')
        if not isinstance(e['reviewer_attestation'], str) or not e['reviewer_attestation'].strip():
            raise ValueError('A review of actual public evidence must be attested')
        external = e.get('external_deposit')
        if external:
            if not external['published_url'].startswith('https://') or external['protocol_sha256'] != protocol['sha256']:
                raise ValueError('External deposit evidence differs')
            dt.datetime.fromisoformat(external['service_published_at'].replace('Z', '+00:00'))
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise GateError('Registration gate closed: '+str(exc)) from exc
    return dict(source_lock_sha256=lock, registration_sha256=sha(evidence_file), evidence=e)


def require_validation():
    reg = require_registration()
    f = c.ROOT/'validation'/reg['source_lock_sha256']/'VALIDATION.json'
    if not f.is_file() or read(f).get('status') != 'PASS':
        raise GateError('Numerical validation has not passed for the registered source lock.')
    if read(f).get('registration_sha256') != reg['registration_sha256']:
        raise GateError('Registration evidence changed after numerical validation.')
    for name, expected in read(f)['files'].items():
        if sha(f.parent/name) != expected:
            raise StudyError('Numerical validation artifact changed: '+name)
    reg['validation_sha256'] = sha(f)
    return reg


def verify_job(f):
    d = read(f)
    for name, expected in d.get('files', {}).items():
        if Path(name).name != name or sha(Path(f).parent/name) != expected:
            raise StudyError('Saved result hash mismatch: '+str(f))
    return d


def require_selection():
    reg = require_validation()
    selection = c.ROOT/'runs'/'DESIGN_SELECTION.json'
    evidence = c.ROOT/'selection_evidence.json'
    if not selection.is_file() or not evidence.is_file():
        raise GateError('Held-out gate closed: committed design selection evidence is absent.')
    s, e = read(selection), read(evidence)
    if s['registration_sha256'] != reg['registration_sha256'] or e.get('selection_sha256') != sha(selection):
        raise GateError('Committed selection hash or registration differs.')
    if not re.fullmatch(r'[0-9a-f]{40}', e.get('commit_sha') or '') or not (e.get('evidence_url') or '').startswith('https://'):
        raise GateError('Full public design-selection commit and evidence URL are required.')
    if e.get('source_lock_sha256') != reg['source_lock_sha256']:
        raise GateError('Design selection belongs to a different implementation.')
    for name, expected in s['design_metadata_sha256'].items():
        f = c.ROOT/'runs'/name
        if sha(f) != expected:
            raise StudyError('Design results changed after selection.')
        verify_job(f)
    reg.update(selection=s, selection_sha256=sha(selection), selection_evidence_sha256=sha(evidence))
    return reg


@contextlib.contextmanager
def phase_lock(name):
    f = c.ROOT/'RUNNING.lock'
    try:
        fd = os.open(f, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise StudyError('Another phase is running, or an interrupted run needs manual audit.') from exc
    with os.fdopen(fd, 'w') as out:
        json.dump(dict(phase=name, pid=os.getpid(), started_at=utcnow()), out)
    try:
        yield
    finally:
        f.unlink(missing_ok=True)


def deadline_check(start=False):
    f = c.ROOT/'runs'/'CAMPAIGN_CLOCK.json'
    if not f.exists():
        if not start:
            raise StudyError('Campaign clock missing')
        write(f, dict(started_at=utcnow(), started_unix=time.time(), limit_seconds=c.CAMPAIGN_SECONDS))
    clock = read(f)
    if time.time()-clock['started_unix'] >= c.CAMPAIGN_SECONDS:
        raise StudyError('12-hour campaign wall-clock limit reached; study remains incomplete.')


def write_matrix(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(' '.join(format(x, '.17g') for x in row)+'\n' for row in rows))


def generate_inputs(group, device, selection_authorization=None):
    # Never call this for test before require_selection has returned.
    if group == 'test':
        if selection_authorization is None:
            require_selection()
        elif sha(c.ROOT/'runs'/'DESIGN_SELECTION.json') != selection_authorization['selection_sha256']:
            raise GateError('Design selection changed before input generation')
    folder = c.ROOT/'runs'/'inputs'/group/str(device)
    meta = folder/'INPUTS.json'
    if meta.exists():
        d = read(meta)
        for name, expected in d['files'].items():
            if sha(folder/name) != expected:
                raise StudyError('Physical input hash mismatch')
        return folder
    folder.mkdir(parents=True, exist_ok=True)
    key = c.namespace(group, device, 'shared', 'physical')
    nominal = c.nominal_physics()
    fields = [[nominal[p % 5]*(1+1e-4*(2*c.counter_uniform(key, i*15+p)-1)) for p in range(15)]
              for i in range(1560)]
    write_matrix(folder/'physical.txt', fields)
    write_matrix(folder/'H_unity.txt', [[1.0]*3 for _ in range(1560)])
    specs = {}
    for condition in c.CONDITIONS:
        spec = c.condition_spec(group, device, condition)
        if c.reachable_outputs(spec['source_lane'], spec['cut_layer'], spec['cut_lane']) != set(range(12)):
            raise StudyError('A declared cut disconnects an output')
        half = spec['gain_half_width']
        key = c.namespace(group, device, condition, 'actuation')
        values = [[1+half*(2*c.counter_uniform(key, i*3+p)-1) for p in range(3)] for i in range(1560)]
        write_matrix(folder/(condition+'_H.txt'), values)
        specs[condition] = spec
    files = {f.name: sha(f) for f in sorted(folder.glob('*.txt'))}
    write(meta, dict(group=group, device=device, conditions=specs, files=files,
                    generator='SHA256(namespace/counter), first 53 of 64 bits, midpoint uniform',
                    paired_H='One shared file per device/condition, never drawn per arm.'))
    return folder


def job_spec(group, device, condition, mode, purpose='evaluation'):
    spec = c.condition_spec(group, device, condition)
    acquire = purpose == 'acquisition'
    drift = condition == 'post_acquisition_drift'
    return dict(group=group, device=device, condition=condition, mode=mode, purpose=purpose,
                source_lane=0 if acquire and drift else spec['source_lane'],
                cut_layer=0 if acquire and drift else spec['cut_layer'],
                cut_lane=0 if acquire and drift else spec['cut_lane'],
                n=c.ACQUISITION_PULSES if acquire else c.DESIGN_PULSES if group == 'design' else c.TEST_PULSES,
                start=0.0 if acquire else c.EVAL_START, schedule='train' if acquire else 'test',
                stage=c.STAGES[purpose], noise_seed=c.noise_seed(group, device, condition, purpose),
                H_file='H_unity.txt' if acquire and drift else condition+'_H.txt', label_offset=0)


def result_path(group, device, condition, name):
    return c.ROOT/'runs'/group/str(device)/condition/(name+'.json')


def run_job(dest, spec, inputs, registration, checkpoint=None, binary=None, enforce_deadline=True):
    if ABORT.is_set():
        raise StudyError('Phase stopped after another execution/integrity fault.')
    try:
        if check_sources() != registration['source_lock_sha256'] or sha(c.ROOT/'registration.json') != registration['registration_sha256']:
            raise StudyError('Registered source or evidence changed during execution')
    except GateError as exc:
        raise StudyError('Registered source changed during execution: '+str(exc)) from exc
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cp = Path(checkpoint) if checkpoint else None
    bind = dict(source_lock_sha256=registration['source_lock_sha256'],
                registration_sha256=registration['registration_sha256'],
                physical_sha256=sha(inputs/'physical.txt'), H_sha256=sha(inputs/spec['H_file']),
                checkpoint_sha256=sha(cp) if cp else None)
    if dest.exists():
        d = verify_job(dest)
        if d['job_spec'] != spec or d['binding'] != bind:
            raise StudyError('Cached job has different inputs/protocol: '+str(dest))
        if d['status'] not in (OK, REFUSED):
            raise StudyError('Previous execution failure requires a prospective review: '+str(dest))
        return d
    partial = dest.with_name(dest.stem+'.raw.partial')
    if partial.exists() or Path(str(partial)+'.states').exists():
        raise StudyError('Uncommitted partial output requires audit: '+str(partial))
    if enforce_deadline:
        deadline_check()
    cmd = [str(binary or c.ROOT/'build'/'driver'), spec['mode'], str(spec['noise_seed']),
           str(inputs/'physical.txt'), str(inputs/spec['H_file']), str(cp) if cp else '-',
           str(spec['source_lane']), str(spec['cut_layer']), str(spec['cut_lane']), str(spec['n']),
           format(spec['start'], '.17g'), spec['schedule'], str(spec['stage']), str(partial), str(spec['label_offset'])]
    before = time.monotonic()
    d = dict(job_spec=spec, binding=bind, started_at=utcnow(), files={})
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=c.JOB_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        d.update(status='EXECUTION_TIMEOUT', error=str(exc), seconds=time.monotonic()-before)
        write(dest, d)
        raise StudyError('A subprocess timed out; no inference is allowed.') from exc
    d['seconds'] = time.monotonic()-before
    if r.returncode:
        d.update(status=REFUSED if r.returncode == 10 else 'EXECUTION_FAILURE', error=r.stderr, returncode=r.returncode)
        write(dest, d)
        if r.returncode != 10:
            raise StudyError('Execution fault retained in '+str(dest)+': '+r.stderr)
        return d
    try:
        raw = read(partial)
        score = scoring.check_raw(raw, spec['n'], spec['label_offset'])
        states = Path(str(partial)+'.states')
        if not states.is_file():
            raise ValueError('Missing terminal checkpoint')
        raw_dest = dest.with_name(dest.stem+'.raw.json.gz')
        with raw_dest.open('wb') as out:
            with gzip.GzipFile(fileobj=out, mode='wb', mtime=0) as compressed:
                compressed.write(partial.read_bytes())
        state_dest = dest.with_name(dest.stem+'.states')
        states.replace(state_dest)
        partial.unlink()
        d.update(status=OK, score=score, work_total=raw['work_total'], work_components=raw['work_components'],
                 resource_lower_bound=raw['resource_lower_bound'], sum_delta_z=raw['sum_delta_z'],
                 sum_delta_b=raw['sum_delta_b'], files={f.name: sha(f) for f in (raw_dest, state_dest)})
        write(dest, d)
        return d
    except Exception as exc:
        d.update(status='INTEGRITY_FAILURE', error=str(exc))
        write(dest, d)
        raise StudyError('Output integrity failed; study stopped.') from exc


def raw_result(dest):
    dest = Path(dest)
    d = verify_job(dest)
    if d['status'] != OK:
        return None
    with gzip.open(dest.with_name(dest.stem+'.raw.json.gz'), 'rt') as f:
        return json.load(f)


def pool_phase(name, tasks, registration):
    ABORT.clear()
    expected = len(tasks)
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=c.WORKERS) as pool:
        futures = [pool.submit(function, *args) for function, args in tasks]
        try:
            for future in concurrent.futures.as_completed(futures):
                future.result()
                completed += 1
                status = dict(status='RUNNING', phase=name, completed_contexts=completed,
                              expected_contexts=expected, updated_at=utcnow(),
                              source_lock_sha256=registration['source_lock_sha256'])
                write(c.ROOT/'runs'/'STATUS.json', status)
                print(json.dumps(status), flush=True)
        except Exception:
            ABORT.set()
            for f in futures:
                f.cancel()
            raise


def design_context(device, condition, reg, inputs):
    for candidate in c.CANDIDATES:
        mode = f'static_{candidate:02d}'
        run_job(result_path('design', device, condition, mode), job_spec('design', device, condition, mode), inputs, reg)


def design():
    reg = require_validation()
    if (c.ROOT/'runs'/'INCOMPLETE.json').exists():
        raise GateError('An incomplete-study record requires prospective review; no automatic retry.')
    previous = c.ROOT/'runs'/'DESIGN_SELECTION.json'
    if previous.exists():
        saved = read(previous)
        if saved['source_lock_sha256'] != reg['source_lock_sha256'] or saved['registration_sha256'] != reg['registration_sha256']:
            raise GateError('Existing design selection belongs to another registration.')
        for name, expected in saved['design_metadata_sha256'].items():
            f = c.ROOT/'runs'/name
            if sha(f) != expected:
                raise StudyError('Frozen design selection data changed')
            verify_job(f)
        print('Design already selected and frozen; no search or selection rewrite performed.')
        return
    if (c.ROOT/'runs'/'inputs'/'test').exists():
        raise GateError('Held-out inputs exist; starting a new design search is forbidden.')
    with phase_lock('design'):
        deadline_check(start=True)
        inputs = {device: generate_inputs('design', device) for device in c.DESIGN_DEVICES}
        tasks = [(design_context, (device, condition, reg, inputs[device])) for device in c.DESIGN_DEVICES for condition in c.CONDITIONS]
        pool_phase('design', tasks, reg)
        deadline_check()
        scores, hashes = [], {}
        for candidate in c.CANDIDATES:
            fractions = []
            for condition in c.CONDITIONS:
                count = 0
                for device in c.DESIGN_DEVICES:
                    f = result_path('design', device, condition, f'static_{candidate:02d}')
                    d = verify_job(f)
                    hashes[str(f.relative_to(c.ROOT/'runs'))] = sha(f)
                    count += d['score']['complete_words'] if d['status'] == OK else 0
                fractions.append(count/(len(c.DESIGN_DEVICES)*2))
            scores.append(dict(candidate=candidate, family_success_fractions=fractions,
                               worst_family=min(fractions), overall=sum(fractions)/4,
                               nominal_gain_sum=c.nominal_gain_sum(candidate), b=1.1 if candidate % 2 else .5))
        winner = min(scores, key=lambda r: (-r['worst_family'], -r['overall'], *c.candidate_tie_key(r['candidate'])))
        write(c.ROOT/'runs'/'DESIGN_SELECTION.json', dict(status='DESIGN_COMPLETE_TEST_NOT_STARTED',
              selected_candidate=winner['candidate'], candidates=scores, design_metadata_sha256=hashes,
              registration_sha256=reg['registration_sha256'], source_lock_sha256=reg['source_lock_sha256'],
              selection_rule='maximin, overall, nominal gain sum, largest b, smallest ID', completed_at=utcnow()))
        write(c.ROOT/'runs'/'STATUS.json', dict(status='DESIGN_COMPLETE_AWAITING_COMMITTED_SELECTION', completed_at=utcnow()))


def unavailable_job(dest, spec, inputs, reg, cause):
    d = dict(status=UNAVAILABLE, cause=cause, job_spec=spec, binding=dict(
        source_lock_sha256=reg['source_lock_sha256'], registration_sha256=reg['registration_sha256'],
        physical_sha256=sha(inputs/'physical.txt'), H_sha256=sha(inputs/spec['H_file'])), files={})
    if dest.exists() and read(dest) != d:
        raise StudyError('Unavailable result changed on resume')
    write(dest, d)


def test_context(device, condition, reg, inputs):
    acq_path = result_path('test', device, condition, 'acquisition')
    acquired = run_job(acq_path, job_spec('test', device, condition, 'learn', 'acquisition'), inputs, reg)
    if acquired['status'] == OK:
        for line in acq_path.with_suffix('.states').read_text().splitlines():
            row = [float(x) for x in line.split()]
            if len(row) != 7 or not all(math.isfinite(x) for x in row) or row[6] != 0 or row[5] >= c.EVAL_START:
                raise StudyError('Acquisition checkpoint is not READY before the fixed evaluation date; prospective review required.')
    for arm in ('active', 'frozen'):
        dest = result_path('test', device, condition, arm)
        spec = job_spec('test', device, condition, arm)
        if acquired['status'] == OK:
            run_job(dest, spec, inputs, reg, checkpoint=acq_path.with_suffix('.states'))
        else:
            unavailable_job(dest, spec, inputs, reg, acquired['status'])
    candidates = []
    for candidate in c.CANDIDATES:
        mode = f'static_{candidate:02d}'
        d = run_job(result_path('test', device, condition, mode), job_spec('test', device, condition, mode), inputs, reg)
        candidates.append((candidate, d['score']['complete_words'] if d['status'] == OK else 0))
    oracle = min(candidates, key=lambda pair: (-pair[1], *c.candidate_tie_key(pair[0])))[0]
    oracle_path = result_path('test', device, condition, 'oracle_choice')
    choice = dict(candidate=oracle, rule='Hindsight maximum over four words; no deployable/generalization claim',
                  source_lock_sha256=reg['source_lock_sha256'])
    if oracle_path.exists() and read(oracle_path) != choice:
        raise StudyError('Oracle choice changed on resume')
    write(oracle_path, choice)
    if condition == 'post_acquisition_drift':
        for candidate in sorted({reg['selection']['selected_candidate'], oracle}):
            mode = f'static_{candidate:02d}'
            run_job(result_path('test', device, condition, f'pre_{mode}'),
                    job_spec('test', device, condition, mode, 'acquisition'), inputs, reg)


def test():
    reg = require_selection()  # Must run before ANY held-out field is materialized.
    if (c.ROOT/'runs'/'INCOMPLETE.json').exists():
        raise GateError('An incomplete-study record requires prospective review; no automatic retry.')
    if (c.ROOT/'runs'/'TEST_COMPLETE.json').exists():
        saved = read(c.ROOT/'runs'/'TEST_COMPLETE.json')
        for key in ('source_lock_sha256', 'registration_sha256', 'selection_sha256', 'selection_evidence_sha256'):
            if saved[key] != reg[key]:
                raise StudyError('Completed test belongs to another registration/selection.')
        print('Held-out campaign already completed; use analyze. No simulations repeated.')
        return
    with phase_lock('test'):
        deadline_check()
        inputs = {device: generate_inputs('test', device, reg) for device in c.TEST_DEVICES}
        tasks = [(test_context, (device, condition, reg, inputs[device])) for device in c.TEST_DEVICES for condition in c.CONDITIONS]
        pool_phase('test', tasks, reg)
        deadline_check()
        write(c.ROOT/'runs'/'TEST_COMPLETE.json', dict(status='COMPLETE', completed_at=utcnow(),
              registration_sha256=reg['registration_sha256'], source_lock_sha256=reg['source_lock_sha256'],
              selection_sha256=reg['selection_sha256'], selection_evidence_sha256=reg['selection_evidence_sha256']))
        write(c.ROOT/'runs'/'STATUS.json', dict(status='TEST_COMPLETE_AWAITING_ANALYSIS', completed_at=utcnow()))


def validate():
    reg = require_registration()
    with phase_lock('validation'):
        import validation
        validation.run(reg)


def analyze():
    reg = require_selection()
    if (c.ROOT/'runs'/'INCOMPLETE.json').exists():
        raise GateError('Incomplete-study record present: inference is forbidden.')
    complete = c.ROOT/'runs'/'TEST_COMPLETE.json'
    if not complete.is_file():
        raise GateError('No complete held-out campaign: inference is forbidden.')
    d = read(complete)
    for key in ('registration_sha256', 'source_lock_sha256', 'selection_sha256', 'selection_evidence_sha256'):
        if d[key] != reg[key]:
            raise StudyError('Final campaign binding differs: '+key)
    import analysis
    analysis.run(reg)


def plan():
    print(json.dumps(dict(status='CODE_PREPARATION_ONLY_NO_SIMULATIONS', design_devices=8, held_out_devices=32,
          condition_families=list(c.CONDITIONS), static_candidates=12, design_evaluations=384,
          held_out_static_evaluations=1536, held_out_acquisitions=128, active_or_frozen_evaluations=256,
          selected_drift_static_pre_lifetimes='32 to 64 additional jobs', numerical_validation='separate dedicated seeds',
          workers=4, raw_word_definition='128 labels, all 12 final lanes, once and in order, no extras',
          protocol_revision=c.PROTOCOL_REVISION, registration='required; currently not supplied'), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan', 'build', 'check-registration', 'validate', 'design', 'test', 'analyze'))
    command = parser.parse_args().command
    try:
        if command == 'check-registration':
            require_registration()
            print('Evidence structure and local hashes are consistent; public evidence still requires human verification.')
        else:
            globals()[command]()
    except GateError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except StudyError as exc:
        if command in ('design', 'test'):
            write(c.ROOT/'runs'/'INCOMPLETE.json', dict(status='INCOMPLETE_NO_INFERENCE', phase=command, error=str(exc), stopped_at=utcnow()))
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())

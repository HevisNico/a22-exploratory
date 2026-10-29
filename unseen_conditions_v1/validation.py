"""Deferred numerical fixtures. Nothing runs until the registration gate passes."""
import copy
import json
import math
import subprocess
import traceback
import config as c
import study as s


def compare_events(a, b, minimum_label=None):
    events = 0
    maximum = 0.0
    for left, right in zip(a['outputs'], b['outputs']):
        if minimum_label is not None:
            left = [e for e in left if e[1] >= minimum_label]
        if [e[1] for e in left] != [e[1] for e in right]:
            raise ValueError('Continuation/parity output labels differ')
        for x, y in zip(left, right):
            maximum = max(maximum, abs(x[0]-y[0]))
        events += len(left)
    if maximum > 1e-7:
        raise ValueError('Continuation/parity timing differs beyond 1e-7 model units')
    return dict(events=events, max_time_difference=maximum, output_labels_identical=True)


def state_rows(path):
    rows = [[float(x) for x in line.split()] for line in path.read_text().splitlines()]
    if len(rows) != 1560 or any(len(row) != 7 or any(not math.isfinite(x) for x in row) for row in rows):
        raise ValueError('Invalid state table')
    return rows


def run(reg):
    folder = c.ROOT/'validation'/reg['source_lock_sha256']
    report = folder/'VALIDATION.json'
    for previous in (c.ROOT/'validation').glob('*/VALIDATION.json'):
        if s.read(previous).get('status') != 'FAIL':
            continue
        amendments = reg['evidence'].get('amendments', [])
        if not any(a.get('previous_failure_sha256') == s.sha(previous)
                   and a.get('replacement_source_lock_sha256') == reg['source_lock_sha256']
                   and (a.get('public_prospective_record_url') or '').startswith('https://') for a in amendments):
            raise s.GateError('A failed validation requires a public prospective amendment before retry.')
    if report.exists():
        if s.read(report)['status'] != 'PASS':
            raise s.GateError('This implementation already failed validation; retain its failure record.')
        s.require_validation()
        print('This registered implementation already passed; no fixtures repeated.')
        return
    folder.mkdir(parents=True, exist_ok=True)
    result = dict(status='FAIL', source_lock_sha256=reg['source_lock_sha256'],
                  registration_sha256=reg['registration_sha256'], dedicated_seed=930901,
                  started_at=s.utcnow(), tolerance_model_units=1e-7)
    try:
        inputs = folder/'inputs'
        inputs.mkdir(exist_ok=True)
        nominal = c.nominal_physics()
        key = c.namespace('validation', 930901, 'shared', 'physical')
        fields = [[nominal[p % 5]*(1+1e-4*(2*c.counter_uniform(key, i*15+p)-1)) for p in range(15)] for i in range(1560)]
        s.write_matrix(inputs/'physical.txt', fields)
        s.write_matrix(inputs/'H_unity.txt', [[1.0]*3 for _ in range(1560)])
        key = c.namespace('validation', 930901, 'drift', 'actuation')
        s.write_matrix(inputs/'H_drift.txt', [[1+.2*(2*c.counter_uniform(key, i*3+p)-1) for p in range(3)] for i in range(1560)])

        def fixture(name, mode, n, start=0.0, offset=0, checkpoint=None, reference=False, H='H_unity.txt', schedule='train'):
            spec = dict(group='validation', device=930901, condition='dedicated_fixture', mode=mode,
                        purpose='fixture', source_lane=0, cut_layer=0, cut_lane=0, n=n, start=start,
                        schedule=schedule, stage=201 if schedule == 'test' else 101,
                        noise_seed=c.noise_seed('validation', 930901, 'dedicated_fixture',
                                                'test' if schedule == 'test' else 'train'),
                        H_file=H, label_offset=offset)
            f = folder/(name+'.json')
            job = s.run_job(f, spec, inputs, reg, checkpoint,
                            c.ROOT/'build'/'driver_reference' if reference else None, enforce_deadline=False)
            if job['status'] != s.OK:
                raise ValueError('Dedicated validation fixture was numerically unassessed: '+name)
            return f, s.raw_result(f)

        old_path, old = fixture('original_128', 'learn', 128, reference=True)
        full_path, full = fixture('modified_128', 'learn', 128)
        if old['outputs'] != full['outputs'] or old['work_components'] != full['work_components']:
            raise ValueError('H=1 parity with the unmodified kernel failed')
        if old_path.with_suffix('.states').read_bytes() != full_path.with_suffix('.states').read_bytes():
            raise ValueError('H=1 terminal checkpoint parity failed')
        result['unmodified_kernel_H1_parity'] = dict(all_outputs_bitwise_identical=True, work_and_states_identical=True)
        # Amendment 1: split only at a quiet point, as the study does. The continuous reference has
        # the same 512-unit quiet interval between pulses 63 and 64 (schedule 'trainquiet').
        prefix_path, _ = fixture('prefix_64', 'learn', 64)
        quiet_path, quiet = fixture('quiet_128', 'learn', 128, schedule='trainquiet')
        suffix_path, suffix = fixture('suffix_64', 'active', 64, start=8.0*63+512.0, offset=64,
                                      checkpoint=prefix_path.with_suffix('.states'))
        result['chronological_continuation'] = compare_events(quiet, suffix, minimum_label=64)
        max_parameter = max(abs(a-b) for x, y in zip(state_rows(quiet_path.with_suffix('.states')),
                            state_rows(suffix_path.with_suffix('.states'))) for a, b in zip(x[:4], y[:4]))
        if max_parameter > 1e-7:
            raise ValueError('Continued learned parameters differ')
        result['chronological_continuation']['max_parameter_difference'] = max_parameter

        static_checks = []
        for candidate in c.CANDIDATES:
            mode = f'static_{candidate:02d}'
            pre_path, _ = fixture(f'pre_{mode}', mode, 32)
            _, fresh = fixture(f'fresh_{mode}', mode, 32, start=32*8.0+512.0, H='H_drift.txt', schedule='test')
            frozen_path, continued = fixture(f'continued_{mode}', 'frozen', 32, start=32*8.0+512.0,
                                           checkpoint=pre_path.with_suffix('.states'), H='H_drift.txt', schedule='test')
            if fresh['outputs'] != continued['outputs'] or fresh['work_components'] != continued['work_components']:
                raise ValueError('Rested static shortcut is not exact: '+mode)
            if [r[:4] for r in state_rows(pre_path.with_suffix('.states'))] != [r[:4] for r in state_rows(frozen_path.with_suffix('.states'))]:
                raise ValueError('Frozen static parameters moved')
            static_checks.append(dict(candidate=candidate, outputs_and_service_work_bitwise_identical=True))
        result['all_12_static_rest_equivalence_checks'] = static_checks
        frozen_path, _ = fixture('acquired_frozen', 'frozen', 32, start=128*8.0+512.0,
                                checkpoint=full_path.with_suffix('.states'), H='H_drift.txt', schedule='test')
        if [r[:4] for r in state_rows(full_path.with_suffix('.states'))] != [r[:4] for r in state_rows(frozen_path.with_suffix('.states'))]:
            raise ValueError('Acquired frozen parameters moved')
        result['acquired_frozen_parameters_unchanged'] = True
        local = subprocess.run([str(c.ROOT/'build'/'driver'), '--selftest'], capture_output=True,
                               text=True, timeout=c.JOB_TIMEOUT)
        (folder/'LOCAL_CHECK_STDOUT.txt').write_text(local.stdout)
        (folder/'LOCAL_CHECK_STDERR.txt').write_text(local.stderr)
        if local.returncode:
            raise ValueError('Isolated check failed: '+local.stderr)
        local_checks = json.loads(local.stdout)
        if local_checks['status'] != 'PASS':
            raise ValueError('Isolated charge/work/cut self-test failed')
        s.write(folder/'LOCAL_CHECKS.json', local_checks)
        result['isolated_checks'] = local_checks
        result['paired_H_specification'] = []
        for condition in c.CONDITIONS:
            specs = [s.job_spec('validation', 930901, condition, mode) for mode in ['active', 'frozen', *[f'static_{i:02d}' for i in c.CANDIDATES]]]
            for key in ('H_file', 'source_lane', 'cut_layer', 'cut_lane', 'noise_seed', 'stage', 'start', 'n'):
                if len({spec[key] for spec in specs}) != 1:
                    raise ValueError('Arm pairing differs for '+key)
            result['paired_H_specification'].append(dict(condition=condition, all_14_modes_share_H_and_latent_test_keys=True))
        result['status'] = 'PASS'
    except Exception as exc:
        result.update(error=str(exc), traceback=traceback.format_exc())
        raise
    finally:
        result['completed_at'] = s.utcnow()
        result['files'] = {str(f.relative_to(folder)): s.sha(f) for f in sorted(folder.rglob('*')) if f.is_file() and f != report}
        s.write(report, result)
    print(json.dumps(result, indent=2))

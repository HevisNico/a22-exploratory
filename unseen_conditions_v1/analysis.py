"""Final, paired-device analysis; all static candidates and refusals are retained."""
import csv
import json
import config as c
import inference
import scoring
import study as s


def run(reg):
    ledger = []
    primary_cases = []
    word_rows = []
    device_rows = []
    oracle_rows = []
    all_h_pairings = []
    totals = {arm: 0 for arm in ('active', 'frozen', 'robust_static', 'oracle_static')}

    def checked_job(path):
        d = s.verify_job(path)
        if d['status'] not in (s.OK, s.REFUSED, s.UNAVAILABLE):
            raise s.StudyError('Execution/integrity fault prevents inference: '+str(path))
        if d['binding']['source_lock_sha256'] != reg['source_lock_sha256'] or d['binding']['registration_sha256'] != reg['registration_sha256']:
            raise s.StudyError('Job belongs to another registered implementation')
        if d['status'] == s.OK:
            scoring.check_raw(s.raw_result(path), d['job_spec']['n'], d['job_spec']['label_offset'])
        ledger.append(dict(path=str(path.relative_to(c.ROOT)), status=d['status'],
                           metadata_sha256=s.sha(path), job_spec=d['job_spec'],
                           binding=d['binding'], score=d.get('score'),
                           work_total=d.get('work_total'), work_components=d.get('work_components')))
        return d

    for device in c.TEST_DEVICES:
        cases = []
        for condition in c.CONDITIONS:
            f = lambda name: s.result_path('test', device, condition, name)
            acq = checked_job(f('acquisition'))
            adaptive = {arm: checked_job(f(arm)) for arm in ('active', 'frozen')}
            candidates = {i: checked_job(f(f'static_{i:02d}')) for i in c.CANDIDATES}
            comparison_jobs = list(adaptive.values())+list(candidates.values())
            for key in ('H_sha256', 'physical_sha256'):
                if len({d['binding'][key] for d in comparison_jobs}) != 1:
                    raise s.StudyError('Physical pairing mismatch: '+key)
            for key in ('noise_seed', 'source_lane', 'cut_layer', 'cut_lane', 'start', 'stage', 'n'):
                if len({d['job_spec'][key] for d in comparison_jobs}) != 1:
                    raise s.StudyError('Latent noise/input pairing mismatch: '+key)
            if acq['status'] == s.OK:
                expected_cp = s.sha(f('acquisition').with_suffix('.states'))
                for arm in ('active', 'frozen'):
                    if adaptive[arm]['binding'].get('checkpoint_sha256') != expected_cp:
                        raise s.StudyError('Adaptive/frozen acquisition checkpoints differ')
            all_h_pairings.append(dict(device=device, condition=condition,
                                      H_sha256=comparison_jobs[0]['binding']['H_sha256'],
                                      physical_sha256=comparison_jobs[0]['binding']['physical_sha256'],
                                      all_14_modes_matched=True))
            oracle = min(c.CANDIDATES, key=lambda i: (-(candidates[i]['score']['complete_words']
                         if candidates[i]['status'] == s.OK else 0), *c.candidate_tie_key(i)))
            if s.read(f('oracle_choice'))['candidate'] != oracle:
                raise s.StudyError('Recorded oracle differs from fixed selection rule')
            robust = reg['selection']['selected_candidate']
            pre = {}
            if condition == 'post_acquisition_drift':
                for i in sorted({robust, oracle}):
                    pre[i] = checked_job(f(f'pre_static_{i:02d}'))
                    if pre[i]['binding']['H_sha256'] != acq['binding']['H_sha256']:
                        raise s.StudyError('Pre-drift H differs across chosen static and acquired arms')
            arm_data = {'active': (adaptive['active'], acq), 'frozen': (adaptive['frozen'], acq),
                        'robust_static': (candidates[robust], pre.get(robust)),
                        'oracle_static': (candidates[oracle], pre.get(oracle))}
            case = dict(device=device, condition=condition, arms={})
            for arm, (evaluation, acquisition) in arm_data.items():
                usable = evaluation['status'] == s.OK and (acquisition is None or acquisition['status'] == s.OK)
                words = evaluation['score']['words'] if usable else [False]*4
                if len(words) != 4:
                    raise s.StudyError('Expected four held-out words')
                success = sum(words)/4
                acquire_work = acquisition['work_total'] if acquisition is not None and acquisition['status'] == s.OK else 0.0 if acquisition is None else None
                service_work = evaluation['work_total'] if evaluation['status'] == s.OK else None
                total_work = acquire_work+service_work if acquire_work is not None and service_work is not None else None
                case['arms'][arm] = dict(assessable=usable, success_fraction=success,
                                         lower_success=success if usable else 0.0,
                                         upper_success=success if usable else 1.0,
                                         acquisition_work=acquire_work, service_work=service_work,
                                         total_deployment_work=total_work,
                                         evaluation_status=evaluation['status'],
                                         prehistory_status=acquisition['status'] if acquisition else 'NOT_REQUIRED')
                totals[arm] += sum(words)
                for word, complete in enumerate(words):
                    word_rows.append(dict(device=device, condition=condition, arm=arm, word=word,
                                          complete=complete, numerically_assessable=usable,
                                          evaluation_status=evaluation['status']))
            unknown_candidate = any(d['status'] != s.OK for d in candidates.values())
            observed_oracle = candidates[oracle]['score']['complete_words'] if candidates[oracle]['status'] == s.OK else 0
            oracle_rows.append(dict(device=device, condition=condition, selected_candidate=oracle,
                                    observed_hindsight_word_count=observed_oracle,
                                    possible_upper_word_count=4 if unknown_candidate else observed_oracle,
                                    numerically_unassessed_candidates=sum(d['status'] != s.OK for d in candidates.values()),
                                    diagnostic_only=True))
            cases.append(case)
            primary_cases.append(case)
        means = {arm: sum(case['arms'][arm]['success_fraction'] for case in cases)/4 for arm in totals}
        difference = means['active']-means['robust_static']
        lower = sum(case['arms']['active']['lower_success']-case['arms']['robust_static']['upper_success'] for case in cases)/4
        upper = sum(case['arms']['active']['upper_success']-case['arms']['robust_static']['lower_success'] for case in cases)/4
        work = {}
        for arm in totals:
            values = [case['arms'][arm]['total_deployment_work'] for case in cases]
            work[arm] = sum(values) if all(x is not None for x in values) else None
        device_rows.append(dict(device=device, mean_success=means, primary_difference=difference,
                                refusal_lower_difference=lower, refusal_upper_difference=upper,
                                summed_work_over_four_scenarios=work))
    expected = 128+256+1536+sum(1 for r in ledger if '/pre_static_' in r['path'])
    if len(ledger) != expected or len({r['path'] for r in ledger}) != len(ledger):
        raise s.StudyError('Incomplete or duplicate held-out job ledger')
    statistics = inference.paired_inference([r['primary_difference'] for r in device_rows])
    pessimistic = inference.paired_inference([r['refusal_lower_difference'] for r in device_rows])
    claim = statistics['positive_by_registered_statistics'] and pessimistic['positive_by_registered_statistics']
    families = []
    for condition in c.CONDITIONS:
        rr = [r for r in primary_cases if r['condition'] == condition]
        families.append(dict(condition=condition, expected_words_per_arm=128,
                             complete_words={arm: sum(round(r['arms'][arm]['success_fraction']*4) for r in rr) for arm in totals},
                             assessable_scenarios={arm: sum(r['arms'][arm]['assessable'] for r in rr) for arm in totals}))
    cost = inference.work_summary([(r['summed_work_over_four_scenarios']['active'],
                                    r['summed_work_over_four_scenarios']['robust_static']) for r in device_rows])
    output = c.ROOT/'runs'/'analysis'
    output.mkdir(parents=True, exist_ok=True)
    with (output/'PER_WORD.csv').open('w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=list(word_rows[0]))
        writer.writeheader()
        writer.writerows(word_rows)
    for filename, data in [('ALL_JOBS.json', ledger), ('PER_DEVICE.json', device_rows),
                           ('PER_SCENARIO.json', primary_cases), ('ORACLE_DIAGNOSTIC.json', oracle_rows),
                           ('PAIRED_H_CHECKS.json', all_h_pairings)]:
        s.write(output/filename, data)
    summary = dict(status='COMPLETED_POINT_STUDY_NOT_CERTIFIED', devices=32,
                   global_static_candidate=reg['selection']['selected_candidate'], expected_words_per_arm=512,
                   complete_words=totals, family_results=families, primary_statistics=statistics,
                   pessimistic_refusal_statistics=pessimistic,
                   conclusion='ADAPTIVE_ADVANTAGE_UNDER_REGISTERED_CRITERIA' if claim else 'NO_DEMONSTRATED_ADAPTIVE_ADVANTAGE',
                   modeled_work=cost, total_saved_test_jobs=len(ledger),
                   simulator_refusals=sum(r['status'] == s.REFUSED for r in ledger),
                   acquisition_unavailable=sum(r['status'] == s.UNAVAILABLE for r in ledger),
                   registration_sha256=reg['registration_sha256'], source_lock_sha256=reg['source_lock_sha256'],
                   selection_sha256=reg['selection_sha256'], scope='Finite static family, declared distribution shift; no hardware or universal robustness claim.')
    s.write(output/'SUMMARY.json', summary)
    lines = ['# A22 held-out conditions: registered analysis', '',
             '**'+summary['conclusion']+'**', '',
             f'32 independent device blocks. Fixed robust static candidate: {summary["global_static_candidate"]}.', '',
             '| Arm | Complete words / 512 |', '|---|---:|']
    for arm, count in totals.items():
        lines.append(f'| {arm} | {count} |')
    lines += ['', 'The 512 words per arm are repeated measurements within 32 devices.', '',
              '## Primary paired-device inference', '', '```json', json.dumps(statistics, indent=2), '```', '',
              'Pessimistic bounds for all numerically unassessed paired outcomes are retained in SUMMARY.json.', '',
              '## Four preregistered families', '', '| Family | Active | Robust static | Frozen | Hindsight oracle |', '|---|---:|---:|---:|---:|']
    for r in families:
        v = r['complete_words']
        lines.append(f'| {r["condition"]} | {v["active"]}/128 | {v["robust_static"]}/128 | {v["frozen"]}/128 | {v["oracle_static"]}/128 |')
    lines += ['', 'Gain heterogeneity and post-acquisition drift were prespecified as the leading possible sources of an advantage. A gain limited to those families is not evidence for arbitrary unseen conditions.', '',
              'The oracle intentionally uses test outcomes within the finite static family. It is an optimistic diagnostic, not a deployable estimate or theoretical bound.', '',
              'Total modeled work includes acquisition for acquired arms and the pre-change lifetime for chosen drift statics. Static arms need no acquisition-only inputs in the other scenarios. This is the registered deployment comparison, not equal calibration exposure, measured hardware energy or a claim of equal delivered service.', '',
              'All static candidates, statuses, raw files and checkpoints remain available. Passive labels do not describe every residual-charge ancestor. No interval certification or independent expert review is claimed.']
    (output/'RESULTS_EN.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary, indent=2))

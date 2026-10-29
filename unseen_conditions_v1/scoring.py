"""Independent scoring of saved events, following the fixed word definition."""
import bisect
import math


def rescore(raw, offset=0):
    dates = raw['source_dates']
    if not dates or any(not math.isfinite(x) for x in dates):
        raise ValueError('Invalid source dates')
    n = len(dates)
    blocks = (n+127)//128
    complete = [True]*blocks
    boundaries = [dates[k]+15.6 for k in range(128, n, 128)]
    missing = duplicate = ambiguous = outside = order = events = pairs = 0
    square_errors = []
    if len(raw['outputs']) != 12:
        raise ValueError('Exactly twelve output lanes are required')
    for lane in raw['outputs']:
        counts = [0]*n
        times = [None]*n
        previous = -1
        previous_time = -math.inf
        for time, label in lane:
            if not math.isfinite(time) or time < previous_time or int(label) != label:
                raise ValueError('Invalid or nonchronological event')
            previous_time = time
            events += 1
            k = int(label)-offset
            if k < 0 or k >= n:
                complete[bisect.bisect_right(boundaries, time)] = False
                if label < 0:
                    ambiguous += 1
                else:
                    outside += 1
                continue
            counts[k] += 1
            times[k] = time
            if previous > k:
                order += 1
                complete[k//128] = complete[previous//128] = False
            previous = k
        for k, count in enumerate(counts):
            if count != 1:
                complete[k//128] = False
            missing += count == 0
            duplicate += max(0, count-1)
        for k in range(n-1):
            if counts[k] == counts[k+1] == 1:
                gap = dates[k+1]-dates[k]
                if gap <= 0:
                    raise ValueError('Nonpositive source gap')
                square_errors.append(((times[k+1]-times[k]-gap)/gap)**2)
                pairs += 1
    return dict(words=complete, complete_words=sum(complete), expected_words=blocks,
                missing_labels=missing, duplicate_labels=duplicate, ambiguous_events=ambiguous,
                outside_labels=outside, order_violations=order, final_events=events,
                interval_pairs=pairs,
                relative_interval_rms=math.sqrt(math.fsum(square_errors)/pairs) if pairs else None)


def check_raw(raw, n, offset=0):
    if len(raw['source_dates']) != n:
        raise ValueError('Unexpected source count')
    score = rescore(raw, offset)
    for key, value in score.items():
        if isinstance(value, float):
            if not math.isclose(raw[key], value, rel_tol=1e-10, abs_tol=1e-12):
                raise ValueError(f'Independent score differs: {key}')
        elif raw[key] != value:
            raise ValueError(f'Independent score differs: {key}')
    work = raw['work_components']
    if len(work) != 9 or any(not math.isfinite(x) or x < 0 for x in work):
        raise ValueError('Invalid work components')
    if not math.isclose(math.fsum(work), raw['work_total'], rel_tol=1e-11, abs_tol=1e-9):
        raise ValueError('Inconsistent work total')
    if not math.isfinite(raw['resource_lower_bound']) or raw['resource_lower_bound'] <= 0:
        raise ValueError('Resource feasibility unavailable')
    return score

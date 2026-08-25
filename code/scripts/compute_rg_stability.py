# -*- coding: utf-8 -*-
"""RegimeGlobal 3-seed stability: compare seed0 baseline vs seed1000/2000.

Reads regimeglobal_new_scorers.json (seed 0) and regimeglobal_seed{1000,2000}.json.
Reports per-scorer pooled L1/top1 and best-method check for the OCSVM column
(was RegimeGlobal 0.870 the seed-0 winner?)."""
import json
import numpy as np

BASE = r'D:\0科研\工作1\第10篇SCI\src\_cache'

def load(fn):
    return json.load(open(f'{BASE}\\{fn}', encoding='utf-8'))

s0 = load('regimeglobal_new_scorers.json')
seeds = {0: s0}
for sd in (1000, 2000):
    try:
        seeds[sd] = load(f'regimeglobal_seed{sd}.json')
    except FileNotFoundError:
        print(f'seed {sd} not ready')

def pooled(data, scorer):
    l1s, t1s, ns = [], [], []
    for k, v in data.items():
        if not k.startswith(scorer):
            continue
        rg = v.get('RegimeGlobal') or v.get('regimeglobal')
        if rg is None or 'error' in rg:
            continue
        if 'layer1_macro_f1' not in rg or 'layer2_top1' not in rg:
            continue
        n = int(np.sum(rg.get('layer2_hits_top1', [])))  # fallback
        l1s.append(rg['layer1_macro_f1'])
        t1s.append(rg['layer2_top1'])
        ns.append(rg.get('n_eval', 1))
    if not l1s:
        return None
    return (float(np.average(l1s, weights=ns)), float(np.average(t1s, weights=ns)),
            len(l1s))

print('scorer | seed | pooled L1 | pooled top1 | units')
for scorer in ('pca', 'ocsvm'):
    for sd in sorted(seeds):
        r = pooled(seeds[sd], scorer)
        if r:
            print(f'{scorer} | {sd} | {r[0]:.3f} | {r[1]:.3f} | {r[2]}')

# per-unit L1 spread across seeds (units present in all seeds)
common = set(seeds[0])
for sd in seeds:
    common &= set(seeds[sd])
for scorer in ('pca', 'ocsvm'):
    diffs = []
    for k in sorted(common):
        if not k.startswith(scorer):
            continue
        vals = [seeds[sd][k]['RegimeGlobal']['layer1_macro_f1'] for sd in sorted(seeds)
                if 'RegimeGlobal' in seeds[sd][k]
                and 'layer1_macro_f1' in seeds[sd][k]['RegimeGlobal']]
        if len(vals) >= 2:
            diffs.append(max(vals) - min(vals))
    if diffs:
        print(f'{scorer}: per-unit L1 max-min across seeds: median '
              f'{np.median(diffs):.3f}, mean {np.mean(diffs):.3f}, max {np.max(diffs):.3f} '
              f'({len(diffs)} units)')

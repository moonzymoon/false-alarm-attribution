# -*- coding: utf-8 -*-
"""Extend pairs table with SHAP per-pair means and recompute DAAS LOO.

Inputs: pairs_table_17.json (existing 8 methods), shap_iforest.json,
new_scorer_results_shap.json, at_ext.json, cmhmil shap (if present).
Outputs: pairs_table_shap.json + daas_shap.json (strict/tolerant, family rule,
fixed-strategy baselines, binomial CIs)."""
import json
import os
import sys
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from common import cpath  # noqa: E402


def pair_means_shap():
    out = {}
    def add(pair, d):
        vals = [v['layer2_top1'] for k, v in d.items()
                if k.startswith(prefix) and isinstance(v, dict)
                and 'layer2_top1' in v]
        if vals:
            out[pair] = float(np.mean(vals))
    # iforest pairs
    for ds in ('SWaT', 'SMD', 'MetroPT3', 'PSM', 'SMAP'):
        d = json.load(open(cpath('shap_iforest.json'), encoding='utf-8'))
        prefix = f'iforest_{ds}_'
        add(f'iforest/{ds}', d)
    # pca/ocsvm pairs
    d = json.load(open(cpath('new_scorer_results_shap.json'), encoding='utf-8'))
    for sc in ('pca', 'ocsvm'):
        for ds in ('SWaT', 'SMD', 'PSM'):
            globals()['prefix'] = f'{sc}_{ds}_'
            add(f'{sc}/{ds}', d)
    # AT pairs
    try:
        d = json.load(open(cpath('at_ext.json'), encoding='utf-8'))
        for ds in ('PSM', 'SMAP'):
            k = f'AT_{ds}_var'
            if isinstance(d.get(k), dict) and 'SHAP' in d[k] and \
                    'layer2_top1' in d[k]['SHAP']:
                out[f'AT/{ds}'] = d[k]['SHAP']['layer2_top1']
    except FileNotFoundError:
        pass
    # cmhmil shap (optional)
    try:
        d = json.load(open(cpath('shap_cmhmil.json'), encoding='utf-8'))
        for ds in ('SWaT', 'SMD', 'PSM', 'SMAP'):
            globals()['prefix'] = f'cmhmil_{ds}_'
            add(f'cmhmil/{ds}', d)
    except FileNotFoundError:
        pass
    return out


def recompute_daas(pairs):
    """pairs: {pair: {method: top1}} over the extended method set."""
    methods = set()
    for m in pairs.values():
        methods |= set(m)
    methods.discard('Random')
    # best fixed strategy over non-random methods
    fixed = {m: np.mean([pm[m] for pm in pairs.values() if m in pm])
             for m in methods}
    best_fixed = max(fixed, key=fixed.get)
    strict = tol = 0
    fam_rule = {'iforest': 'AERec', 'pca': 'RC-CA', 'ocsvm': 'RC-CA',
                'AT': 'RC-CA', 'cmhmil': 'CondAttr'}
    strict_f = tol_f = 0
    for held, pm in pairs.items():
        det = held.split('/')[0]
        train_pm = {p: v for p, v in pairs.items() if p.split('/')[0] == det and p != held}
        if not train_pm:
            continue
        cand = set.intersection(*[set(v) for v in train_pm.values()]) if train_pm else set()
        cand = {m for m in cand if m in pm}
        if not cand:
            continue
        pick = max(cand, key=lambda m: np.mean([v[m] for v in train_pm.values()]))
        best = max(pm, key=pm.get)
        if pick == best:
            strict += 1
        if pm[pick] >= pm[best] - 0.05:
            tol += 1
        # family rule: reconstruction for iforest else best counterfactual on train
        cf = ['RC-CA', 'GlobalCF', 'CondAttr', 'RegimeGlobal']
        if det == 'iforest':
            fpick = 'AERec'
        else:
            tc = [m for m in cf if all(m in v for v in train_pm.values())]
            fpick = max(tc, key=lambda m: np.mean([v[m] for v in train_pm.values()])) if tc else 'AERec'
        if fpick == best:
            strict_f += 1
        if pm[fpick] >= pm[best] - 0.05:
            tol_f += 1
    n = len(pairs)
    from scipy.stats import binomtest
    res = {
        'n_pairs': n, 'methods': sorted(methods),
        'strict': strict, 'tolerant': tol,
        'strict_frac': strict / n, 'tolerant_frac': tol / n,
        'family_strict': strict_f, 'family_tolerant': tol_f,
        'family_strict_frac': strict_f / n, 'family_tolerant_frac': tol_f / n,
        'best_fixed': best_fixed, 'best_fixed_mean': fixed[best_fixed],
        'fixed_means': fixed,
    }
    return res


def main():
    base = json.load(open(cpath('pairs_table_17.json'), encoding='utf-8'))
    shap = pair_means_shap()
    print('SHAP per-pair:', {k: round(v, 3) for k, v in shap.items()})
    pairs = {}
    for pair, m in base.items():
        pairs[pair] = dict(m)
    for pair, v in shap.items():
        if pair in pairs:
            pairs[pair]['SHAP'] = v
        else:
            pairs[pair] = {'SHAP': v}
    json.dump(pairs, open(cpath('pairs_table_shap.json'), 'w'), indent=1)
    res = recompute_daas(pairs)
    json.dump(res, open(cpath('daas_shap.json'), 'w'), indent=1)
    print(json.dumps(res, indent=1)[:900])


if __name__ == '__main__':
    main()

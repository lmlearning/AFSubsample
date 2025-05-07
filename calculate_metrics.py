#!/usr/bin/env python3

"""
Example: Match original TGF files named like:
    afinput_exp_acyclic_indvary2_step2_batch_yyy02.tgf
against subsampled TGFs named like:
    afinput_exp_acyclic_indvary2_step2_batch_yyy02_random_8.tgf

We do the following for the subsampled filenames:
  1. Remove the trailing "_<digits>" if present.
  2. Remove any trailing "_random", "_degree", "_bfs", "_community".
  3. Append ".tgf" so it matches the original key exactly.

We then average structural metrics over multiple numeric variants.
"""

import argparse
import os
import json
import math
import glob
import re
import networkx as nx
from pathlib import Path
from tqdm import tqdm

###########################
# 0) Parsing TGF & Utils  #
###########################
def parse_tgf(tgf_path):
    """Parse TGF file -> (nodes, edges)."""
    nodes = []
    edges = []
    reading_nodes = True
    with open(tgf_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if reading_nodes:
                if line == '#':
                    reading_nodes = False
                else:
                    nodes.append(line)
            else:
                parts = line.split()
                if len(parts) == 2:
                    edges.append((parts[0], parts[1]))
    return nodes, edges

def build_digraph(nodes, edges):
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    return G

###############################
# 1) Compute Structural Metrics
###############################
def compute_structural_metrics(tgf_path):
    """
    Compute four metrics: density, avg_degree, weak_connectivity, reciprocity.
    """
    nodes, edges = parse_tgf(tgf_path)
    G = build_digraph(nodes, edges)
    n = len(nodes)
    e = len(edges)

    if n < 2:
        return {
            "density": 0.0,
            "avg_degree": 0.0,
            "weak_connectivity": 0.0,
            "reciprocity": 0.0
        }

    # 1) Density
    density = e / (n * (n - 1))

    # 2) Average out-degree
    avg_degree = e / n

    # 3) Weak connectivity fraction
    UG = G.to_undirected()
    connected_components = list(nx.connected_components(UG))
    largest_cc = max((len(c) for c in connected_components), default=0)
    weak_connectivity = largest_cc / n

    # 4) Reciprocity = fraction of edges that appear in both directions
    edgeset = set(edges)
    reciprocal_count = 0
    for (u, v) in edgeset:
        if (v, u) in edgeset:
            reciprocal_count += 1
    reciprocity = reciprocal_count / e if e > 0 else 0

    return {
        "density": density,
        "avg_degree": avg_degree,
        "weak_connectivity": weak_connectivity,
        "reciprocity": reciprocity
    }

############################################
# 2) Compare Structural: Summarize Deviation
############################################
def transform_key(key, suffix):
    # Split the key into base and extension using the last dot
    if '.' in key:
        base, ext = key.rsplit('.', 1)
        return f"{base}_{suffix}"
    else:
        return f"{key}_{suffix}"
    
def compare_struct(orig_dict, sub_dict, weights=None):
    """
    Compare these four metrics with absolute differences:
      - density
      - avg_degree
      - weak_connectivity
      - reciprocity

    Returns the weighted sum of these differences (or None if missing).
    """
    if weights is None:
        weights = {
            "density": 0.25,
            "avg_degree": 0.25,
            "weak_connectivity": 0.25,
            "reciprocity": 0.25
        }

    total_dev = 0.0
    total_w   = 0.0

    # 1) density
    do = orig_dict.get("density")
    ds = sub_dict.get("density")
    if do is not None and ds is not None:
        w = weights["density"]
        total_dev += w * abs(do - ds)
        total_w   += w

    # 2) avg_degree
    ado = orig_dict.get("avg_degree")
    ads = sub_dict.get("avg_degree")
    if ado is not None and ads is not None:
        w = weights["avg_degree"]
        total_dev += w * abs(ado - ads)
        total_w   += w

    # 3) weak_connectivity
    wco = orig_dict.get("weak_connectivity")
    wcs = sub_dict.get("weak_connectivity")
    if wco is not None and wcs is not None:
        w = weights["weak_connectivity"]
        total_dev += w * abs(wco - wcs)
        total_w   += w

    # 4) reciprocity
    ro = orig_dict.get("reciprocity")
    rs = sub_dict.get("reciprocity")
    if ro is not None and rs is not None:
        w = weights["reciprocity"]
        total_dev += w * abs(ro - rs)
        total_w   += w

    if total_w == 0.0:
        return None
    return total_dev

#####################################
# 3) Extension Deviation & Combining
#####################################
def logistic_blending(e_val, T0=5.0, K=1.0):
    return 1.0 / (1.0 + math.exp(-(e_val - T0)/K))

def compute_target(e_orig, proportion, T0=5.0, K=1.0):
    if e_orig <= 0:
        return 0
    lam = logistic_blending(e_orig, T0, K)
    return (1 - lam)*e_orig + lam*(proportion * e_orig)

def ext_deviation(e_orig, e_sub, i_val):
    """Deviation for extension counts, relative to the logistic-blended target."""
    if e_orig == 0:
        return None
    return abs(e_sub - i_val) / e_orig

def combine_ext_devs(dev_list):
    """Average the valid extension deviations."""
    valid = [d for d in dev_list if d is not None]
    if not valid:
        return None
    return sum(valid)/len(valid)

############################
# 4) Key Unification Logic #
############################
METHODS = ["random", "degree", "bfs", "community"]

def unify_original_key(tgf_path):
    """
    Return the EXACT string used in the original extension JSON.
    E.g. "afinput_exp_acyclic_indvary2_step2_batch_yyy02.tgf"
    """
    return Path(tgf_path).name  # includes ".tgf"

def unify_subsample_key(tgf_path):
    """
    Remove trailing "_<digits>" and one of "_random/_degree/_bfs/_community" if present,
    then append ".tgf" so it matches the original's key.
    """
    base_name = Path(tgf_path).stem  # remove the .tgf suffix

    # 1) Remove trailing _<digits> if present
    parts = base_name.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        base_name = parts[0]

    # 2) Remove trailing _<method> if present
    for m in METHODS:
        suffix = "_" + m
        if base_name.endswith(suffix):
            base_name = base_name[: -len(suffix)]
            break

    # 3) Finally add ".tgf" to match the original key style
    return base_name + ".tgf"

########################
# Main Evaluate Script #
########################
def main():
    parser = argparse.ArgumentParser(description="Match structural metrics of subsampled TGFs (with _random etc.) to original TGFs.")
    parser.add_argument("--original-dir", required=True, help="Directory with original TGF files.")
    parser.add_argument("--subsample-parent-dir", required=True,
                        help="Parent directory with subfolders: random, degree, bfs, community, each containing multiple <root>_<method>_<num>.tgf files.")
    parser.add_argument("--original-extensions", required=True,
                        help="JSON with extension counts for original TGFs (keys end with .tgf).")
    parser.add_argument("--subsample-extensions", nargs="+", required=True,
                        help="One or more JSON files with extension counts for subsampled TGFs (keys are method-suffixed, but averaged?).")
    parser.add_argument("--output", default="evaluation_results.json",
                        help="Where to write the final JSON evaluation.")
    parser.add_argument("--proportion", type=float, default=0.5,
                        help="Fallback proportion p=|A'|/|A| if unknown.")
    parser.add_argument("--w-ext", type=float, default=0.5,
                        help="Weight for extension-based deviation in final combo.")
    parser.add_argument("--w-struct", type=float, default=0.5,
                        help="Weight for structural-based deviation in final combo.")
    args = parser.parse_args()

    ########################################################################
    # 0) Load extension JSON data
    ########################################################################
    print("Loading original extension counts...")
    with open(args.original_extensions, 'r') as f:
        original_ext_data = json.load(f)

    # Merge all subsample extension data by method
    subsample_ext_data = {m: {} for m in METHODS}
    print("Loading subsample extension counts from JSONs:")
    for sub_json in args.subsample_extensions:
        print(f"  - {sub_json}")
        with open(sub_json, 'r') as f:
            data = json.load(f)
            for method_key, method_val in data.items():
                if method_key in subsample_ext_data:
                    for filename, ext_counts in method_val.items():
                        subsample_ext_data[method_key][filename] = ext_counts
                else:
                    # skip unknown method keys
                    pass

    ########################################################################
    # 1) Compute structural metrics for the original TGF files
    ########################################################################
    print("\nComputing structural metrics for original TGFs...")
    original_struct = {}  # key => structural metrics

    original_files = glob.glob(os.path.join(args.original_dir, "*.tgf"))
    for tgf_path in tqdm(original_files, desc="Original TFs"):
        key = unify_original_key(tgf_path)
        sm = compute_structural_metrics(tgf_path)
        original_struct[key] = sm

    ########################################################################
    # 2) Compute structural metrics for each method’s subfolder, averaging by variant
    ########################################################################
    method_struct = {m: {} for m in METHODS}

    print("\nComputing structural metrics for each method's subfolder:")
    for method in METHODS:
        method_dir = os.path.join(args.subsample_parent_dir, method)
        if not os.path.isdir(method_dir):
            print(f"  [Warning] Subfolder '{method}' not found: {method_dir}")
            continue
        print(f"  -> Processing {method} in {method_dir}")
        method_files = glob.glob(os.path.join(method_dir, "*.tgf"))

        # Collect each <root>_<method>_<num>.tgf into a list, and average afterward
        group_metrics = {}
        for tgf_path in tqdm(method_files, desc=f"{method} TFs", leave=False):
            group_key = unify_subsample_key(tgf_path)
            sm = compute_structural_metrics(tgf_path)
            group_metrics.setdefault(group_key, []).append(sm)

        for gk, sm_list in group_metrics.items():
            n = len(sm_list)
            avg_metrics = {}
            for field in ["density", "avg_degree", "weak_connectivity", "reciprocity"]:
                avg_metrics[field] = sum(m[field] for m in sm_list) / n
            method_struct[method][gk] = avg_metrics

    ########################################################################
    # 3) Evaluate extension + structural deviations
    ########################################################################
    print("\nEvaluating extension + structural deviations...")
    results = {m: {} for m in METHODS}

    for method in tqdm(METHODS, desc="Methods"):
        for original_file in tqdm(original_ext_data.keys(), desc=f"{method} files", leave=False):
            if transform_key(original_file, method) not in subsample_ext_data[method]:
                continue
            if original_file not in method_struct[method]:
                continue
            if original_file not in original_struct:
                continue

            # get original extension counts
            orig_counts = original_ext_data[original_file]
            sub_counts  = subsample_ext_data[method][transform_key(original_file, method)]

            # -- Extension deviation (with partial details) --
            dev_list = []
            ext_dev_details = {}
            p = args.proportion
            for sem in ["CE-CO", "CE-PR", "CE-ST"]:
                e_orig = orig_counts.get(sem, None)
                e_sub_obj = sub_counts.get(sem, None)
                if isinstance(e_sub_obj, dict):
                    e_sub = e_sub_obj.get("average")
                else:
                    e_sub = e_sub_obj

                if e_orig is None or e_sub is None:
                    d_val = None
                else:
                    i_val = compute_target(e_orig, p, 5.0, 1.0)
                    d_val = ext_deviation(e_orig, e_sub, i_val)

                dev_list.append(d_val)
                ext_dev_details[sem] = d_val

            ext_score = combine_ext_devs(dev_list)

            # -- Structural deviation (aggregate + partial) --
            orig_st = original_struct[original_file]
            subs_st = method_struct[method][original_file]
            struct_score = compare_struct(orig_st, subs_st, weights=None)

            # Compute individual structural metric differences
            if struct_score is not None:
                partial_density_diff = abs(orig_st["density"] - subs_st["density"])
                partial_avg_degree_diff = abs(orig_st["avg_degree"] - subs_st["avg_degree"])
                partial_weak_connectivity_diff = abs(orig_st["weak_connectivity"] - subs_st["weak_connectivity"])
                partial_reciprocity_diff = abs(orig_st["reciprocity"] - subs_st["reciprocity"])
            else:
                partial_density_diff = None
                partial_avg_degree_diff = None
                partial_weak_connectivity_diff = None
                partial_reciprocity_diff = None

            partial_structural = {
                "density": partial_density_diff,
                "avg_degree": partial_avg_degree_diff,
                "weak_connectivity": partial_weak_connectivity_diff,
                "reciprocity": partial_reciprocity_diff
            }

            # -- Combine overall deviation --
            if ext_score is None and struct_score is None:
                overall = None
            else:
                epart = 0.0 if ext_score is None else ext_score
                spart = 0.0 if struct_score is None else struct_score
                overall = args.w_ext * epart + args.w_struct * spart

            results[method][original_file] = {
                "extension_deviation": ext_score,
                "extension_deviation_details": ext_dev_details,  # per-category
                "structural_deviation": struct_score,
                "structural_deviation_details": partial_structural,  # per-metric
                "overall_deviation": overall
            }

    ########################################################################
    # 4) Write results
    ########################################################################
    print(f"\nWriting final JSON to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()

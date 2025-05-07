#!/usr/bin/env python3
"""
Batch script for generating derivative argumentation frameworks (.tgf files)
using four subsampling methods from a source directory.

Usage:
  python af_subsample.py --source <SOURCE_DIR> --dest <DEST_DIR> \
                            [--proportion 0.5] [--num 10]
                            
Description:
  1) For each .tgf file in SOURCE_DIR, parse it as an argumentation framework 
     in the TGF format (nodes until '#' line, then edges).
  2) For each method (random, degree, bfs, community), generate NUM subsampled
     graphs, each with a unique random seed.
  3) Write the resulting .tgf files to DEST_DIR/<method>/ 
     using the pattern "<originalbasename>_<method>_<i>.tgf".
"""

import argparse
import os
import random
import subsampling_lib as sblib  # Reuse the library code from earlier

def main():
    parser = argparse.ArgumentParser(description="Batch subsample .tgf argumentation frameworks.")
    parser.add_argument("--source", required=True, help="Path to source directory containing .tgf files.")
    parser.add_argument("--dest", required=True, help="Path to destination directory.")
    parser.add_argument("--proportion", type=float, default=0.5, 
                        help="Fraction of nodes to keep (0 < proportion <= 1).")
    parser.add_argument("--num", type=int, default=10, 
                        help="Number of derivative graphs per method.")
    args = parser.parse_args()

    source_dir = args.source
    dest_dir = args.dest
    proportion = args.proportion
    num_samples = args.num

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    # Create subdirectories for each method if they don't exist
    methods = ["random", "degree", "bfs", "community"]
    for method in methods:
        method_dir = os.path.join(dest_dir, method)
        os.makedirs(method_dir, exist_ok=True)

    # Iterate over all .tgf files in the source directory
    for file_name in os.listdir(source_dir):
        if file_name.lower().endswith(".tgf"):
            input_path = os.path.join(source_dir, file_name)
            print(f"Processing: {input_path}")
            
            # Parse the graph
            try:
                nodes, edges = sblib.parse_graph(input_path)
            except Exception as e:
                print(f"Failed to parse '{file_name}': {e}")
                continue
            
            base_name = os.path.splitext(file_name)[0]

            # For each method, generate 'num_samples' subsamples
            for method in methods:
                method_dir = os.path.join(dest_dir, method)
                
                for i in range(1, num_samples + 1):
                    # Use a unique random seed for reproducibility,
                    # or you can skip the seed setting if you want pure randomness each time.
                    seed_value = hash((base_name, method, i)) & 0xffffffff
                    random.seed(seed_value)

                    # Perform subsampling
                    if method == "random":
                        subs_nodes, subs_edges = sblib.random_subsample(nodes, edges, proportion)
                    elif method == "degree":
                        subs_nodes, subs_edges = sblib.degree_extension_subsample(nodes, edges, proportion)
                    elif method == "bfs":
                        subs_nodes, subs_edges = sblib.bfs_subsample(nodes, edges, proportion)
                    elif method == "community":
                        subs_nodes, subs_edges = sblib.community_subsample(nodes, edges, proportion)
                    else:
                        continue  # Should not happen given our methods list

                    # Construct output filename
                    output_file = f"{base_name}_{method}_{i}.tgf"
                    output_path = os.path.join(method_dir, output_file)

                    # Write the subsampled graph
                    sblib.write_subsampled_graph(output_path, subs_nodes, subs_edges)
                    print(f"  -> {method} #{i} -> {output_path}")

    print("Batch subsampling complete.")

if __name__ == "__main__":
    main()

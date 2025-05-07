#!/usr/bin/env python3
import os
import argparse
import numpy as np

# ---------------------------------------------------------------------
# The following functions/classes are taken or adapted from your context.
# ---------------------------------------------------------------------

BLANK  = 0
IN     = 1
OUT    = 2

def parseTGF(file):
    """
    Parses a .tgf file and returns a tuple (args, atts).
      args is a list of argument names/IDs.
      atts is a list of pairs [src, tgt], each representing an attack.
    """
    with open(file, 'r') as f:
        args = []
        atts = []
        hash_seen = False
        for line in f:
            line = line.strip()
            if line == '#':
                hash_seen = True
                continue
            if not hash_seen:
                args.append(line)
            else:
                atts.append(line.split(' '))
    return args, atts

def solve(adj_matrix):
    """
    Compute the grounded extension via a simple iterative procedure:
    1. Label all unattacked arguments as IN.
    2. Propagate OUT labels to any nodes attacked by IN nodes.
    3. If a node's attackers are all labeled OUT, label it IN.
    4. Repeat until no more changes occur.
    """
    labelling = np.zeros((adj_matrix.shape[0]), np.int8)

    # Step 1: Mark unattacked arguments as IN
    a = np.sum(adj_matrix, axis=0) == 0
    unattacked_args = np.nonzero(a)[0]
    labelling[unattacked_args] = IN

    # Step 2 & 3: Propagate OUT labels and continue until stable
    cascade = True
    while cascade:
        # find new nodes attacked by the current IN arguments
        new_attacks = np.unique(np.nonzero(adj_matrix[unattacked_args, :])[1])
        # keep only those not already labeled OUT
        new_attacks_l = np.array([i for i in new_attacks if labelling[i] != OUT])
        
        if len(new_attacks_l) > 0:
            # label those as OUT
            labelling[new_attacks_l] = OUT
            # gather all nodes that these newly OUT arguments attack
            affected_idx = np.unique(np.nonzero(adj_matrix[new_attacks_l, :])[1])
        else:
            affected_idx = np.zeros((0), dtype='int64')
        
        # if any affected node now has all attackers labeled OUT, label it IN
        all_outs = []
        for idx in affected_idx:
            incoming_attacks = np.nonzero(adj_matrix[:, idx])[0]
            # if all attackers are OUT => label node IN
            if np.all(labelling[incoming_attacks] == OUT):
                all_outs.append(idx)

        if len(all_outs) > 0:
            labelling[np.array(all_outs)] = IN
            unattacked_args = np.array(all_outs)
        else:
            cascade = False

    # Return the indices of nodes labeled IN
    return np.nonzero(labelling == IN)[0]

# ---------------------------------------------------------------------
# Script: parse each TGF, build adjacency, solve, and write .apx.SE-GR
# ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compute the grounded extension for all .tgf files in a directory "
                    "and store solutions in .apx.SE-GR files (in [[a1,a2,...]] format)."
    )
    parser.add_argument(
        "directory",
        help="Path to the directory containing .tgf files."
    )
    args = parser.parse_args()
    
    input_dir = args.directory
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a valid directory.")
        return

    # Go through all .tgf files in the directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".tgf"):
            filepath = os.path.join(input_dir, filename)
            
            # 1. Parse the TGF
            arg_list, att_list = parseTGF(filepath)
            
            # If there are no arguments, either skip or just output empty brackets
            if len(arg_list) == 0:
                out_filename = filename + ".apx.SE-GR"
                out_filepath = os.path.join(input_dir, out_filename)
                with open(out_filepath, "w") as out_f:
                    out_f.write("[[]]\n")
                print(f"Processed (empty AF): {filename} -> {out_filename}")
                continue
            
            # Build dictionary from argument -> index
            name_to_idx = {name: i for i, name in enumerate(arg_list)}
            num_args = len(arg_list)
            
            # 2. Build adjacency matrix
            adj_matrix = np.zeros((num_args, num_args), dtype=int)
            for (src, tgt) in att_list:
                if src in name_to_idx and tgt in name_to_idx:
                    adj_matrix[name_to_idx[src], name_to_idx[tgt]] = 1
            
            # 3. Solve for grounded extension
            in_indices = solve(adj_matrix)
            in_args = [arg_list[idx] for idx in in_indices]
            
            # 4. Write solution to <filename>.apx.SE-GR
            # Output format: [[a1,a2,...]]
            out_filename = filename + ".apx.SE-GR"
            out_filepath = os.path.join(input_dir, out_filename)
            with open(out_filepath, "w") as out_f:
                out_f.write("[[")
                out_f.write(",".join(in_args))
                out_f.write("]]\n")
            
            print(f"Processed: {filename} -> {out_filename}")

if __name__ == "__main__":
    main()

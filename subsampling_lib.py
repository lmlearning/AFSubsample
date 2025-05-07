#!/usr/bin/env python3
"""
Subsampling library for argumentation frameworks.

This library provides:
1) Parsing of a graph file in the specified format.
2) Optional parsing of a solution file under preferred semantics
   (to compute extension-based metrics for "Degree-/Extension-Guided" sampling).
3) Four subsampling methods:
   - random_subsample
   - degree_extension_subsample
   - bfs_subsample
   - community_subsample
4) Functions to output the resulting subsampled graph in the same format.
"""

import random
import networkx as nx

def parse_graph(graph_filename):
    """
    Reads a graph file of the form:
      <argument_1>
      <argument_2>
      ...
      #
      <attacker_1> <attacked_1>
      ...
    Returns:
      nodes (list): list of node labels (strings)
      edges (list of tuples): list of directed edges (attacker, attacked)
    """
    nodes = []
    edges = []
    reading_nodes = True

    with open(graph_filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # skip empty lines

            if reading_nodes:
                if line == '#':
                    reading_nodes = False
                else:
                    # Each line is a node label, e.g., "a1", "a2", ...
                    nodes.append(line)
            else:
                # Each line is "X Y" meaning X attacks Y
                parts = line.split()
                if len(parts) == 2:
                    edges.append((parts[0], parts[1]))

    return nodes, edges


def parse_solution(solution_filename):
    """
    Reads a solution file under preferred semantics, which has multiple solution sets in a bracketed format:
      [[a1,a2,...],[a1,a3,...],...]

    Returns:
      extension_count (dict): 
         A dictionary counting how many times each argument appears 
         across all solution sets. Key: argument, Value: occurrence count.
    """
    extension_count = {}
    with open(solution_filename, 'r', encoding='utf-8') as f:
        content = f.read().strip()

        # Very naive parsing for a bracketed list of lists:
        # We'll split by ']' then parse each chunk if it has arguments
        # Another approach: use a JSON parser after small replacements
        # but let's do a straightforward approach here.
        # Format example: [[a11,a32],[a11,a33],...]
        # We'll remove outer brackets and then split on "],["

        # Remove outer brackets
        cleaned = content.lstrip('[').rstrip(']')
        # Now split on "],["
        sets_raw = cleaned.split('],[')
        
        for s in sets_raw:
            # Remove any remaining [ or ]
            s_clean = s.replace('[', '').replace(']', '')
            # split on commas
            args = s_clean.split(',')
            for arg in args:
                arg = arg.strip()
                if arg:
                    extension_count[arg] = extension_count.get(arg, 0) + 1

    return extension_count


def build_graph(nodes, edges):
    """
    Build and return a directed NetworkX graph from node list and edge list.
    """
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    return G


def random_subsample(nodes, edges, proportion):
    """
    Randomly selects proportion of the nodes and retains edges that connect them.
    Returns a subsampled (nodes_sub, edges_sub).
    """
    total_nodes = len(nodes)
    k = int(round(proportion * total_nodes))
    if k <= 0:
        raise ValueError("proportion * total_nodes is too small, no nodes would be selected.")

    selected_nodes = set(random.sample(nodes, k))
    
    # Filter edges to keep only those where both endpoints are in selected_nodes
    filtered_edges = [(u, v) for (u, v) in edges if (u in selected_nodes and v in selected_nodes)]

    return list(selected_nodes), filtered_edges


def degree_extension_subsample(nodes, edges, proportion, solution_dict=None):
    """
    Selects proportion of the nodes based on a relevance score:
      score(node) = degree(node) + alpha * extension_count(node)
    where alpha is a scaling factor you can adjust if you want.

    If solution_dict is provided, extension_count is used; otherwise only degree is used.
    """
    alpha = 1.0  # you can tune this parameter

    G = build_graph(nodes, edges)
    
    # Calculate (in_degree + out_degree) for each node
    # For argumentation, it might be more relevant to weigh in-degree/out-degree differently,
    # but here we just sum them.
    degrees = {}
    for n in G.nodes:
        degrees[n] = G.in_degree(n) + G.out_degree(n)

    # For extension count, if no solution_dict given, treat it as 0
    def get_extension_count(n):
        if solution_dict is None:
            return 0
        return solution_dict.get(n, 0)

    # Compute combined score
    node_scores = []
    for n in nodes:
        score = degrees[n] + alpha * get_extension_count(n)
        node_scores.append((n, score))

    # Sort by descending score
    node_scores.sort(key=lambda x: x[1], reverse=True)

    # Pick top p% of nodes
    total_nodes = len(nodes)
    k = int(round(proportion * total_nodes))
    if k <= 0:
        raise ValueError("proportion * total_nodes is too small, no nodes would be selected.")

    selected_nodes = set([x[0] for x in node_scores[:k]])

    # Filter edges
    filtered_edges = [(u, v) for (u, v) in edges if (u in selected_nodes and v in selected_nodes)]

    return list(selected_nodes), filtered_edges


def bfs_subsample(nodes, edges, proportion, seed=None):
    """
    BFS ("snowball") sampling. 
    - Start from one random or specified seed.
    - Expand until proportion of the nodes is reached (or graph exhausted).
    Returns (nodes_sub, edges_sub).
    """
    G = build_graph(nodes, edges)
    total_nodes = len(nodes)
    k = int(round(proportion * total_nodes))
    if k <= 0:
        raise ValueError("proportion * total_nodes is too small, no nodes would be selected.")
    
    if seed is None:
        seed = random.choice(nodes)

    visited = set()
    queue = [seed]
    visited.add(seed)
    
    idx = 0
    while queue and len(visited) < k:
        current = queue.pop(0)
        # neighbors = direct successors + direct predecessors to mimic argumentation links
        neighbors = list(G.successors(current)) + list(G.predecessors(current))
        random.shuffle(neighbors)  # optional shuffle for variety
        for nb in neighbors:
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
                if len(visited) >= k:
                    break

    selected_nodes = visited
    filtered_edges = [(u, v) for (u, v) in edges if (u in selected_nodes and v in selected_nodes)]
    return list(selected_nodes), filtered_edges


def community_subsample(nodes, edges, proportion):
    """
    Community-based sampling:
    1) Detect communities via a standard community-detection method (e.g. greedy_modularity_communities).
    2) Sample from each community proportionally.

    Returns (nodes_sub, edges_sub).
    """
    G = build_graph(nodes, edges)
    total_nodes = len(nodes)
    k = int(round(proportion * total_nodes))
    if k <= 0:
        raise ValueError("proportion * total_nodes is too small, no nodes would be selected.")

    # We'll use the built-in greedy_modularity_communities (undirected approach),
    # so let's convert to an undirected version for community detection.
    # Then sample from each community in proportion to its size.

    UG = G.to_undirected()
    # from networkx.algorithms import community
    communities_gen = nx.algorithms.community.greedy_modularity_communities(UG)
    communities = list(communities_gen)  # each is a set of nodes

    # total communities
    sampled_nodes = set()
    remaining_needed = k

    # One simple approach: sample from each community proportionally
    # or if small communities are found, make sure we handle rounding carefully.
    for c in communities:
        community_size = len(c)
        if community_size == 0:
            continue

        # how many to pick from this community?
        # proportional share: (community_size / total_nodes) * k
        comm_k = int(round((community_size / total_nodes) * k))
        if comm_k > len(c):
            comm_k = len(c)
        if comm_k > remaining_needed:
            comm_k = remaining_needed

        # random sample comm_k from this community
        selected_in_comm = random.sample(list(c), comm_k)
        sampled_nodes.update(selected_in_comm)
        remaining_needed = k - len(sampled_nodes)
        if remaining_needed <= 0:
            break

    # If we haven't reached k (due to rounding), sample from any leftover communities randomly
    if len(sampled_nodes) < k:
        missing = k - len(sampled_nodes)
        leftover = list(set(nodes) - sampled_nodes)
        if missing > len(leftover):
            missing = len(leftover)
        if missing > 0:
            extra = random.sample(leftover, missing)
            sampled_nodes.update(extra)

    filtered_edges = [(u, v) for (u, v) in edges if (u in sampled_nodes and v in sampled_nodes)]
    return list(sampled_nodes), filtered_edges


def write_subsampled_graph(output_filename, nodes_sub, edges_sub):
    """
    Writes the subsampled graph to a file in the same format:
      node1
      node2
      ...
      #
      attacker1 attacked1
      ...
    """
    with open(output_filename, 'w', encoding='utf-8') as f:
        for n in nodes_sub:
            f.write(f"{n}\n")
        f.write("#\n")
        for (u, v) in edges_sub:
            f.write(f"{u} {v}\n")

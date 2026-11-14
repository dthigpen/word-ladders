#!/usr/bin/env python3
"""
Word Ladder Puzzle Generator

Generates high-quality word ladder puzzles from a curated word list,
filtering by Puzzle Quality Score (PQS) and tagging by difficulty.
"""

import json
import random
import string
from collections import deque
from pathlib import Path
from typing import Set, Dict, List, Tuple

import wordfreq


def load_words(file_path: str) -> Set[str]:
    """Load words from a file, one per line."""
    with open(file_path, 'r') as f:
        return {line.strip().lower() for line in f if line.strip()}


def get_neighbors(word: str, word_set: Set[str]) -> Set[str]:
    """Get all 1-letter-edit neighbors of a word within the given word set."""
    neighbors = set()
    for i in range(len(word)):
        for c in string.ascii_lowercase:
            if c != word[i]:
                candidate = word[:i] + c + word[i+1:]
                if candidate in word_set:
                    neighbors.add(candidate)
    return neighbors


def build_graph(word_set: Set[str]) -> Dict[str, Set[str]]:
    """Build a graph adjacency list mapping each word to its neighbors."""
    graph = {}
    for word in word_set:
        graph[word] = get_neighbors(word, word_set)
    return graph


def find_all_shortest_paths(
    start: str,
    end: str,
    graph: Dict[str, Set[str]]
) -> List[List[str]]:
    """
    Find all shortest paths between start and end using BFS.
    Returns a list of paths, where each path is a list of words.
    """
    if start not in graph or end not in graph:
        return []
    
    if start == end:
        return [[start]]
    
    # BFS to find shortest distance and track predecessors
    queue = deque([start])
    visited = {start}
    distance = {start: 0}
    predecessors = {start: []}
    
    while queue:
        current = queue.popleft()
        
        if current == end:
            break
        
        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                distance[neighbor] = distance[current] + 1
                predecessors[neighbor] = [current]
                queue.append(neighbor)
            elif distance[neighbor] == distance[current] + 1:
                # Another shortest path to this node
                predecessors[neighbor].append(current)
    
    if end not in distance:
        return []
    
    # Reconstruct all shortest paths using backtracking
    shortest_distance = distance[end]
    all_paths = []
    
    def backtrack(node: str, path: List[str]):
        if node == start:
            all_paths.append(path[::-1])
            return
        
        for pred in predecessors[node]:
            backtrack(pred, path + [pred])
    
    backtrack(end, [end])
    
    return all_paths


def calculate_pqs(
    paths: List[List[str]],
    word_freq_map: Dict[str, float],
    graph_degrees: Dict[str, int]
) -> float:
    """
    Calculate Puzzle Quality Score (PQS) for a set of shortest paths.
    Returns a score from 0 to 100.
    """
    if not paths:
        return 0.0
    
    num_paths = len(paths)
    intermediate_steps = len(paths[0]) - 2
    
    # 1. Vocabulary Commonality (evaluate weakest word across primary paths)
    all_path_words = {w for path in paths for w in path}
    min_freq = min(word_freq_map.get(w, 0.0) for w in all_path_words)
    
    if min_freq < 2e-6:
        return 0.0  # Hard disqualification
    elif min_freq >= 5e-5:
        freq_score = 100
    elif min_freq >= 1e-5:
        freq_score = 75
    else:
        freq_score = 40
    
    # Single-Path Rule enforcement
    if num_paths == 1 and freq_score < 100:
        return 0.0
    
    # 2. Path Diversity
    if num_paths >= 4:
        diversity_score = 100
    elif num_paths >= 2:
        diversity_score = 70
    else:
        diversity_score = 20
    
    # 3. Optimal Length
    if intermediate_steps in (3, 4):
        length_score = 100
    elif intermediate_steps in (2, 5):
        length_score = 75
    else:
        length_score = 40
    
    # 4. Graph Connectivity (check intermediate nodes only)
    intermediates = {w for path in paths for w in path[1:-1]}
    if intermediates:
        min_degree = min(graph_degrees.get(w, 0) for w in intermediates)
        if min_degree >= 5:
            conn_score = 100
        elif min_degree >= 3:
            conn_score = 60
        else:
            conn_score = 0
    else:
        conn_score = 100
    
    # Weighted Sum
    pqs = (
        (freq_score * 0.30) +
        (diversity_score * 0.30) +
        (length_score * 0.20) +
        (conn_score * 0.20)
    )
    return round(pqs, 2)


def calculate_difficulty_tag(
    paths: List[List[str]],
    word_freq_map: Dict[str, float],
    graph_degrees: Dict[str, int]
) -> str:
    """
    Calculate Composite Difficulty Score (CDS) and return difficulty tag.
    Returns: 'Easy', 'Medium', 'Hard', or 'Expert'
    """
    if not paths:
        return "Unknown"
    
    num_paths = len(paths)
    intermediate_steps = len(paths[0]) - 2
    
    # 1. Length Component (0-100 normalized)
    if intermediate_steps <= 2:
        length_score = 20
    elif intermediate_steps <= 4:
        length_score = 50
    elif intermediate_steps <= 6:
        length_score = 80
    else:
        length_score = 100
    
    # 2. Rarity Penalty (based on weakest path word frequency)
    all_words = {w for path in paths for w in path}
    min_freq = min(word_freq_map.get(w, 0.0) for w in all_words)
    if min_freq >= 5e-5:
        rarity_score = 10
    elif min_freq >= 1e-5:
        rarity_score = 40
    elif min_freq >= 2e-6:
        rarity_score = 80
    else:
        rarity_score = 100
    
    # 3. Fragility Penalty (Path Diversity inverse)
    if num_paths >= 4:
        fragility_score = 10
    elif num_paths >= 2:
        fragility_score = 50
    else:
        fragility_score = 100
    
    # 4. Bottleneck Penalty (Intermediate node connectivity)
    intermediates = {w for path in paths for w in path[1:-1]}
    if intermediates:
        min_deg = min(graph_degrees.get(w, 0) for w in intermediates)
        if min_deg >= 6:
            bottleneck_score = 10
        elif min_deg >= 3:
            bottleneck_score = 50
        else:
            bottleneck_score = 100
    else:
        bottleneck_score = 10
    
    # Weighted Composite Difficulty Score
    cds = (
        (length_score * 0.25) +
        (rarity_score * 0.35) +
        (fragility_score * 0.25) +
        (bottleneck_score * 0.15)
    )
    
    # Threshold Mapping
    if cds < 35:
        return "Easy"
    elif cds < 60:
        return "Medium"
    elif cds < 85:
        return "Hard"
    else:
        return "Expert"


def generate_puzzles(
    word_set: Set[str],
    graph: Dict[str, Set[str]],
    word_freq_map: Dict[str, float],
    graph_degrees: Dict[str, int],
    num_puzzles: int = 100,
    min_pqs: float = 80.0,
    min_distance: int = 3,
    max_distance: int = 6
) -> List[Dict]:
    """
    Generate puzzles by sampling word pairs and filtering by PQS.
    
    Args:
        word_set: Set of valid words
        graph: Word adjacency graph
        word_freq_map: Dict mapping word -> frequency
        graph_degrees: Dict mapping word -> neighbor count
        num_puzzles: Target number of puzzles to generate
        min_pqs: Minimum PQS threshold (default 80)
        min_distance: Minimum intermediate steps
        max_distance: Maximum intermediate steps
    
    Returns:
        List of puzzle dictionaries with metadata
    """
    puzzles = []
    attempts = 0
    max_attempts = num_puzzles * 20  # Allow many attempts to find good puzzles
    word_list = list(word_set)
    
    # Track used start/end pairs to avoid duplicates
    used_pairs = set()
    
    while len(puzzles) < num_puzzles and attempts < max_attempts:
        attempts += 1
        
        # Sample two random words
        start, end = random.sample(word_list, 2)
        
        # Skip if this pair (or reverse) has been used
        pair_key = tuple(sorted([start, end]))
        if pair_key in used_pairs:
            continue
        
        # Find all shortest paths
        paths = find_all_shortest_paths(start, end, graph)
        
        if not paths:
            continue
        
        intermediate_steps = len(paths[0]) - 2
        
        # Filter by distance constraints
        if intermediate_steps < min_distance or intermediate_steps > max_distance:
            continue
        
        # Calculate PQS
        pqs = calculate_pqs(paths, word_freq_map, graph_degrees)
        
        if pqs < min_pqs:
            continue
        
        # Calculate difficulty
        difficulty = calculate_difficulty_tag(paths, word_freq_map, graph_degrees)
        
        # Mark pair as used
        used_pairs.add(pair_key)
        
        # Create puzzle record
        puzzle = {
            'start': start,
            'end': end,
            'paths': paths,
            'intermediate_steps': intermediate_steps,
            'num_paths': len(paths),
            'pqs': pqs,
            'difficulty': difficulty,
        }
        
        puzzles.append(puzzle)
        
        if attempts % 100 == 0:
            print(f"  Generated {len(puzzles)}/{num_puzzles} puzzles (attempts: {attempts})")
    
    print(f"  Generated {len(puzzles)} puzzles in {attempts} attempts")
    return puzzles


def main():
    """Main puzzle generation workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate word ladder puzzles or solve specific pairs')
    parser.add_argument('-n', '--num-puzzles', type=int, default=50, help='Number of puzzles to generate')
    parser.add_argument('--min-pqs', type=float, default=80.0, help='Minimum PQS threshold')
    parser.add_argument('--min-distance', type=int, default=3, help='Minimum intermediate steps')
    parser.add_argument('--max-distance', type=int, default=6, help='Maximum intermediate steps')
    parser.add_argument('-w', '--word-list', default='data/output/valid_4letter_words.txt', help='Path to word list')
    parser.add_argument('-o', '--output', default='data/output/generated_puzzles.json', help='Output file path')
    parser.add_argument('--solve', nargs=2, metavar=('START', 'END'), help='Solve a specific word ladder pair')
    
    args = parser.parse_args()
    
    print("Word Ladder Puzzle Generator")
    print("=" * 50)
    
    # Load word list
    print(f"\nLoading word list from: {args.word_list}")
    word_set = load_words(args.word_list)
    print(f"  Loaded {len(word_set)} words")
    
    # Build graph
    print("\nBuilding word graph...")
    graph = build_graph(word_set)
    graph_degrees = {word: len(neighbors) for word, neighbors in graph.items()}
    print(f"  Graph built with {len(graph)} nodes")
    
    # Build frequency map
    print("\nBuilding frequency map...")
    word_freq_map = {word: wordfreq.word_frequency(word, 'en') for word in word_set}
    print(f"  Frequency map built")
    
    # Solve specific pair mode
    if args.solve:
        start, end = args.solve
        start = start.lower()
        end = end.lower()
        
        print(f"\nSolving: {start} -> {end}")
        
        if start not in word_set:
            print(f"  Error: '{start}' not in word list")
            return
        if end not in word_set:
            print(f"  Error: '{end}' not in word list")
            return
        
        paths = find_all_shortest_paths(start, end, graph)
        
        if not paths:
            print(f"  No path found between {start} and {end}")
            return
        
        pqs = calculate_pqs(paths, word_freq_map, graph_degrees)
        difficulty = calculate_difficulty_tag(paths, word_freq_map, graph_degrees)
        
        print(f"\nFound {len(paths)} shortest path(s):")
        for i, path in enumerate(paths, 1):
            print(f"  {i}. {' -> '.join(path)}")
        
        print(f"\nPQS: {pqs}")
        print(f"Difficulty: {difficulty}")
        print(f"Intermediate steps: {len(paths[0]) - 2}")
        return
    
    # Generate puzzles mode
    print(f"\nGenerating puzzles (min PQS: {args.min_pqs}, distance: {args.min_distance}-{args.max_distance})...")
    puzzles = generate_puzzles(
        word_set=word_set,
        graph=graph,
        word_freq_map=word_freq_map,
        graph_degrees=graph_degrees,
        num_puzzles=args.num_puzzles,
        min_pqs=args.min_pqs,
        min_distance=args.min_distance,
        max_distance=args.max_distance
    )
    
    # Sort by PQS descending
    puzzles.sort(key=lambda p: p['pqs'], reverse=True)
    
    # Export results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save puzzles as JSON
    with open(output_path, 'w') as f:
        json.dump(puzzles, f, indent=2)
    print(f"\nPuzzles saved to: {output_path}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  Total puzzles: {len(puzzles)}")
    if puzzles:
        print(f"  PQS range: {puzzles[-1]['pqs']:.2f} - {puzzles[0]['pqs']:.2f}")
        
        difficulty_counts = {}
        for p in puzzles:
            difficulty_counts[p['difficulty']] = difficulty_counts.get(p['difficulty'], 0) + 1
        print(f"  Difficulty breakdown: {difficulty_counts}")
        
        # Show top 5 puzzles
        print("\nTop 5 puzzles by PQS:")
        for i, p in enumerate(puzzles[:5], 1):
            print(f"  {i}. {p['start']} -> {p['end']} (PQS: {p['pqs']}, Difficulty: {p['difficulty']}, Paths: {p['num_paths']}, Steps: {p['intermediate_steps']})")
    else:
        print("  No puzzles generated. Try lowering the min-pqs threshold.")


if __name__ == '__main__':
    main()

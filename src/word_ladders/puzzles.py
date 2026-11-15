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
import yaml


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
    difficulty_targets: Dict[str, int] = None,
    num_puzzles: int = 100,
    min_pqs: float = 80.0,
    min_distance: int = 3,
    max_distance: int = 6,
    max_attempts: int = None
) -> List[Dict]:
    """
    Generate puzzles by sampling word pairs and filtering by PQS.
    
    Args:
        word_set: Set of valid words
        graph: Word adjacency graph
        word_freq_map: Dict mapping word -> frequency
        graph_degrees: Dict mapping word -> neighbor count
        difficulty_targets: Dict mapping difficulty -> target count (e.g., {'easy': 10, 'medium': 20})
                          If None or all zeros, uses num_puzzles as total target
        num_puzzles: Target number of puzzles to generate (used if difficulty_targets not set)
        min_pqs: Minimum PQS threshold (default 80)
        min_distance: Minimum intermediate steps
        max_distance: Maximum intermediate steps
        max_attempts: Maximum sampling attempts (default: calculated based on targets)
    
    Returns:
        List of puzzle dictionaries with metadata
    """
    puzzles = []
    attempts = 0
    
    # Determine generation mode
    use_difficulty_targets = difficulty_targets and sum(difficulty_targets.values()) > 0
    
    if use_difficulty_targets:
        total_target = sum(difficulty_targets.values())
        max_attempts = max_attempts or total_target * 50
    else:
        total_target = num_puzzles
        max_attempts = max_attempts or num_puzzles * 100  # More attempts for total-count mode
    
    word_list = sorted(word_set)  # Sort for deterministic ordering
    
    # Track used start/end pairs to avoid duplicates
    used_pairs = set()
    
    # Track current counts per difficulty
    current_counts = {d: 0 for d in ['Easy', 'Medium', 'Hard', 'Expert']}
    
    def targets_met():
        """Check if all difficulty targets have been met."""
        if not use_difficulty_targets:
            return len(puzzles) >= total_target
        
        for diff, target in difficulty_targets.items():
            if current_counts[diff.capitalize()] < target:
                return False
        return True
    
    def should_accept(difficulty: str) -> bool:
        """Check if a puzzle should be accepted based on difficulty targets."""
        if not use_difficulty_targets:
            return True
        
        target = difficulty_targets.get(difficulty.lower(), 0)
        if target == 0:
            return False  # Don't accept difficulties with 0 target
        
        return current_counts[difficulty] < target
    
    while not targets_met() and attempts < max_attempts:
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
        
        # Check if we should accept this difficulty
        if not should_accept(difficulty):
            continue
        
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
        current_counts[difficulty] += 1
        
        if attempts % 100 == 0:
            if use_difficulty_targets:
                print(f"  Progress: {current_counts} / {difficulty_targets} (attempts: {attempts})")
            else:
                print(f"  Generated {len(puzzles)}/{total_target} puzzles (attempts: {attempts})")
    
    if use_difficulty_targets:
        print(f"  Generated {len(puzzles)} puzzles: {current_counts} (attempts: {attempts})")
    else:
        print(f"  Generated {len(puzzles)} puzzles in {attempts} attempts")
    
    return puzzles


def load_config(config_path: str = 'config/config.yaml') -> Dict:
    """Load configuration from YAML file and resolve relative paths."""
    from word_ladders.lexicon import load_config as load_config_base
    return load_config_base(config_path)


def main():
    """Main puzzle generation workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate word ladder puzzles or solve specific pairs')
    parser.add_argument('-c', '--config', default='config.yaml', help='Path to config file')
    parser.add_argument('-n', '--num-puzzles', type=int, help='Number of puzzles to generate (overrides config)')
    parser.add_argument('--min-pqs', type=float, help='Minimum PQS threshold (overrides config)')
    parser.add_argument('--min-distance', type=int, help='Minimum intermediate steps (overrides config)')
    parser.add_argument('--max-distance', type=int, help='Maximum intermediate steps (overrides config)')
    parser.add_argument('-w', '--word-list', help='Path to word list (overrides config)')
    parser.add_argument('-o', '--output', help='Output file path (overrides config)')
    parser.add_argument('--seed', type=int, help='Random seed for deterministic generation (overrides config)')
    parser.add_argument('--easy', type=int, help='Target count for Easy puzzles (overrides config)')
    parser.add_argument('--medium', type=int, help='Target count for Medium puzzles (overrides config)')
    parser.add_argument('--hard', type=int, help='Target count for Hard puzzles (overrides config)')
    parser.add_argument('--expert', type=int, help='Target count for Expert puzzles (overrides config)')
    parser.add_argument('--solve', nargs=2, metavar=('START', 'END'), help='Solve a specific word ladder pair')
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    puzzle_config = config.get('puzzle_generation', {})
    
    # Apply CLI overrides
    word_list = args.word_list or puzzle_config.get('word_list', 'data/output/valid_4letter_words.txt')
    output = args.output or puzzle_config.get('output', 'data/output/generated_puzzles.json')
    min_pqs = args.min_pqs if args.min_pqs is not None else puzzle_config.get('min_pqs', 80.0)
    min_distance = args.min_distance if args.min_distance is not None else puzzle_config.get('min_distance', 3)
    max_distance = args.max_distance if args.max_distance is not None else puzzle_config.get('max_distance', 6)
    seed = args.seed if args.seed is not None else puzzle_config.get('seed')
    
    # Difficulty targets
    # If num_puzzles is explicitly provided via CLI, ignore difficulty targets
    if args.num_puzzles is not None:
        difficulty_targets = {'easy': 0, 'medium': 0, 'hard': 0, 'expert': 0}
        num_puzzles = args.num_puzzles
    else:
        config_targets = puzzle_config.get('difficulty_targets', {})
        difficulty_targets = {
            'easy': args.easy if args.easy is not None else config_targets.get('easy', 0),
            'medium': args.medium if args.medium is not None else config_targets.get('medium', 0),
            'hard': args.hard if args.hard is not None else config_targets.get('hard', 0),
            'expert': args.expert if args.expert is not None else config_targets.get('expert', 0),
        }
        num_puzzles = puzzle_config.get('num_puzzles', 50)
    
    # Set random seed for determinism
    if seed is not None:
        random.seed(seed)
        print(f"Using random seed: {seed}")
    
    print("Word Ladder Puzzle Generator")
    print("=" * 50)
    
    # Load word list
    print(f"\nLoading word list from: {word_list}")
    word_set = load_words(word_list)
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
    use_targets = sum(difficulty_targets.values()) > 0
    
    if use_targets:
        print(f"\nGenerating puzzles with difficulty targets: {difficulty_targets}")
    else:
        print(f"\nGenerating {num_puzzles} puzzles")
    
    print(f"  Min PQS: {min_pqs}, Distance: {min_distance}-{max_distance}")
    
    puzzles = generate_puzzles(
        word_set=word_set,
        graph=graph,
        word_freq_map=word_freq_map,
        graph_degrees=graph_degrees,
        difficulty_targets=difficulty_targets if use_targets else None,
        num_puzzles=num_puzzles,
        min_pqs=min_pqs,
        min_distance=min_distance,
        max_distance=max_distance
    )
    
    # Sort by PQS descending
    puzzles.sort(key=lambda p: p['pqs'], reverse=True)
    
    # Export results
    output_path = Path(output)
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
        print("  No puzzles generated. Try lowering the min-pqs threshold or adjusting difficulty targets.")


if __name__ == '__main__':
    main()

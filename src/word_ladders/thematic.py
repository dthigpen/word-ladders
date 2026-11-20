#!/usr/bin/env python3
"""
Thematic Word Pair Generator

Extracts semantically meaningful word pairs using WordNet lexical relationships,
validates them against the word ladder solver and PQS criteria.
"""

import itertools
import json
from collections import defaultdict
from pathlib import Path
from typing import Set, Dict, List, Tuple

import nltk
import yaml
from nltk.corpus import wordnet as wn

# Import shared functions from puzzles module
from word_ladders.puzzles import (
    load_words,
    build_graph,
    find_all_shortest_paths,
    calculate_pqs,
    calculate_difficulty_tag,
)


def download_nltk_data():
    """Ensure required NLTK corpora are downloaded."""
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)


def hamming_distance(w1: str, w2: str) -> int:
    """Compute the number of differing characters between two equal-length strings."""
    return sum(c1 != c2 for c1, c2 in zip(w1, w2))


def build_domain_buckets(
    valid_words: Set[str],
    max_senses: int = 2
) -> Dict[str, Set[str]]:
    """
    Group valid 4-letter words into WordNet lexicographer domains.
    
    Args:
        valid_words: Set of valid words to categorize
        max_senses: Limit to top N senses per word to avoid semantic pollution
    
    Returns:
        Dict mapping lexname -> set of words
    """
    buckets = defaultdict(set)
    
    for word in valid_words:
        # Limit to primary senses to avoid obscure semantic pollution
        for syn in wn.synsets(word)[:max_senses]:
            buckets[syn.lexname()].add(word)
    
    return dict(buckets)


def extract_antonym_polarity_pairs(
    valid_words: Set[str],
    min_hamming: int = 2
) -> List[Dict]:
    """
    Extract direct antonyms and cross-pole synonym pairs within valid_words.
    
    Args:
        valid_words: Set of valid words
        min_hamming: Minimum hamming distance required
    
    Returns:
        List of candidate pair dictionaries with theme metadata
    """
    seen_pairs = set()
    results = []
    
    for word in sorted(valid_words):
        for syn in wn.synsets(word):
            for lemma in syn.lemmas():
                for ant in lemma.antonyms():
                    ant_word = ant.name().lower()
                    
                    # Skip if antonym not in valid words or is the same word
                    if ant_word not in valid_words or ant_word == word:
                        continue
                    
                    ant_syn = ant.synset()
                    
                    # Build synonym clusters (poles) for both senses
                    pole_a = {l.name().lower() for l in syn.lemmas()} & valid_words
                    pole_b = {l.name().lower() for l in ant_syn.lemmas()} & valid_words
                    
                    # Generate cross-pole pairs
                    for wa, wb in itertools.product(pole_a, pole_b):
                        if wa == wb or hamming_distance(wa, wb) < min_hamming:
                            continue
                        
                        canonical = tuple(sorted((wa, wb)))
                        if canonical in seen_pairs:
                            continue
                        seen_pairs.add(canonical)
                        
                        is_direct = (wa == word and wb == ant_word) or (wb == word and wa == ant_word)
                        
                        results.append({
                            "start": wa,
                            "end": wb,
                            "theme_type": "antonym_direct" if is_direct else "antonym_polarity",
                            "theme_label": f"Opposites ({word} / {ant_word})"
                        })
    
    return results


def extract_domain_pairs(
    buckets: Dict[str, Set[str]],
    domain_pairs: List[Tuple[str, str]],
    min_hamming: int = 2,
    max_per_domain_pair: int = 500
) -> List[Dict]:
    """
    Generate candidate pairs within or across specified WordNet domains.
    
    Args:
        buckets: Dict mapping lexname -> set of words
        domain_pairs: List of (domain_a, domain_b) tuples to process
        min_hamming: Minimum hamming distance required
        max_per_domain_pair: Maximum pairs to generate per domain pair
    
    Returns:
        List of candidate pair dictionaries with theme metadata
    """
    seen_pairs = set()
    results = []
    
    for dom_a, dom_b in domain_pairs:
        words_a = sorted(buckets.get(dom_a, set()))
        words_b = sorted(buckets.get(dom_b, set()))
        
        if not words_a or not words_b:
            continue
        
        # Choose combinations (intra-domain) or product (cross-domain)
        candidates = (
            itertools.combinations(words_a, 2)
            if dom_a == dom_b
            else itertools.product(words_a, words_b)
        )
        
        count = 0
        for wa, wb in candidates:
            if wa == wb or hamming_distance(wa, wb) < min_hamming:
                continue
            
            canonical = tuple(sorted((wa, wb)))
            if canonical in seen_pairs:
                continue
            seen_pairs.add(canonical)
            
            results.append({
                "start": wa,
                "end": wb,
                "theme_type": "intra_domain" if dom_a == dom_b else "cross_domain",
                "theme_label": f"{dom_a} <-> {dom_b}"
            })
            
            count += 1
            if count >= max_per_domain_pair:
                break
    
    return results


def validate_thematic_pairs(
    candidates: List[Dict],
    graph: Dict[str, Set[str]],
    word_freq_map: Dict[str, float],
    graph_degrees: Dict[str, int],
    min_pqs: float = 80.0,
    min_distance: int = 2,
    max_distance: int = 5
) -> List[Dict]:
    """
    Validate candidate pairs using the solver and PQS criteria.
    
    Args:
        candidates: List of candidate pair dictionaries
        graph: Word adjacency graph
        word_freq_map: Dict mapping word -> frequency
        graph_degrees: Dict mapping word -> neighbor count
        min_pqs: Minimum PQS threshold
        min_distance: Minimum intermediate steps
        max_distance: Maximum intermediate steps
    
    Returns:
        List of validated puzzle dictionaries with full metadata
    """
    validated = []
    
    for i, candidate in enumerate(candidates):
        start = candidate['start']
        end = candidate['end']
        
        # Find shortest paths
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
        
        # Create final puzzle record
        puzzle = {
            "id": f"{start}_{end}",
            "start": start,
            "end": end,
            "theme_type": candidate['theme_type'],
            "theme_label": candidate['theme_label'],
            "intermediate_steps": intermediate_steps,
            "num_paths": len(paths),
            "pqs": pqs,
            "difficulty": difficulty,
            "sample_path": paths[0],  # First shortest path as sample
            "paths": paths,
            "source": "thematic",
        }
        
        validated.append(puzzle)
        
        if (i + 1) % 50 == 0:
            print(f"  Validated {len(validated)}/{i+1} candidates...")
    
    return validated


def generate_thematic_puzzles(
    word_set: Set[str],
    graph: Dict[str, List[str]],
    word_freq_map: Dict[str, float],
    graph_degrees: Dict[str, int],
    min_pqs: float = 80.0,
    min_distance: int = 2,
    max_distance: int = 5,
    target_domain_pairs: List[List[str]] = None,
    max_per_domain_pair: int = 500,
    min_hamming: int = 2,
    max_senses: int = 2,
) -> List[Dict]:
    """Generate thematic puzzles directly from graph and word set."""
    if target_domain_pairs is None:
        # Use sensible defaults
        target_domain_pairs = [
            ["noun.animal", "noun.animal"],
            ["noun.food", "noun.food"],
            ["noun.body", "noun.body"],
            ["noun.feeling", "noun.feeling"],
            ["noun.artifact", "noun.artifact"],
        ]
    
    # Strategy A: Build domain buckets
    buckets = build_domain_buckets(word_set, max_senses=max_senses)
    
    # Generate domain pairs
    domain_candidates = extract_domain_pairs(
        buckets,
        target_domain_pairs,
        min_hamming=min_hamming,
        max_per_domain_pair=max_per_domain_pair
    )
    
    # Strategy B: Extract antonym and polarity pairs
    antonym_candidates = extract_antonym_polarity_pairs(word_set, min_hamming=min_hamming)
    
    # Combine and deduplicate
    all_candidates = domain_candidates + antonym_candidates
    
    # Deduplicate by canonical pair
    seen = set()
    deduplicated = []
    for candidate in all_candidates:
        canonical = tuple(sorted((candidate['start'], candidate['end'])))
        if canonical not in seen:
            seen.add(canonical)
            deduplicated.append(candidate)
    
    # Validate pairs
    validated = validate_pairs(
        deduplicated,
        graph,
        word_freq_map,
        graph_degrees,
        min_pqs=min_pqs,
        min_distance=min_distance,
        max_distance=max_distance
    )
    
    return validated


def main():
    """Main thematic pair generation workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate thematic word ladder puzzles')
    parser.add_argument('-c', '--config', default='config/config.yaml', help='Path to config file')
    parser.add_argument('-w', '--word-list', help='Path to word list (overrides config)')
    parser.add_argument('-o', '--output', help='Output file path (overrides config)')
    parser.add_argument('--min-pqs', type=float, help='Minimum PQS threshold (overrides config)')
    parser.add_argument('--min-distance', type=int, help='Minimum intermediate steps (overrides config)')
    parser.add_argument('--max-distance', type=int, help='Maximum intermediate steps (overrides config)')
    parser.add_argument('--max-per-domain', type=int, help='Max pairs per domain pair (overrides config)')
    
    args = parser.parse_args()
    
    # Ensure NLTK data is available
    download_nltk_data()
    
    # Load config with path resolution
    from word_ladders.lexicon import load_config
    config = load_config(args.config)
    
    pair_config = config.get('pair_generation', {})
    
    # Apply CLI overrides
    word_list = args.word_list or pair_config.get('word_list', 'data/output/valid_4letter_words.txt')
    output = args.output or pair_config.get('output', 'data/output/thematic_puzzles.json')
    min_pqs = args.min_pqs if args.min_pqs is not None else pair_config.get('min_pqs', 80.0)
    min_distance = args.min_distance if args.min_distance is not None else pair_config.get('min_distance', 2)
    max_distance = args.max_distance if args.max_distance is not None else pair_config.get('max_distance', 5)
    min_hamming = pair_config.get('min_hamming_distance', 2)
    max_senses = pair_config.get('max_senses_per_word', 2)
    max_per_domain = args.max_per_domain if args.max_per_domain is not None else pair_config.get('max_per_domain_pair', 500)
    
    # Get domain pairs from config, with sensible defaults if not specified
    target_domain_pairs = pair_config.get('target_domain_pairs', [
        ["noun.animal", "noun.animal"],
        ["noun.food", "noun.food"],
        ["noun.body", "noun.body"],
        ["noun.feeling", "noun.feeling"],
        ["noun.artifact", "noun.artifact"],
    ])
    
    print("Thematic Word Pair Generator")
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
    import wordfreq
    word_freq_map = {word: wordfreq.word_frequency(word, 'en') for word in word_set}
    print(f"  Frequency map built")
    
    # Strategy A: Build domain buckets
    print("\nStrategy A: Building semantic domain buckets...")
    buckets = build_domain_buckets(word_set, max_senses=max_senses)
    print(f"  Found {len(buckets)} domains")
    
    # Show top domains by size
    sorted_domains = sorted(buckets.items(), key=lambda x: len(x[1]), reverse=True)
    print(f"  Top 10 domains:")
    for domain, words in sorted_domains[:10]:
        print(f"    {domain}: {len(words)} words")
    
    # Generate domain pairs
    print(f"\nGenerating domain pairs ({len(target_domain_pairs)} domain pairings)...")
    domain_candidates = extract_domain_pairs(
        buckets,
        target_domain_pairs,
        min_hamming=min_hamming,
        max_per_domain_pair=max_per_domain
    )
    print(f"  Generated {len(domain_candidates)} domain candidates")
    
    # Strategy B: Extract antonym pairs
    print("\nStrategy B: Extracting antonym and polarity pairs...")
    antonym_candidates = extract_antonym_polarity_pairs(word_set, min_hamming=min_hamming)
    print(f"  Generated {len(antonym_candidates)} antonym candidates")
    
    # Combine and deduplicate candidates
    print("\nCombining candidates...")
    all_candidates = domain_candidates + antonym_candidates
    
    # Deduplicate by canonical pair
    seen = set()
    deduplicated = []
    for candidate in all_candidates:
        canonical = tuple(sorted((candidate['start'], candidate['end'])))
        if canonical not in seen:
            seen.add(canonical)
            deduplicated.append(candidate)
    
    print(f"  After deduplication: {len(deduplicated)} unique candidates")
    
    # Validate pairs
    print(f"\nValidating pairs (min PQS: {min_pqs}, distance: {min_distance}-{max_distance})...")
    validated = validate_thematic_pairs(
        deduplicated,
        graph,
        word_freq_map,
        graph_degrees,
        min_pqs=min_pqs,
        min_distance=min_distance,
        max_distance=max_distance
    )
    
    print(f"  Validated {len(validated)} thematic puzzles")
    
    # Sort by PQS descending
    validated.sort(key=lambda p: p['pqs_score'], reverse=True)
    
    # Export results
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save without all_paths to reduce file size (keep sample_path)
    export_data = [
        {k: v for k, v in p.items() if k != 'all_paths'}
        for p in validated
    ]
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    print(f"\nThematic puzzles saved to: {output_path}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  Total validated puzzles: {len(validated)}")
    
    if validated:
        print(f"  PQS range: {validated[-1]['pqs_score']:.2f} - {validated[0]['pqs_score']:.2f}")
        
        # Count by theme type
        theme_counts = {}
        for p in validated:
            theme_type = p['theme_type']
            theme_counts[theme_type] = theme_counts.get(theme_type, 0) + 1
        print(f"  Theme type breakdown: {theme_counts}")
        
        # Count by difficulty
        difficulty_counts = {}
        for p in validated:
            difficulty_counts[p['difficulty']] = difficulty_counts.get(p['difficulty'], 0) + 1
        print(f"  Difficulty breakdown: {difficulty_counts}")
        
        # Show top 10 puzzles
        print("\nTop 10 puzzles by PQS:")
        for i, p in enumerate(validated[:10], 1):
            print(f"  {i}. {p['start']} -> {p['end']} ({p['theme_type']}, PQS: {p['pqs_score']}, Difficulty: {p['difficulty']})")
            print(f"     Theme: {p['theme_label']}")
    else:
        print("  No puzzles generated. Try lowering the min-pqs threshold or adjusting domain pairs.")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Iterative 4-Letter Word Ladder Lexicon Pipeline

A deterministic, reproducible data-processing pipeline to extract a high-quality,
playable set of English 4-letter words from raw lexical datasets.
"""

import json
import re
import string
from pathlib import Path
from typing import Set, Dict, List, Tuple

import nltk
import yaml
import wordfreq
from nltk.corpus import wordnet as wn


def download_nltk_data():
    """Ensure required NLTK corpora are downloaded."""
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file and resolve relative paths."""
    config_path = Path(config_path).resolve()
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Resolve relative paths in config to be relative to config file
    config_dir = config_path.parent
    if 'paths' in config:
        for key, value in config['paths'].items():
            if isinstance(value, str) and (value.startswith('.') or value.startswith('..')):
                config['paths'][key] = str((config_dir / value).resolve())
    if 'puzzle_generation' in config:
        pg = config['puzzle_generation']
        if 'word_list' in pg and (pg['word_list'].startswith('.') or pg['word_list'].startswith('..')):
            pg['word_list'] = str((config_dir / pg['word_list']).resolve())
        if 'output' in pg and (pg['output'].startswith('.') or pg['output'].startswith('..')):
            pg['output'] = str((config_dir / pg['output']).resolve())
        if 'force_puzzle_pairs' in pg and (pg['force_puzzle_pairs'].startswith('.') or pg['force_puzzle_pairs'].startswith('..')):
            pg['force_puzzle_pairs'] = str((config_dir / pg['force_puzzle_pairs']).resolve())
    if 'pair_generation' in config:
        pg = config['pair_generation']
        if 'word_list' in pg and (pg['word_list'].startswith('.') or pg['word_list'].startswith('..')):
            pg['word_list'] = str((config_dir / pg['word_list']).resolve())
        if 'output' in pg and (pg['output'].startswith('.') or pg['output'].startswith('..')):
            pg['output'] = str((config_dir / pg['output']).resolve())
    
    return config


def load_words(file_path: str) -> Set[str]:
    """
    Load words from a file, normalizing and filtering invalid entries.
    - Strips whitespace and converts to lowercase
    - Ignores empty lines and comments (lines starting with #)
    - Validates against regex ^[a-z]{4}$
    """
    words = set()
    path = Path(file_path)
    
    if not path.exists():
        return words
    
    with open(path, 'r') as f:
        for line in f:
            word = line.strip().lower()
            # Skip empty lines and comments
            if not word or word.startswith('#'):
                continue
            # Structural validation: must be exactly 4 lowercase letters
            if re.match(r'^[a-z]{4}$', word):
                words.add(word)
    
    return words


def exists_in_wordnet(word: str) -> bool:
    """Check if word exists in WordNet (has at least one synset)."""
    return len(wn.synsets(word)) > 0


def has_allowed_pos(word: str, allowed_pos_tags: Set[str]) -> bool:
    """
    Check if word has at least one synset with an allowed Part-of-Speech tag.
    """
    for synset in wn.synsets(word):
        if synset.pos() in allowed_pos_tags:
            return True
    return False


def meets_frequency_threshold(word: str, min_frequency: float) -> bool:
    """Check if word meets minimum frequency threshold."""
    freq = wordfreq.word_frequency(word, 'en')
    return freq >= min_frequency


def apply_linguistic_filters(
    candidates: Set[str],
    min_frequency: float,
    allowed_pos_tags: Set[str]
) -> Tuple[Set[str], Dict[str, int], List[Tuple[str, float]], List[Tuple[str, float]]]:
    """
    Apply automated heuristic filtering to raw dataset.
    
    Returns:
        - Filtered set of words
        - Dictionary of drop counts per stage
        - List of (word, frequency) for lowest-frequency passed words (sorted by freq)
        - List of (word, frequency) for highest-frequency failed words (sorted by freq desc)
    """
    survivors = set()
    drop_counts = {
        'regex_filtered': 0,
        'not_in_wordnet': 0,
        'invalid_pos': 0,
        'below_frequency': 0,
    }
    
    # Track frequencies for borderline analysis
    passed_with_freq = []
    failed_with_freq = []
    
    for word in candidates:
        # Stage 2.1: Existence Check (WordNet)
        if not exists_in_wordnet(word):
            drop_counts['not_in_wordnet'] += 1
            continue
        
        # Stage 2.2: Part-of-Speech Filtering
        if not has_allowed_pos(word, allowed_pos_tags):
            drop_counts['invalid_pos'] += 1
            continue
        
        # Stage 2.3: Frequency Thresholding
        freq = wordfreq.word_frequency(word, 'en')
        if freq < min_frequency:
            drop_counts['below_frequency'] += 1
            failed_with_freq.append((word, freq))
            continue
        
        # Word passed all filters
        survivors.add(word)
        passed_with_freq.append((word, freq))
    
    # Sort borderline lists for diagnostic output
    passed_with_freq.sort(key=lambda x: x[1])  # Lowest frequency first
    failed_with_freq.sort(key=lambda x: x[1], reverse=True)  # Highest frequency first
    
    return survivors, drop_counts, passed_with_freq, failed_with_freq


def apply_curation_overrides(
    candidates: Set[str],
    force_include: Set[str],
    force_exclude: Set[str]
) -> Tuple[Set[str], int]:
    """
    Apply manual curation overrides.
    
    Returns:
        - Updated candidate set
        - Count of words rescued via force_include
    """
    # Apply force_include (union)
    rescued = force_include - candidates
    candidates |= force_include
    
    # Apply force_exclude (subtract) - always wins
    candidates -= force_exclude
    
    return candidates, len(rescued)


def get_neighbors(word: str, word_set: Set[str]) -> Set[str]:
    """
    Get all 1-letter-edit neighbors of a word within the given word set.
    """
    neighbors = set()
    for i in range(len(word)):
        for c in string.ascii_lowercase:
            if c != word[i]:
                candidate = word[:i] + c + word[i+1:]
                if candidate in word_set:
                    neighbors.add(candidate)
    return neighbors


def build_graph(word_set: Set[str]) -> Dict[str, Set[str]]:
    """
    Build a graph adjacency list mapping each word to its neighbors.
    """
    graph = {}
    for word in word_set:
        graph[word] = get_neighbors(word, word_set)
    return graph


def prune_isolated_words(
    words: Set[str],
    graph: Dict[str, Set[str]]
) -> Tuple[Set[str], int]:
    """
    Phase 2 Hook: Prune isolated words (words with zero 1-letter-edit neighbors).
    
    Returns:
        - Pruned word set
        - Count of words removed
    """
    pruned = {word for word in words if len(graph[word]) > 0}
    removed_count = len(words) - len(pruned)
    return pruned, removed_count


def export_results(
    words: Set[str],
    output_path: str,
    audit_log: Dict
):
    """Export final word list and audit log."""
    # Sort words alphabetically and write to file
    sorted_words = sorted(words)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(sorted_words) + '\n')
    
    # Write audit log
    audit_path = Path(audit_log['paths']['audit_log'])
    with open(audit_path, 'w') as f:
        json.dump(audit_log, f, indent=2)


def main():
    """Main pipeline execution."""
    import sys
    
    # Parse simple args for config path
    config_path = 'config/config.yaml'
    if len(sys.argv) > 1:
        if sys.argv[1] == '-c' and len(sys.argv) > 2:
            config_path = sys.argv[2]
    
    # Ensure NLTK data is available
    download_nltk_data()
    
    # Load configuration
    config = load_config(config_path)
    paths = config['paths']
    filtering = config['filtering']
    
    # Stage 1: Ingestion & Normalization
    print("Stage 1: Ingestion & Normalization")
    raw_words = load_words(paths['raw_input'])
    force_include = load_words(paths['force_include'])
    force_exclude = load_words(paths['force_exclude'])
    
    print(f"  Raw words loaded: {len(raw_words)}")
    print(f"  Force include entries: {len(force_include)}")
    print(f"  Force exclude entries: {len(force_exclude)}")
    
    # Count regex-filtered words (non-4-letter entries from raw input)
    # We do this by checking what didn't match the pattern
    # Since load_words already filters, we estimate from total lines vs valid
    total_raw_lines = len(Path(paths['raw_input']).read_text().splitlines())
    regex_filtered = total_raw_lines - len(raw_words)
    
    # Stage 2: Automated Heuristic Filtering
    print("\nStage 2: Automated Heuristic Filtering")
    min_frequency = filtering['min_frequency']
    allowed_pos_tags = set(filtering['allowed_pos'])
    
    candidates, drop_counts, passed_with_freq, failed_with_freq = apply_linguistic_filters(
        raw_words,
        min_frequency,
        allowed_pos_tags
    )
    
    drop_counts['regex_filtered'] = regex_filtered
    
    print(f"  Regex filtered: {drop_counts['regex_filtered']}")
    print(f"  Not in WordNet: {drop_counts['not_in_wordnet']}")
    print(f"  Invalid POS: {drop_counts['invalid_pos']}")
    print(f"  Below frequency: {drop_counts['below_frequency']}")
    print(f"  Survived automated filters: {len(candidates)}")
    
    # Stage 3: Iterative Curation Overrides
    print("\nStage 3: Iterative Curation Overrides")
    candidates, rescued_count = apply_curation_overrides(
        candidates,
        force_include,
        force_exclude
    )
    
    print(f"  Rescued via force_include: {rescued_count}")
    print(f"  Removed via force_exclude: {len(force_exclude)}")
    print(f"  Final word count: {len(candidates)}")
    
    # Stage 3.5: Phase 2 Graph Connectivity Pruning
    print("\nStage 3.5: Graph Connectivity Pruning (Phase 2)")
    graph = build_graph(candidates)
    candidates, isolated_removed = prune_isolated_words(candidates, graph)
    print(f"  Isolated words removed: {isolated_removed}")
    print(f"  Connected word count: {len(candidates)}")
    
    # Stage 4: Export & Diagnostic Reporting
    print("\nStage 4: Export & Diagnostic Reporting")
    
    # Prepare audit log
    audit_log = {
        'paths': paths,
        'filtering': filtering,
        'metrics': {
            'total_raw_processed': total_raw_lines,
            'drop_counts': drop_counts,
            'rescued_via_force_include': rescued_count,
            'force_excluded_count': len(force_exclude),
            'isolated_words_removed': isolated_removed,
            'final_word_count': len(candidates),
        },
        'borderline_samples': {
            'lowest_frequency_passed': [
                {'word': w, 'frequency': f} for w, f in passed_with_freq[:50]
            ],
            'highest_frequency_failed': [
                {'word': w, 'frequency': f} for w, f in failed_with_freq[:50]
            ],
        },
    }
    
    export_results(candidates, paths['output_words'], audit_log)
    print(f"  Word list written to: {paths['output_words']}")
    print(f"  Audit log written to: {paths['audit_log']}")
    
    print("\nPipeline complete!")


if __name__ == '__main__':
    main()

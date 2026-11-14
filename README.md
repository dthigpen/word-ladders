# word-ladders

A set of scripts I have used to help generate word ladder puzzles.

## Setup

1. Create a Python virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Scripts

Run each with `--help` for more details.

### `src/build_lexicon.py`

**New:** Iterative 4-letter word ladder lexicon pipeline. This script processes raw Scrabble dictionaries to extract a high-quality, playable set of English 4-letter words (nouns, verbs, and adjectives) while filtering out obscure terms and supporting human-in-the-loop curation.

```bash
python src/build_lexicon.py
```

The pipeline:
- Reads from `data/raw/scrabble_words.txt`
- Applies linguistic filters (WordNet existence, POS tags, frequency threshold)
- Applies manual overrides from `data/curation/force_include.txt` and `data/curation/force_exclude.txt`
- Outputs to `data/output/valid_4letter_words.txt`
- Generates `data/output/pipeline_audit_log.json` with metrics and borderline samples for tuning

**Iterative Curation Workflow:**
1. Run the pipeline with default settings
2. Review `pipeline_audit_log.json` (borderline passed/failed lists) or test puzzle generation
3. Add inappropriate words to `data/curation/force_exclude.txt`
4. Add missing good words to `data/curation/force_include.txt`
5. Adjust `min_frequency` in `config.yaml` if needed
6. Re-run the pipeline

See `docs/WORDLIST_GEN_DESIGN.md` for full architectural details.

### `word_list.py`

Generates a word list given various word files (legacy script).

```bash
python word_list.py
```

### `src/generate_puzzles.py`

**New:** Generates high-quality word ladder puzzles from the curated word list, filtering by Puzzle Quality Score (PQS) and tagging by difficulty (Easy/Medium/Hard/Expert). Can also solve specific word ladder pairs.

```bash
# Generate puzzles
python src/generate_puzzles.py

# Solve a specific pair
python src/generate_puzzles.py --solve warm cold
```

Options:
- `-n, --num-puzzles`: Number of puzzles to generate (default: 50)
- `--min-pqs`: Minimum PQS threshold (default: 80.0)
- `--min-distance`: Minimum intermediate steps (default: 3)
- `--max-distance`: Maximum intermediate steps (default: 6)
- `-w, --word-list`: Path to word list (default: data/output/valid_4letter_words.txt)
- `-o, --output`: Output file path (default: data/output/generated_puzzles.json)
- `--solve START END`: Solve a specific word ladder pair

The generator:
- Loads the curated word list
- Builds a graph of word connections
- Samples random word pairs and finds all shortest paths using BFS
- Calculates PQS (vocabulary commonality, path diversity, optimal length, graph connectivity)
- Tags puzzles by difficulty using CDS (Composite Difficulty Score)
- Filters to only keep puzzles meeting the PQS threshold
- Outputs puzzles as JSON with all solution paths and metadata

See `docs/word_ladder_puzzle_quality_score_specification.md` and `docs/word_ladder_difficulty_tagging_specification.md` for detailed scoring algorithms.
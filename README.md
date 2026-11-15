# Word Ladders

Toolkit for generating and solving word ladder puzzles.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

### Build Word List

```bash
word-ladders lexicon
```

Reads from `data/raw/scrabble_words.txt`, applies filters, and outputs to `data/output/valid_4letter_words.txt`.

Edit `data/curation/force_include.txt` and `data/curation/force_exclude.txt` to manually add/remove words.

### Generate Random Puzzles

```bash
word-ladders puzzles
word-ladders puzzles --solve warm cold
word-ladders puzzles --min-pqs 70 --seed 42 --easy 10 --medium 20
```

Generates puzzles with PQS filtering and difficulty tagging. See `config/config.yaml` for defaults.

### Generate Thematic Puzzles

```bash
word-ladders thematic
```

Uses WordNet to find semantically related word pairs (same category, antonyms, cross-domain).

## Configuration

All settings in `config/config.yaml`:
- `paths`: File paths
- `filtering`: Word list parameters
- `puzzle_generation`: Random puzzle settings
- `pair_generation`: Thematic puzzle settings

## Project Structure

```
word-ladders/
├── config/config.yaml
├── data/
│   ├── raw/           # Input dictionaries
│   ├── curation/      # Manual overrides
│   ├── output/        # Generated outputs (gitignored)
│   └── curated/       # Final word lists and puzzle sets
└── src/word_ladders/  # Package code
```

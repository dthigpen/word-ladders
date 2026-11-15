# Curated Word Lists and Puzzles

This directory contains final, curated outputs ready to use.

## Files

- `wordlist.txt` - 1,923 filtered 4-letter words (nouns, verbs, adjectives)
- `puzzles.json` - Randomly generated puzzles with PQS and difficulty tags
- `thematic_puzzles.json` - Semantically related word pairs (intra-domain, cross-domain, antonyms)

## Regenerating

To update these files:

```bash
word-ladders lexicon
word-ladders puzzles
word-ladders thematic
cp data/output/valid_4letter_words.txt data/curated/wordlist.txt
cp data/output/generated_puzzles.json data/curated/puzzles.json
cp data/output/thematic_puzzles.json data/curated/thematic_puzzles.json
```

## Puzzle JSON Format

```json
{
  "id": "warm_cold",
  "start": "warm",
  "end": "cold",
  "theme_type": "antonym_direct",
  "theme_label": "Opposites (warm / cold)",
  "intermediate_steps": 3,
  "num_shortest_paths": 3,
  "pqs_score": 73.0,
  "difficulty": "Medium",
  "sample_path": ["warm", "ward", "card", "cord", "cold"]
}
```

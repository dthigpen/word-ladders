# word-ladders

A set of scripts I have used to help generate word ladder puzzles.

## Usage

Just install the dependencies with `pip install -r requirements.txt`, then run the desired script. E.g. `python word_list.py`.

## Scripts

Run each with `--help` for more details.

### `ladder.py`

Right now this script just solves a given word ladder, given optional constraints.

```bash
python ladder.py --solve warm cold
```

Output:

```
cold cord word ward warm
```

### `word_list.py`

Generates a word list given various word files.

```bash
python word_list.py
```
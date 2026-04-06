import argparse
import string
from pathlib import Path
from collections import deque

def load_words(path: str):
    with open(path) as f:
        return set(word.strip().lower() for word in f)


def neighbors(word: str, words: set[str]):
    for i in range(len(word)):
        for c in string.ascii_lowercase:
            if c != word[i]:
                candidate = word[:i] + c + word[i+1:]
                if candidate in words:
                    yield candidate


def find_ladder(start: str, end: str, words: set[str]):
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        word, path = queue.popleft()

        if word == end:
            return path

        for next_word in neighbors(word, words):
            if next_word not in visited:
                visited.add(next_word)
                queue.append((next_word, path + [next_word]))

def existing_file(p: str) -> Path:
    p = Path(p)
    if p.is_file():
        return p
    raise argparse.ArgumentTypeError('File path must exist')

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate word ladder solutions')
    parser.add_argument('-w', '--words', required=True, type=existing_file, help='Path to the word list that the words in the chain will come from')
    parser.add_argument('--pair',nargs='2', type=str, help='Start and end words to generate a chain for')
    parser.add_argument('--min-steps', type=int, help='The minimum number for steps in the chain')
    parser.add_argument('--max-steps', type=int, help='The maximum number for steps in the chain')
    parser.add_argument('-d', '--delimiter', default=' ', type=str, help='Delimiter between each word in the chain. Default to space')
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    words = load_words(args.words)
    start_word, end_word = args.pair
    ladder = find_ladder(start_word, end_word, words)

    print(args.delimiter.join(ladder))    
    
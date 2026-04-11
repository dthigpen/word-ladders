import argparse
import itertools
from pathlib import Path
from wordfreq import zipf_frequency
from collections.abc import Iterable, Iterator

def existing_file(p: str) -> Path:
    p = Path(p)
    if p.is_file():
        return p
    raise argparse.ArgumentTypeError('File path must exist')

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate a word list')

    parser.add_argument('-s', '--sources', nargs='+', default=[Path('scrabble_2023.txt')], type=existing_file, help='Path to the word list that the words in the chain will come from')
    parser.add_argument('-b', '--bad-words', default='bad_words.txt', type=existing_file, help='Path to the the "bad" words list to be filtered out')
    parser.add_argument('-g', '--good-words', default='good_words.txt', type=existing_file, help='Path to extra "good" words list to be filtered in')
    parser.add_argument('-o', '--out-file', type=Path, help='Output file path')
    parser.add_argument('--min-score', type=float, default=3.5, help='Minimum zipf frequency score. Defaults to 3.5')
    parser.add_argument('--length', type=float, default=4, help='Length of the words to use. Defaults to 4')
    return parser.parse_args()


def normalize(words: Iterable[str], length=4) -> Iterator[str]:
    for word in words:
        word = word.strip().lower()
        if len(word) == length and word.isalpha():
            yield word

if __name__ == '__main__':
    args = parse_args()
    # base words include good words + lots of junk
    sources = args.sources
    words = set()
    for p in sources:
        print(f'Reading source words from: {p}')
        new_words = normalize(p.read_text().splitlines())
        words.update(new_words)

    # filter out junk by frequency score
    zf = lambda w: zipf_frequency(w, 'en') >= args.min_score
    words = filter(zf, words)

    
    # manually filter out words
    if args.bad_words:
        print(f'Filtering out bad words from: {args.bad_words}')
        bad_words = set(args.bad_words.read_text().splitlines())
        words = filter(lambda w: w not in bad_words, words)
    
    # manually add words
    if args.good_words:
        print(f'Adding additional good words from: {args.good_words}')
        missing_words = args.good_words.read_text().splitlines()
        words = itertools.chain(words, missing_words)
    
    # ensure nothing unexpected slipped through
    words = normalize(words)
    words = sorted(list(set(words)))
    print(f'Word count: {len(words)}')
    Path('words.txt').write_text('\n'.join(words))

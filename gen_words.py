from pathlib import Path
from wordfreq import top_n_list
import itertools


import itertools

if __name__ == '__main__':
    words_file = Path('words.txt')
    words = [w.strip().lower() for w in top_n_list('en', 50_000) if w.strip().isalpha()]
    words = [w for w in words if len(w) == 4]
    words = itertools.islice(words, 1000)
    words_file.write_text('\n'.join(words))

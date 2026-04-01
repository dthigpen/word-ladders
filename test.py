import word_ladders as wl
from pathlib import Path

import itertools

if __name__ == '__main__':
    words = wl.load_words(max_words=10000, min_length=4, max_length=4)
    # index = wl.build_pattern_index(words)
    # ladder = wl.shortest_ladder('warm', 'cold', words, index)
    # print(ladder)
    print(f'Words in dataset: {len(words)}')
    num_ladders = 1000
    for i in range(3, 6):
        print(f'Generating {num_ladders} word ladders with {i} steps')
        ladders = wl.find_ladders(words=words, min_steps=i, max_steps=i, sample_size=5000)
        ladders = list(itertools.islice(ladders, num_ladders))
        lines = [', '.join(l) for l in ladders]
        Path(f'word_ladders_{i}.csv').write_text('\n'.join(lines), encoding="utf-8")

from word_ladders.words import load_words
from word_ladders.core import build_pattern_index, shortest_ladder

import random

def find_ladders(words: list[str]=None, pairs: list[tuple[str, str]]=None, min_steps=2, max_steps=5, limit=None, sample_size=1000):
    """
    Generate word ladders that meet step constraints.

    Args:
        words: Optional list of words. If None, loads default 4-letter words.
        pairs: Optional iterable of (start, end) pairs. If None, random pairs are sampled.
        min_steps: Minimum number of steps (edges)
        max_steps: Maximum number of steps
        limit: Max number of ladders to yield (None = no limit)
        sample_size: Number of random pairs to try if pairs not provided

    Yields:
        path_tuple
    """

    # --- Load + prepare words ---
    if words is None:
        words = load_words(min_length=4, max_length=4)

    index = build_pattern_index(words)

    # --- Track seen pairs to avoid duplicates ---
    seen_pairs = set()

    # --- Pair source ---
    if pairs is None:
        words_list = list(words)

        def pair_generator():
            attempts = 0
            while True:
                w1, w2 = random.sample(words_list, 2)

                # normalize ordering so (a,b) == (b,a)
                key = tuple(sorted((w1, w2)))
                if key in seen_pairs:
                    continue

                seen_pairs.add(key)
                yield w1, w2

                attempts += 1
                if sample_size and attempts >= sample_size:
                    return

        pair_iter = pair_generator()

    else:
        def pair_generator():
            for w1, w2 in pairs:
                key = tuple(sorted((w1, w2)))
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                yield w1, w2

        pair_iter = pair_generator()

    # --- Main loop ---
    yielded = 0

    for start, end in pair_iter:
        path = shortest_ladder(start, end, words, index)

        if not path:
            continue

        steps = len(path) - 1

        if min_steps <= steps <= max_steps:
            yield path

            yielded += 1
            if limit is not None and yielded >= limit:
                return

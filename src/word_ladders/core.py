from collections import deque


def build_pattern_index(words: list[str]) -> dict[str, str]:
    """
    Precompute patterns like:
    h*t -> ["hot", "hat", ...]
    """
    index = {}
    for word in words:
        for i in range(len(word)):
            pattern = word[:i] + "*" + word[i+1:]
            index.setdefault(pattern, []).append(word)
    return index


def get_neighbors(word: str, index: dict[str, str]) -> set[str]:
    """Find all words differing by one letter."""
    neighbors = set()
    for i in range(len(word)):
        pattern = word[:i] + "*" + word[i+1:]
        neighbors.update(index.get(pattern, []))
    neighbors.discard(word)
    return neighbors


def shortest_ladder(start: str, end: str, words: list[str], index: dict[str, str]=None) -> tuple[str]:
    """
    BFS to find shortest word ladder.
    Returns a tuple path or None.
    """
    if len(start) != len(end):
        return None

    # words = normalize_words(words, length=len(start))
    if end not in words:
        return None

    if not index:
        index = build_pattern_index(words)

    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        word, path = queue.popleft()

        if word == end:
            return tuple(path)

        for neighbor in get_neighbors(word, index):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None

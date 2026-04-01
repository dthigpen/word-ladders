from wordfreq import top_n_list


def load_words(
    language="en",
    max_words=10000,
    min_length=None,
    max_length=None,
):
    """
    Load common words using wordfreq. All words are returned in lowercase.

    Args:
        language: Language code (default "en")
        max_words: Number of most frequent words to include
        min_length: Optional minimum word length
        max_length: Optional maximum word length

    Returns:
        List of words (strings)
    """
    words = normalize_words(top_n_list(language, max_words))

    if min_length is not None:
        words = [w for w in words if len(w) >= min_length]

    if max_length is not None:
        words = [w for w in words if len(w) <= max_length]

    return words

def normalize_words(words, length=None):
    """Lowercase and optionally filter words by length."""
    words = {w.lower() for w in words if (length is None or len(w) == length) and w.isalpha()}
    return words

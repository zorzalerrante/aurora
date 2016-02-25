from collections import Counter
import numpy as np

def entropy(predictions, normalize=False, n_categories=None):
    counts = Counter(list(predictions)).values()

    if len(counts) <= 1:
        return 0.0

    total_count = float(len(predictions))

    if not total_count:
        return 0.0

    probabilities = []
    for count in counts:
        probabilities.append(count / total_count)

    probabilities = np.array(probabilities)
    value = - np.sum(probabilities * np.log(probabilities))
    if normalize is True:
        if n_categories is not None:
            value /= float(np.log(n_categories))
        else:
            value /= float(np.log(len(counts)))
    return value
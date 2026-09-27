"""
Official Evaluation Metric for Amazon ML Challenge 2026.

Metric: Macro-averaged F_0.5 score per Source 1 entity.
Formula:
    F_0.5 = (1.25 * Precision * Recall) / (0.25 * Precision + Recall)

Special Rules (Verified from Official README):
- Macro-averaged across ALL Source 1 entities in the evaluation set.
- Singletons (S1 entities with 0 true matches):
    - Correctly predicting empty list: score = 1.0
    - Predicting any match: score = 0.0
"""

from typing import Dict, Set, Tuple


def compute_f05(precision: float, recall: float) -> float:
    """Compute F_0.5 score given precision and recall."""
    if precision + recall == 0.0:
        return 0.0
    return (1.25 * precision * recall) / (0.25 * precision + recall)


def evaluate_predictions(
    ground_truth: Dict[str, Set[str]],
    predictions: Dict[str, Set[str]]
) -> Dict[str, float]:
    """
    Evaluate predicted matches against ground truth.

    Args:
        ground_truth: mapping of source1_id -> set of true matching S2/S3 IDs.
        predictions: mapping of source1_id -> set of predicted matching S2/S3 IDs.

    Returns:
        Dictionary containing:
            - 'macro_f05': the primary official leaderboard metric
            - 'macro_precision': macro-averaged precision
            - 'macro_recall': macro-averaged recall
            - 'singleton_accuracy': accuracy on 0-match entities
            - 'total_entities': number of S1 entities evaluated
            - 'singletons_count': number of true singletons
    """
    total_f05 = 0.0
    total_precision = 0.0
    total_recall = 0.0
    singleton_correct = 0
    singleton_count = 0

    for s1_id, true_matches in ground_truth.items():
        pred_matches = predictions.get(s1_id, set())

        # Singleton case: ground truth has 0 matches
        if not true_matches:
            singleton_count += 1
            if not pred_matches:
                score = 1.0
                singleton_correct += 1
                prec = 1.0
                rec = 1.0
            else:
                score = 0.0
                prec = 0.0
                rec = 1.0
        else:
            # Non-singleton case
            if not pred_matches:
                score = 0.0
                prec = 0.0
                rec = 0.0
            else:
                tp = len(true_matches.intersection(pred_matches))
                prec = tp / len(pred_matches)
                rec = tp / len(true_matches)
                score = compute_f05(prec, rec)

        total_f05 += score
        total_precision += prec
        total_recall += rec

    n = len(ground_truth)
    if n == 0:
        return {
            "macro_f05": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "singleton_accuracy": 0.0,
            "total_entities": 0,
            "singletons_count": 0,
        }

    return {
        "macro_f05": total_f05 / n,
        "macro_precision": total_precision / n,
        "macro_recall": total_recall / n,
        "singleton_accuracy": (singleton_correct / singleton_count) if singleton_count > 0 else 1.0,
        "total_entities": n,
        "singletons_count": singleton_count,
    }

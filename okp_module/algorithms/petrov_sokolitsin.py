import numpy as np


def completion_matrix(B, seq):
    B = np.array(B, dtype=float)
    n = len(seq)
    m = B.shape[1]
    C = np.zeros((n, m), dtype=float)

    for i, job in enumerate(seq):
        for j in range(m):
            if i == 0 and j == 0:
                C[i, j] = B[job, j]
            elif i == 0:
                C[i, j] = C[i, j - 1] + B[job, j]
            elif j == 0:
                C[i, j] = C[i - 1, j] + B[job, j]
            else:
                C[i, j] = max(C[i - 1, j], C[i, j - 1]) + B[job, j]

    return C


def petrov_sokolitsin(B):
    """
    Метод Петрова–Соколицина.
    """
    B = np.array(B, dtype=float)
    n, m = B.shape

    if m < 2:
        raise ValueError("Для метода Петрова-Соколицина требуется минимум 2 станка")

    sum_without_first = np.sum(B[:, 1:], axis=1)
    sum_without_last = np.sum(B[:, :-1], axis=1)
    diff = sum_without_first - sum_without_last

    jobs = list(range(n))

    seq1 = sorted(jobs, key=lambda i: (-sum_without_first[i], i))
    seq2 = sorted(jobs, key=lambda i: (sum_without_last[i], i))
    seq3 = sorted(jobs, key=lambda i: (-diff[i], i))

    C1 = completion_matrix(B, seq1)
    t1 = float(C1[-1, -1])

    C2 = completion_matrix(B, seq2)
    t2 = float(C2[-1, -1])

    C3 = completion_matrix(B, seq3)
    t3 = float(C3[-1, -1])

    variants = [
        ("Убывание суммы без первого станка", seq1, C1, t1),
        ("Возрастание суммы без последнего станка", seq2, C2, t2),
        ("Убывание разности", seq3, C3, t3),
    ]
    best_name, best_seq, best_C, best_t = min(variants, key=lambda x: x[3])

    details = {
        "method": "petrov_sokolitsin",
        "sum_without_first": [float(x) for x in sum_without_first],
        "sum_without_last": [float(x) for x in sum_without_last],
        "diff": [float(x) for x in diff],
        "variants": [
            {
                "name": name,
                "sequence": [x + 1 for x in seq],
                "cycle": float(t),
                "completion_matrix": C.tolist(),
            }
            for name, seq, C, t in variants
        ],
        "best_variant": best_name,
        "final_sequence": [x + 1 for x in best_seq],
        "completion_matrix": best_C.tolist(),
    }

    return best_seq, best_C, best_t, details
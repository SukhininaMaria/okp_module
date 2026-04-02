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


def johnson_nmachines(B):
    """
    Модифицированный метод Джонсона для N станков.
    """
    B = np.array(B, dtype=float)
    n, m = B.shape

    if m < 2:
        raise ValueError("Для метода Джонсона требуется минимум 2 станка")

    jobs = list(range(n))
    seq = [None] * n
    left = 0
    right = n - 1
    steps = []

    while jobs:
        min_val = np.inf
        min_job = None
        place_left = True

        row_snapshot = []
        for j in jobs:
            first_time = B[j, 0]
            last_time = B[j, m - 1]
            row_snapshot.append(
                {
                    "job": j + 1,
                    "first_machine": float(first_time),
                    "last_machine": float(last_time),
                }
            )

            if first_time < min_val:
                min_val = first_time
                min_job = j
                place_left = True

            if last_time < min_val:
                min_val = last_time
                min_job = j
                place_left = False

        if place_left:
            seq[left] = min_job
            position = left + 1
            side = "начало"
            left += 1
        else:
            seq[right] = min_job
            position = right + 1
            side = "конец"
            right -= 1

        steps.append(
            {
                "candidates": row_snapshot,
                "chosen_job": min_job + 1,
                "chosen_value": float(min_val),
                "placed_to": side,
                "position": position,
                "current_sequence": [x + 1 if x is not None else "-" for x in seq],
            }
        )

        jobs.remove(min_job)

    C = completion_matrix(B, seq)
    total_time = float(C[-1, -1])

    details = {
        "method": "johnson_nmachines",
        "final_sequence": [x + 1 for x in seq],
        "completion_matrix": C.tolist(),
        "steps": steps,
    }

    return seq, C, total_time, details
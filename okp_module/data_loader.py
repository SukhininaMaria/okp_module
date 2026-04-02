import pandas as pd
import numpy as np


def load_excel(file_path):
    """Возвращает числовую матрицу из Excel"""
    df = pd.read_excel(file_path, header=None)
    mat = df.apply(pd.to_numeric, errors='coerce').fillna(0).to_numpy(dtype=float)
    return mat


def generate_random_matrix(n, m, min_time=1, max_time=20):
    return np.random.randint(min_time, max_time + 1, size=(n, m))
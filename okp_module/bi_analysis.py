import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

def calculate_bi_metrics(B, seq):
    B = np.array(B, dtype=float)
    n_jobs, n_machines = B.shape
    if seq is None:
        seq = list(range(n_jobs))

    start_time = np.zeros((n_jobs, n_machines))
    end_time = np.zeros((n_jobs, n_machines))
    for i in range(n_machines):
        for idx, job in enumerate(seq):
            if i==0 and idx==0:
                start_time[idx,i]=0
            elif i==0:
                start_time[idx,i] = end_time[idx-1,i]
            elif idx==0:
                start_time[idx,i] = end_time[idx,i-1]
            else:
                start_time[idx,i] = max(end_time[idx-1,i], end_time[idx,i-1])
            end_time[idx,i] = start_time[idx,i] + B[job,i]

    idle_times = [float(max(0, start_time[j,i] - end_time[j-1,i])) if j>0 else 0.0
                  for i in range(n_machines) for j in range(n_jobs)]
    # более корректный вариант
    idle_times = []
    for i in range(n_machines):
        total_idle = 0.0
        for j in range(1, n_jobs):
            total_idle += max(0.0, start_time[j,i] - end_time[j-1,i])
        idle_times.append(total_idle)

    wait_times = []
    for j in range(n_jobs):
        wait = 0.0
        for i in range(1, n_machines):
            wait += max(0.0, start_time[j,i] - end_time[j,i-1])
        wait_times.append(wait)

    total_time = float(np.max(end_time))
    load_percent = [float(np.sum(B[:,i])/total_time*100.0) for i in range(n_machines)]

    metrics = {
        "idle_times": idle_times,           # float
        "wait_times": wait_times,           # float
        "load_percent": load_percent,       # float
        "total_cycle": total_time           # float
    }
    return metrics

def create_bi_plots(B, seq):
    metrics = calculate_bi_metrics(B, seq)
    canvases = []

    # Загрузка станков
    fig1, ax1 = plt.subplots(figsize=(6,3))
    ax1.bar(range(len(metrics['load_percent'])), metrics['load_percent'], color='skyblue')
    ax1.set_xticks(range(len(metrics['load_percent'])))
    ax1.set_xticklabels([f"Станок {i+1}" for i in range(len(metrics['load_percent']))])
    ax1.set_ylabel("Загрузка (%)")
    ax1.set_title("Загрузка станков")
    canvases.append(FigureCanvas(fig1))

    # Простой станков
    fig2, ax2 = plt.subplots(figsize=(6,3))
    ax2.bar(range(len(metrics['idle_times'])), metrics['idle_times'], color='salmon')
    ax2.set_xticks(range(len(metrics['idle_times'])))
    ax2.set_xticklabels([f"Станок {i+1}" for i in range(len(metrics['idle_times']))])
    ax2.set_ylabel("Простой")
    ax2.set_title("Простой станков")
    canvases.append(FigureCanvas(fig2))

    # Время ожидания деталей
    fig3, ax3 = plt.subplots(figsize=(6,3))
    ax3.bar(range(len(metrics['wait_times'])), metrics['wait_times'], color='lightgreen')
    ax3.set_xticks(range(len(metrics['wait_times'])))
    ax3.set_xticklabels([f"Деталь {i+1}" for i in range(len(metrics['wait_times']))])
    ax3.set_ylabel("Ожидание")
    ax3.set_title("Время ожидания деталей")
    canvases.append(FigureCanvas(fig3))

    return canvases, metrics
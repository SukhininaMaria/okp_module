import numpy as np
import matplotlib.pyplot as plt
import colorsys
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


def _random_color_for_job(job, brightness=0.8):
    rng = np.random.default_rng(seed=job + 12345)
    h = rng.random()
    s = 0.65
    v = max(0.2, min(1.0, brightness))
    return colorsys.hsv_to_rgb(h, s, v)


def _color_for_job(job, color_mode="by_job", brightness=0.8):
    if color_mode == "random":
        return _random_color_for_job(job, brightness)
    return plt.get_cmap("tab10")(job % 10)


def _build_bar_label(job, width):
    """
    Внутри блока показываем только номер детали.
    Для очень узких блоков уменьшаем шрифт.
    """
    if width < 4:
        return f"{job + 1}", 7
    if width < 8:
        return f"{job + 1}", 8
    return f"{job + 1}", 9


def plot_gantt_canvas(
    B,
    seq=None,
    parent=None,
    time_offset=0,
    show_duration=True,   # оставлено для совместимости с GUI
    color_mode="by_job",
    brightness=0.8,
    scale_height=True,
    row_gap=30,
):
    B = np.array(B, dtype=float)
    n_jobs, n_machines = B.shape

    if seq is None:
        seq = list(range(n_jobs))
    seq = [int(s) for s in seq]

    start_time = np.zeros((len(seq), n_machines), dtype=float)
    end_time = np.zeros((len(seq), n_machines), dtype=float)

    for i in range(n_machines):
        for idx, job in enumerate(seq):
            if i == 0 and idx == 0:
                start_time[idx, i] = 0
            elif i == 0:
                start_time[idx, i] = end_time[idx - 1, i]
            elif idx == 0:
                start_time[idx, i] = end_time[idx, i - 1]
            else:
                start_time[idx, i] = max(end_time[idx - 1, i], end_time[idx, i - 1])

            end_time[idx, i] = start_time[idx, i] + B[job, i]

    fig_height = max(3.8, n_machines * 1.15 if scale_height else n_machines * 0.9)
    fig = Figure(figsize=(11.5, fig_height))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)

    if parent is not None:
        canvas.setParent(parent)

    ax.grid(True, linestyle="--", alpha=0.35)

    y_step = row_gap / 30.0 if scale_height else 1.0
    y_positions = [i * y_step for i in range(n_machines)]
    bar_height = min(0.62, 0.48 * y_step if scale_height else 0.42)

    bars_info = []

    for i in range(n_machines):
        y = y_positions[i]
        for idx, job in enumerate(seq):
            width = B[job, i]
            left = start_time[idx, i] + time_offset
            right = end_time[idx, i] + time_offset

            color = _color_for_job(job, color_mode=color_mode, brightness=brightness)

            patch = ax.barh(
                y=y,
                width=width,
                left=left,
                height=bar_height,
                color=color,
                edgecolor="black",
                alpha=0.9,
                linewidth=1.0,
            )[0]

            text, fontsize = _build_bar_label(job=job, width=width)
            text_color = "white" if width >= 8 else "black"

            ax.text(
                left + width / 2,
                y,
                text,
                ha="center",
                va="center",
                color=text_color,
                fontsize=fontsize,
                fontweight="bold",
                clip_on=True,
            )

            bars_info.append(
                {
                    "patch": patch,
                    "job": job + 1,
                    "machine": i + 1,
                    "start": left,
                    "end": right,
                    "duration": width,
                }
            )

    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"Станок {i + 1}" for i in range(n_machines)], fontsize=10)
    ax.set_xlabel("Время", fontsize=10)
    ax.set_title("Диаграмма Ганта", fontsize=11, pad=10)
    ax.tick_params(axis="x", labelsize=9)
    ax.invert_yaxis()

    fig.subplots_adjust(left=0.14, right=0.985, top=0.88, bottom=0.14)

    # ---------- Tooltip ----------
    annot = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(14, 14),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=9,
        bbox=dict(
            boxstyle="round,pad=0.45",
            fc="#fff8dc",
            ec="#666666",
            lw=0.9,
            alpha=0.98,
        ),
        annotation_clip=False,
    )
    annot.set_visible(False)

    def update_annot(bar_data):
        patch = bar_data["patch"]
        x = patch.get_x() + patch.get_width() / 2
        y = patch.get_y() + patch.get_height() / 2
        annot.xy = (x, y)
        annot.set_text(
            f"Деталь: {bar_data['job']}\n"
            f"Станок: {bar_data['machine']}\n"
            f"Начало: {int(bar_data['start'])}\n"
            f"Конец: {int(bar_data['end'])}\n"
            f"Длительность: {int(bar_data['duration'])}"
        )

    def hover(event):
        if event.inaxes != ax:
            if annot.get_visible():
                annot.set_visible(False)
                canvas.draw_idle()
            return

        found = False
        for bar_data in bars_info:
            contains, _ = bar_data["patch"].contains(event)
            if contains:
                update_annot(bar_data)
                annot.set_visible(True)
                canvas.draw_idle()
                found = True
                break

        if not found and annot.get_visible():
            annot.set_visible(False)
            canvas.draw_idle()

    canvas.mpl_connect("motion_notify_event", hover)
    # -----------------------------

    canvas.draw()
    return canvas
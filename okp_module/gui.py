from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QPushButton, QTableWidget, QTextEdit, QComboBox, QFileDialog,
    QVBoxLayout, QWidget, QHBoxLayout, QLabel, QSpinBox, QTableWidgetItem,
    QTabWidget, QCheckBox, QGroupBox, QFormLayout, QSplitter, QHeaderView,
    QScrollArea, QMessageBox
)
import numpy as np

from gantt_plot import plot_gantt_canvas
from data_loader import load_excel, generate_random_matrix as generate_random_matrix_data
from algorithms import johnson_nmachines, petrov_sokolitsin
from bi_analysis import create_bi_plots, calculate_bi_metrics


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Модуль ОКП")
        self.resize(1400, 850)

        self.matrix_B = None
        self.seq = None
        self.details = None

        self.init_ui()
        self.statusBar().showMessage("Готово к работе")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QHBoxLayout()
        central_widget.setLayout(root_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        # ---------------- Левая панель ----------------
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)

        # Источник данных
        source_group = QGroupBox("Источник данных")
        source_layout = QHBoxLayout()
        source_group.setLayout(source_layout)

        self.load_btn = QPushButton("Загрузить Excel")
        self.load_btn.clicked.connect(self.load_excel_file)
        source_layout.addWidget(self.load_btn)

        self.random_btn = QPushButton("Случайная матрица")
        self.random_btn.clicked.connect(self.generate_random_matrix)
        source_layout.addWidget(self.random_btn)

        left_layout.addWidget(source_group)

        # Параметры задачи
        params_group = QGroupBox("Параметры задачи")
        params_layout = QFormLayout()
        params_group.setLayout(params_layout)

        self.n_spin = QSpinBox()
        self.n_spin.setRange(3, 100)
        self.n_spin.setValue(6)
        self.n_spin.valueChanged.connect(self.resize_table_to_spins)
        params_layout.addRow("Количество деталей:", self.n_spin)

        self.m_spin = QSpinBox()
        self.m_spin.setRange(3, 100)
        self.m_spin.setValue(3)
        self.m_spin.valueChanged.connect(self.resize_table_to_spins)
        params_layout.addRow("Количество станков:", self.m_spin)

        self.min_time_spin = QSpinBox()
        self.min_time_spin.setRange(1, 999)
        self.min_time_spin.setValue(1)
        params_layout.addRow("Мин. время:", self.min_time_spin)

        self.max_time_spin = QSpinBox()
        self.max_time_spin.setRange(1, 999)
        self.max_time_spin.setValue(20)
        params_layout.addRow("Макс. время:", self.max_time_spin)

        self.algo_box = QComboBox()
        self.algo_box.addItems(["Джонсон N станков", "Петрова-Соколицина"])
        params_layout.addRow("Метод:", self.algo_box)

        left_layout.addWidget(params_group)

        # Настройки диаграммы Ганта
        gantt_group = QGroupBox("Настройки диаграммы Ганта")
        gantt_layout = QFormLayout()
        gantt_group.setLayout(gantt_layout)

        self.show_duration_cb = QCheckBox("Показывать длительность")
        self.show_duration_cb.setChecked(True)
        gantt_layout.addRow(self.show_duration_cb)

        self.color_mode_box = QComboBox()
        self.color_mode_box.addItems(["По детали", "Случайные"])
        gantt_layout.addRow("Цвет:", self.color_mode_box)

        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(20, 100)
        self.brightness_spin.setValue(80)
        gantt_layout.addRow("Яркость (%):", self.brightness_spin)

        self.scale_height_cb = QCheckBox("Масштабировать высоту")
        self.scale_height_cb.setChecked(True)
        gantt_layout.addRow(self.scale_height_cb)

        self.row_gap_spin = QSpinBox()
        self.row_gap_spin.setRange(20, 100)
        self.row_gap_spin.setValue(30)
        gantt_layout.addRow("Расстояние между станками:", self.row_gap_spin)

        left_layout.addWidget(gantt_group)

        # Действия
        actions_group = QGroupBox("Действия")
        actions_layout = QHBoxLayout()
        actions_group.setLayout(actions_layout)

        self.update_matrix_btn = QPushButton("Применить изменения")
        self.update_matrix_btn.clicked.connect(self.update_matrix_from_table)
        actions_layout.addWidget(self.update_matrix_btn)

        self.calc_btn = QPushButton("Рассчитать")
        self.calc_btn.clicked.connect(self.calculate)
        self.calc_btn.setMinimumHeight(36)
        actions_layout.addWidget(self.calc_btn)

        left_layout.addWidget(actions_group)

        # Таблица матрицы
        table_group = QGroupBox("Матрица B")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.table_B = QTableWidget()
        self.table_B.setAlternatingRowColors(True)
        self.table_B.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_B.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.table_B)

        left_layout.addWidget(table_group, stretch=1)

        # ---------------- Правая панель ----------------
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)

        # Вкладка отчёта
        self.report_tab = QWidget()
        report_layout = QVBoxLayout()
        self.report_tab.setLayout(report_layout)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        report_layout.addWidget(self.result_text)

        self.tabs.addTab(self.report_tab, "Отчёт")

        # Вкладка диаграммы Ганта
        self.gantt_tab = QWidget()
        gantt_tab_layout = QVBoxLayout()
        self.gantt_tab.setLayout(gantt_tab_layout)

        self.gantt_scroll = QScrollArea()
        self.gantt_scroll.setWidgetResizable(True)
        self.gantt_container = QWidget()
        self.gantt_container_layout = QVBoxLayout()
        self.gantt_container.setLayout(self.gantt_container_layout)
        self.gantt_scroll.setWidget(self.gantt_container)
        gantt_tab_layout.addWidget(self.gantt_scroll)

        self.tabs.addTab(self.gantt_tab, "Диаграмма Ганта")

        # Вкладка BI
        self.bi_tab = QWidget()
        bi_tab_layout = QVBoxLayout()
        self.bi_tab.setLayout(bi_tab_layout)

        self.bi_scroll = QScrollArea()
        self.bi_scroll.setWidgetResizable(True)
        self.bi_container = QWidget()
        self.bi_container_layout = QVBoxLayout()
        self.bi_container.setLayout(self.bi_container_layout)
        self.bi_scroll.setWidget(self.bi_container)
        bi_tab_layout.addWidget(self.bi_scroll)

        self.tabs.addTab(self.bi_tab, "BI-аналитика")

        splitter.setSizes([500, 900])

        # Инициализация пустой таблицы
        self.resize_table_to_spins()

    # ---------------- Вспомогательные методы ----------------
    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            elif child_layout is not None:
                self.clear_layout(child_layout)

    def sync_spins_with_matrix(self):
        if self.matrix_B is None or self.matrix_B.size == 0:
            return

        n, m = self.matrix_B.shape

        self.n_spin.blockSignals(True)
        self.m_spin.blockSignals(True)

        self.n_spin.setValue(n)
        self.m_spin.setValue(m)

        self.n_spin.blockSignals(False)
        self.m_spin.blockSignals(False)

    def resize_table_to_spins(self):
        n = self.n_spin.value()
        m = self.m_spin.value()

        old_data = None
        if self.table_B.rowCount() > 0 and self.table_B.columnCount() > 0:
            old_rows = self.table_B.rowCount()
            old_cols = self.table_B.columnCount()
            old_data = np.zeros((old_rows, old_cols), dtype=float)

            for i in range(old_rows):
                for j in range(old_cols):
                    item = self.table_B.item(i, j)
                    try:
                        old_data[i, j] = float(item.text()) if item and item.text().strip() else 0.0
                    except Exception:
                        old_data[i, j] = 0.0

        self.table_B.setRowCount(n)
        self.table_B.setColumnCount(m)
        self.table_B.setVerticalHeaderLabels([f"Деталь {i+1}" for i in range(n)])
        self.table_B.setHorizontalHeaderLabels([f"Станок {j+1}" for j in range(m)])

        for i in range(n):
            for j in range(m):
                value = 0.0
                if old_data is not None and i < old_data.shape[0] and j < old_data.shape[1]:
                    value = old_data[i, j]

                item = QTableWidgetItem(str(int(value)) if float(value).is_integer() else str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_B.setItem(i, j, item)

    def format_matrix_for_report(self, matrix):
        lines = []
        for row in matrix:
            lines.append("[" + ", ".join(f"{float(x):.2f}" for x in row) + "]")
        return "\n".join(lines)

    def build_detailed_report(self, details):
        if details["method"] == "johnson_nmachines":
            lines = ["\nПОДРОБНЫЙ ОТЧЁТ: МЕТОД ДЖОНСОНА\n"]
            for step_num, step in enumerate(details["steps"], start=1):
                lines.append(f"Шаг {step_num}:")
                for c in step["candidates"]:
                    lines.append(
                        f"  Деталь {c['job']}: первый станок = {c['first_machine']}, "
                        f"последний станок = {c['last_machine']}"
                    )
                lines.append(
                    f"  Выбрана деталь {step['chosen_job']} "
                    f"(минимум = {step['chosen_value']}), "
                    f"помещена в {step['placed_to']} (позиция {step['position']})"
                )
                lines.append(f"  Текущая последовательность: {step['current_sequence']}")
                lines.append("")

            lines.append(f"Итоговая последовательность: {details['final_sequence']}")
            lines.append("Матрица окончаний C:")
            lines.append(self.format_matrix_for_report(details["completion_matrix"]))
            return "\n".join(lines)

        if details["method"] == "petrov_sokolitsin":
            lines = ["\nПОДРОБНЫЙ ОТЧЁТ: МЕТОД ПЕТРОВА–СОКОЛИЦИНА\n"]
            lines.append(f"Сумма по всем станкам, кроме первого: {details['sum_without_first']}")
            lines.append(f"Сумма по всем станкам, кроме последнего: {details['sum_without_last']}")
            lines.append(f"Разность: {details['diff']}\n")

            for idx, variant in enumerate(details["variants"], start=1):
                lines.append(f"Вариант {idx}: {variant['name']}")
                lines.append(f"  Последовательность: {variant['sequence']}")
                lines.append(f"  Длительность цикла: {variant['cycle']}")
                lines.append("  Матрица окончаний C:")
                lines.append(self.format_matrix_for_report(variant["completion_matrix"]))
                lines.append("")

            lines.append(f"Выбран лучший вариант: {details['best_variant']}")
            lines.append(f"Итоговая последовательность: {details['final_sequence']}")
            return "\n".join(lines)

        return ""

    # ---------------- Работа с данными ----------------
    def load_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать файл Excel", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            try:
                mat_float = load_excel(file_path)
                if mat_float.size == 0:
                    raise ValueError("Пустая матрица")

                self.matrix_B = np.array(mat_float, dtype=float, copy=True)
                self.sync_spins_with_matrix()
                self.update_table()

                n, m = self.matrix_B.shape
                self.result_text.setText(f"Матрица {n}x{m} загружена и готова к расчёту.")
                self.statusBar().showMessage("Excel-файл успешно загружен")
            except Exception as e:
                self.result_text.setText(f"Ошибка загрузки Excel: {e}")
                self.statusBar().showMessage("Ошибка загрузки Excel")

    def generate_random_matrix(self):
        n = self.n_spin.value()
        m = self.m_spin.value()
        min_time = self.min_time_spin.value()
        max_time = self.max_time_spin.value()

        if min_time > max_time:
            QMessageBox.warning(self, "Ошибка", "Минимальное время не может быть больше максимального.")
            return

        mat = generate_random_matrix_data(n, m, min_time=min_time, max_time=max_time)
        self.matrix_B = np.array(mat, dtype=float, copy=True)
        self.sync_spins_with_matrix()
        self.update_table()

        self.result_text.setText(
            f"Случайная матрица {n}x{m} создана.\nДиапазон значений: {min_time}..{max_time}"
        )
        self.statusBar().showMessage("Случайная матрица создана")

    def update_table(self):
        if self.matrix_B is None or self.matrix_B.size == 0:
            return

        n, m = self.matrix_B.shape
        self.table_B.setRowCount(n)
        self.table_B.setColumnCount(m)
        self.table_B.setVerticalHeaderLabels([f"Деталь {i+1}" for i in range(n)])
        self.table_B.setHorizontalHeaderLabels([f"Станок {j+1}" for j in range(m)])

        for i in range(n):
            for j in range(m):
                value = self.matrix_B[i, j]
                text = str(int(value)) if float(value).is_integer() else str(round(float(value), 2))
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_B.setItem(i, j, item)

    def update_matrix_from_table(self):
        n, m = self.table_B.rowCount(), self.table_B.columnCount()
        B_new = np.zeros((n, m), dtype=float)

        for i in range(n):
            for j in range(m):
                item = self.table_B.item(i, j)
                text = item.text().strip() if item else ""
                try:
                    B_new[i, j] = float(text)
                except Exception:
                    B_new[i, j] = 0.0
                    self.statusBar().showMessage(
                        f"В ячейке ({i+1},{j+1}) некорректное значение, заменено на 0"
                    )

        self.matrix_B = B_new
        self.sync_spins_with_matrix()
        self.update_table()
        self.statusBar().showMessage("Матрица обновлена из таблицы")

    # ---------------- Расчёт ----------------
    def calculate(self):
        if self.matrix_B is None or self.matrix_B.size == 0:
            self.result_text.setText("Матрица B не задана!")
            self.statusBar().showMessage("Нет матрицы для расчёта")
            return

        algo_name = self.algo_box.currentText()

        try:
            if algo_name == "Джонсон N станков":
                self.seq, _, _, details = johnson_nmachines(self.matrix_B)
            else:
                self.seq, _, _, details = petrov_sokolitsin(self.matrix_B)
            self.details = details
        except Exception as e:
            self.result_text.setText(f"Ошибка при расчёте последовательности: {e}")
            self.statusBar().showMessage("Ошибка алгоритма")
            return

        try:
            metrics = calculate_bi_metrics(self.matrix_B, self.seq)

            total_cycle = round(float(metrics["total_cycle"]), 2)
            load_percent = [round(float(x), 2) for x in metrics["load_percent"]]
            idle_times = [round(float(x), 2) for x in metrics["idle_times"]]
            wait_times = [round(float(x), 2) for x in metrics["wait_times"]]

            seq_display = [s + 1 for s in self.seq]
            report = f"Метод расчёта: {algo_name}\n"
            report += f"Оптимальная последовательность деталей: {seq_display}\n"
            report += f"Общая длительность цикла: {total_cycle}\n\n"

            report += "ПОКАЗАТЕЛИ:\n"
            report += f"Загрузка станков (%): {load_percent}\n"
            report += f"Простой станков: {idle_times}\n"
            report += f"Время ожидания деталей: {wait_times}\n"
            report += f"Минимальный простой: {min(idle_times)}, Максимальный простой: {max(idle_times)}\n"
            report += f"Суммарное ожидание деталей: {sum(wait_times)}\n"

            report += self.build_detailed_report(details)

            self.result_text.setText(report)

            self.render_gantt()
            self.render_bi()

            self.tabs.setCurrentWidget(self.report_tab)
            self.statusBar().showMessage("Расчёт успешно выполнен")

        except Exception as e:
            self.result_text.setText(f"Ошибка расчёта BI: {e}")
            self.statusBar().showMessage("Ошибка BI-аналитики")

    # ---------------- Отрисовка вкладок ----------------
    def render_gantt(self):
        self.clear_layout(self.gantt_container_layout)

        if self.matrix_B is None or self.seq is None:
            return

        color_mode = "by_job" if self.color_mode_box.currentText() == "По детали" else "random"
        brightness = self.brightness_spin.value() / 100.0
        show_duration = self.show_duration_cb.isChecked()
        scale_height = self.scale_height_cb.isChecked()
        row_gap = self.row_gap_spin.value()

        lbl1 = QLabel("Исходная диаграмма Ганта")
        lbl1.setStyleSheet("font-weight: 600; margin: 6px 0 4px 0;")
        self.gantt_container_layout.addWidget(lbl1)

        canvas_orig = plot_gantt_canvas(
            self.matrix_B,
            parent=self,
            show_duration=show_duration,
            color_mode=color_mode,
            brightness=brightness,
            scale_height=scale_height,
            row_gap=row_gap,
        )
        self.gantt_container_layout.addWidget(canvas_orig)

        lbl2 = QLabel("Диаграмма Ганта после оптимизации")
        lbl2.setStyleSheet("font-weight: 600; margin: 10px 0 4px 0;")
        self.gantt_container_layout.addWidget(lbl2)

        canvas_opt = plot_gantt_canvas(
            self.matrix_B,
            seq=self.seq,
            parent=self,
            show_duration=show_duration,
            color_mode=color_mode,
            brightness=brightness,
            scale_height=scale_height,
            row_gap=row_gap,
        )
        self.gantt_container_layout.addWidget(canvas_opt)
        self.gantt_container_layout.addStretch()

    def render_bi(self):
        self.clear_layout(self.bi_container_layout)

        if self.matrix_B is None or self.seq is None:
            return

        canvases, _ = create_bi_plots(self.matrix_B, self.seq)
        for canvas in canvases:
            self.bi_container_layout.addWidget(canvas)

        self.bi_container_layout.addStretch()
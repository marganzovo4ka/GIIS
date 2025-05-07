import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import numpy as np
from scipy.spatial import Delaunay, Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class VoronoiDelaunayApp:
    def __init__(self, master):
        self.master = master
        master.title("Триангуляция Делоне и Диаграмма Вороного")
        master.geometry("1000x700")

        # --- Фрейм для ввода и управления ---
        control_frame = ttk.Frame(master, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(control_frame, text="Введите точки (каждая точка на новой строке, X Y):").pack(pady=5)

        self.points_text = scrolledtext.ScrolledText(control_frame, width=30, height=15, wrap=tk.WORD)
        self.points_text.pack(pady=5)
        # Пример точек для быстрого старта
        self.points_text.insert(tk.INSERT, "10 10\n20 30\n50 15\n60 40\n30 50\n40 5\n70 70\n5 60")

        self.show_points_var = tk.BooleanVar(value=True)
        self.show_delaunay_var = tk.BooleanVar(value=True)
        self.show_voronoi_var = tk.BooleanVar(value=True)
        self.show_voronoi_vertices_var = tk.BooleanVar(value=False)  # Вершины Вороного по умолчанию выключены

        ttk.Checkbutton(control_frame, text="Показывать точки", variable=self.show_points_var,
                        command=self.plot_data).pack(anchor=tk.W)
        ttk.Checkbutton(control_frame, text="Показывать триангуляцию Делоне", variable=self.show_delaunay_var,
                        command=self.plot_data).pack(anchor=tk.W)
        ttk.Checkbutton(control_frame, text="Показывать диаграмму Вороного", variable=self.show_voronoi_var,
                        command=self.plot_data).pack(anchor=tk.W)
        ttk.Checkbutton(control_frame, text="Показывать вершины Вороного", variable=self.show_voronoi_vertices_var,
                        command=self.plot_data).pack(anchor=tk.W)

        generate_button = ttk.Button(control_frame, text="Сгенерировать/Обновить", command=self.generate_diagrams)
        generate_button.pack(pady=10)

        clear_button = ttk.Button(control_frame, text="Очистить всё", command=self.clear_all)
        clear_button.pack(pady=5)

        ttk.Label(control_frame, text="Состояние:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.status_label = ttk.Label(control_frame, text="Готово к работе.", wraplength=200)
        self.status_label.pack(pady=5)

        # --- Фрейм для графика ---
        plot_frame = ttk.Frame(master)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Добавляем панель инструментов Matplotlib
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Сохраняем данные для перерисовки
        self.points = None
        self.delaunay_tri = None
        self.voronoi_diag = None

        # Первичная отрисовка (пустая)
        self.plot_data()

    def parse_points(self):
        text_content = self.points_text.get("1.0", tk.END).strip()
        if not text_content:
            return None

        points_list = []
        lines = text_content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.split()
                if len(parts) != 2:
                    parts = line.split(',')  # Попробуем запятую как разделитель
                    if len(parts) != 2:
                        raise ValueError(f"Неверный формат в строке {i + 1}: '{line}'. Ожидается 'X Y'.")
                x = float(parts[0].strip())
                y = float(parts[1].strip())
                points_list.append([x, y])
            except ValueError as e:
                messagebox.showerror("Ошибка ввода", f"Ошибка в строке {i + 1}: {line}\n{e}")
                return None

        if not points_list:
            messagebox.showwarning("Внимание", "Точки не введены.")
            return None

        if len(points_list) < 3:  # Для Делоне нужно хотя бы 3 точки (не коллинеарные)
            messagebox.showwarning("Внимание", "Нужно как минимум 3 точки для триангуляции.")
            # Можно разрешить меньше для диаграммы Вороного, но для Делоне это минимум
            if len(points_list) < 1: return None  # Совсем пусто

        return np.array(points_list)

    def generate_diagrams(self):
        parsed_points = self.parse_points()
        if parsed_points is None:
            self.status_label.config(text="Ошибка: Не удалось обработать точки.")
            # Если точек нет, очищаем данные
            if not self.points_text.get("1.0", tk.END).strip():
                self.points = None
                self.delaunay_tri = None
                self.voronoi_diag = None
                self.plot_data()
            return

        self.points = parsed_points
        self.status_label.config(text=f"Загружено {len(self.points)} точек.")

        try:
            if len(self.points) >= 3:  # Триангуляция Делоне требует >= 3 точек (не коллинеарных)
                self.delaunay_tri = Delaunay(self.points)
                self.status_label.config(text=self.status_label.cget("text") + "\nТриангуляция Делоне построена.")
            else:
                self.delaunay_tri = None
                self.status_label.config(text=self.status_label.cget("text") + "\nНедостаточно точек для Делоне.")

            if len(self.points) >= 1:  # Диаграмма Вороного может быть построена и для одной точки
                # но scipy.spatial.Voronoi требует >= 2 точек для нетривиального результата.
                # Более того, для корректной работы voronoi_plot_2d нужно >= 4 точек
                # если мы хотим избежать QhullError для коллинеарных или совпадающих точек.
                # scipy.spatial.Voronoi сам по себе может выдать QhullError, если точки "плохие"
                if len(self.points) >= 2:  # SciPy Voronoi требует как минимум 2 точки
                    self.voronoi_diag = Voronoi(self.points, qhull_options="Qbb Qc Qz")  # Опции для устойчивости
                    self.status_label.config(text=self.status_label.cget("text") + "\nДиаграмма Вороного построена.")
                else:
                    self.voronoi_diag = None
                    self.status_label.config(
                        text=self.status_label.cget("text") + "\nНедостаточно точек для Вороного (нужно >= 2).")
            else:
                self.voronoi_diag = None

        except Exception as e:  # Например, scipy.spatial.qhull.QhullError если все точки коллинеарны
            messagebox.showerror("Ошибка вычислений", f"Не удалось построить диаграммы: {e}")
            self.status_label.config(text=f"Ошибка вычислений: {e}")
            # Не сбрасываем points, чтобы пользователь мог их исправить
            self.delaunay_tri = None
            self.voronoi_diag = None

        self.plot_data()

    def plot_data(self):
        self.ax.clear()

        if self.points is not None:
            # Установка пределов для лучшего отображения Вороного
            # (voronoi_plot_2d это делает, но лучше сделать это явно, если он не вызывается)
            if self.voronoi_diag and self.show_voronoi_var.get():
                # Делаем это до voronoi_plot_2d, чтобы он не переопределял
                min_coord = np.min(self.points, axis=0)
                max_coord = np.max(self.points, axis=0)
                range_coord = max_coord - min_coord
                # Добавляем отступы, чтобы бесконечные ребра Вороного были видны
                padding_factor = 0.5  # Можно настроить
                self.ax.set_xlim(min_coord[0] - range_coord[0] * padding_factor,
                                 max_coord[0] + range_coord[0] * padding_factor)
                self.ax.set_ylim(min_coord[1] - range_coord[1] * padding_factor,
                                 max_coord[1] + range_coord[1] * padding_factor)

            if self.show_voronoi_var.get() and self.voronoi_diag:
                try:
                    # voronoi_plot_2d может быть чувствителен к очень маленькому числу точек
                    # или коллинеарным точкам. Он пытается рисовать бесконечные регионы.
                    if len(self.points) >= 2:  # voronoi_plot_2d может падать для 2-3 точек.
                        # Для устойчивости лучше >=4 не коллинеарных.
                        voronoi_plot_2d(self.voronoi_diag, self.ax,
                                        show_vertices=self.show_voronoi_vertices_var.get(),
                                        line_colors='orange', line_width=2, line_alpha=0.8,
                                        point_size=5 if self.show_voronoi_vertices_var.get() else 0)
                        self.ax.plot(self.voronoi_diag.points[:, 0], self.voronoi_diag.points[:, 1], 'o', color='blue',
                                     markersize=1,
                                     alpha=0)  # скрыть точки из voronoi_plot_2d, если show_points_var=False
                    else:
                        # Ручная отрисовка для малого числа точек (если нужно)
                        # или просто пропускаем
                        pass
                except Exception as e:
                    print(f"Ошибка при отрисовке Вороного: {e}")  # Лог в консоль
                    self.status_label.config(text=self.status_label.cget("text") + f"\nОшибка отрисовки Вороного: {e}")

            if self.show_delaunay_var.get() and self.delaunay_tri:
                self.ax.triplot(self.points[:, 0], self.points[:, 1], self.delaunay_tri.simplices, color='green',
                                lw=0.8)

            if self.show_points_var.get():
                self.ax.plot(self.points[:, 0], self.points[:, 1], 'o', color='red', markersize=5)

        self.ax.set_xlabel("X координата")
        self.ax.set_ylabel("Y координата")
        self.ax.set_title("Триангуляция Делоне и Диаграмма Вороного")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.set_aspect('equal', adjustable='box')  # Важно для правильного восприятия геометрии

        self.canvas.draw()

    def clear_all(self):
        self.points_text.delete("1.0", tk.END)
        self.points = None
        self.delaunay_tri = None
        self.voronoi_diag = None
        self.status_label.config(text="Все очищено.")
        self.plot_data()


if __name__ == '__main__':
    root = tk.Tk()
    app = VoronoiDelaunayApp(root)
    root.mainloop()
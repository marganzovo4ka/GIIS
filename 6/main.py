import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import math
import time
import traceback  # Add this at the top of your file



# --- Helper Geometric Functions ---
def orientation(p, q, r):
    if p is None or q is None or r is None: return 0
    val = (q[1] - p[1]) * (r[0] - q[0]) - \
          (q[0] - p[0]) * (r[1] - q[1])
    if val == 0: return 0
    return 1 if val > 0 else 2


def dist_sq(p1, p2):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


def on_segment(p, q, r):
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))


def segments_intersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)
    if o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        if o1 != o2 and o3 != o4:
            return True
    if o1 == 0 and on_segment(p1, p2, q1): return True
    if o2 == 0 and on_segment(p1, q2, q1): return True
    if o3 == 0 and on_segment(p2, p1, q2): return True
    if o4 == 0 and on_segment(p2, q1, q2): return True
    return False


def get_intersection_point(p1, q1, p2, q2):
    x1, y1 = p1;
    x2, y2 = q1;
    x3, y3 = p2;
    x4, y4 = q2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0: return None
    t_num = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
    u_num = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3))
    t = t_num / den;
    u = u_num / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class PolygonEditor:
    def __init__(self, master):
        self.master = master
        master.title("Графический Редактор Полигонов с Заполнением")

        self.canvas_width = 800
        self.canvas_height = 600

        self.BG_COLOR_HEX = "#FFFFFF"
        self.FILL_COLOR_HEX = "#00FFFF"
        self.SEED_POINT_COLOR_HEX = "#FF00FF"
        self.BG_COLOR_RGB = hex_to_rgb(self.BG_COLOR_HEX)
        self.FILL_COLOR_RGB = hex_to_rgb(self.FILL_COLOR_HEX)

        self.current_polygon_points = []
        self.polygons = []
        self.active_polygon_index = -1

        self.current_line_points = []
        self.lines = []

        self.hull_points = []  # Should this be used for something else?
        self.drawn_hull = []

        self.mode = "idle"
        self.fill_algorithm_var = tk.StringVar(value="scanline_et_ael")
        self.debug_mode_var = tk.BooleanVar(value=False)
        self.debug_generator = None
        self.debug_paused = False
        self.debug_info_var = tk.StringVar(value="Отладка: нет данных")
        self.seed_point = None

        self.fill_photo_image = tk.PhotoImage(width=self.canvas_width, height=self.canvas_height)
        self.fill_canvas_item_id = None

        self.menubar = tk.Menu(master)

        filemenu = tk.Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Очистить всё", command=self.clear_all)
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=master.quit)
        self.menubar.add_cascade(label="Файл", menu=filemenu)

        self.polygon_menu = tk.Menu(self.menubar, tearoff=0)
        self.polygon_menu.add_command(label="Завершить полигон", command=self.finish_polygon)
        self.polygon_menu.add_command(label="Проверить на выпуклость", command=self.check_convexity_selected)
        # **** THIS IS WHERE THE MISSING METHODS ARE CALLED ****
        self.polygon_menu.add_command(label="Показать внутренние нормали", command=self.show_normals_selected)
        self.polygon_menu.add_separator()
        self.polygon_menu.add_command(label="Обход Грэхема", command=lambda: self.calculate_convex_hull("graham"))
        self.polygon_menu.add_command(label="Метод Джарвиса", command=lambda: self.calculate_convex_hull("jarvis"))
        self.menubar.add_cascade(label="Полигон", menu=self.polygon_menu)

        actionsmenu = tk.Menu(self.menubar, tearoff=0)
        actionsmenu.add_command(label="Пересечение отрезка со стороной полигона",
                                command=self.set_mode_segment_polygon_intersection)
        actionsmenu.add_command(label="Принадлежность точки полигону", command=self.set_mode_point_in_polygon)
        self.menubar.add_cascade(label="Действия", menu=actionsmenu)

        fillmenu = tk.Menu(self.menubar, tearoff=0)
        fillmenu.add_radiobutton(label="Развертка (ET/AEL)", variable=self.fill_algorithm_var, value="scanline_et_ael")
        fillmenu.add_radiobutton(label="Затравка (простая)", variable=self.fill_algorithm_var, value="seed_fill_simple")
        fillmenu.add_radiobutton(label="Затравка (построчная)", variable=self.fill_algorithm_var,
                                 value="seed_fill_scanline")
        fillmenu.add_separator()
        fillmenu.add_command(label="Заполнить активный полигон", command=self.start_fill_active_polygon)
        fillmenu.add_command(label="Очистить заливку", command=self.clear_current_fill_and_redraw)
        self.menubar.add_cascade(label="Заполнение", menu=fillmenu)

        master.config(menu=self.menubar)

        top_frame = ttk.Frame(master)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.toolbar = ttk.Frame(top_frame, padding="2")
        self.toolbar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_draw_poly = ttk.Button(self.toolbar, text="Рисовать полигон", command=self.set_mode_draw_polygon)
        btn_draw_poly.pack(side=tk.LEFT, padx=2, pady=2)

        self.poly_build_var = tk.StringVar()
        self.poly_build_options = {
            "Обход Грэхема": lambda: self.calculate_convex_hull("graham"),
            "Метод Джарвиса": lambda: self.calculate_convex_hull("jarvis"),
            "Завершить полигон": self.finish_polygon,  # Added from previous logic
            "Проверить выпуклость": self.check_convexity_selected,  # Added
            "Показать нормали": self.show_normals_selected  # Added
        }
        poly_build_om = ttk.OptionMenu(self.toolbar, self.poly_build_var, "Построение полигонов",
                                       *self.poly_build_options.keys(), command=self.on_poly_build_select)
        poly_build_om.pack(side=tk.LEFT, padx=2, pady=2)

        self.fill_algo_toolbar_var = tk.StringVar()
        fill_algo_options_map = {
            "Развертка ET/AEL": "scanline_et_ael",
            "Затравка (простая)": "seed_fill_simple",
            "Затравка (построчная)": "seed_fill_scanline"
        }

        def on_fill_algo_toolbar_select(display_name):
            self.fill_algorithm_var.set(fill_algo_options_map[display_name])
            self.fill_algo_toolbar_var.set("Алгоритм заполнения")

        fill_algo_om = ttk.OptionMenu(self.toolbar, self.fill_algo_toolbar_var, "Алгоритм заполнения",
                                      *fill_algo_options_map.keys(), command=on_fill_algo_toolbar_select)
        fill_algo_om.pack(side=tk.LEFT, padx=2, pady=2)

        btn_fill_poly = ttk.Button(self.toolbar, text="Заполнить", command=self.start_fill_active_polygon)
        btn_fill_poly.pack(side=tk.LEFT, padx=2, pady=2)

        # Added other buttons from previous logic to toolbar for consistency
        btn_draw_line = ttk.Button(self.toolbar, text="Рисовать линию", command=self.set_mode_draw_line)
        btn_draw_line.pack(side=tk.LEFT, padx=2, pady=2)

        btn_intersect = ttk.Button(self.toolbar, text="Пересечение линии/полигона",
                                   command=self.set_mode_segment_polygon_intersection)
        btn_intersect.pack(side=tk.LEFT, padx=2, pady=2)

        btn_point_in_poly = ttk.Button(self.toolbar, text="Точка в полигоне?", command=self.set_mode_point_in_polygon)
        btn_point_in_poly.pack(side=tk.LEFT, padx=2, pady=2)

        btn_clear = ttk.Button(self.toolbar, text="Очистить все", command=self.clear_all)
        btn_clear.pack(side=tk.LEFT, padx=2, pady=2)

        debug_frame = ttk.LabelFrame(top_frame, text="Отладка Заполнения", padding="5")
        debug_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        debug_cb = ttk.Checkbutton(debug_frame, text="Включить", variable=self.debug_mode_var,
                                   command=self.toggle_debug_mode)
        debug_cb.pack(side=tk.TOP, anchor=tk.W)

        self.btn_debug_next = ttk.Button(debug_frame, text="След. шаг", command=self.debug_next_step, state=tk.DISABLED)
        self.btn_debug_next.pack(side=tk.TOP, fill=tk.X, pady=2)

        self.btn_debug_run = ttk.Button(debug_frame, text="Запустить (отладка)", command=self.debug_run_to_completion,
                                        state=tk.DISABLED)
        self.btn_debug_run.pack(side=tk.TOP, fill=tk.X, pady=2)

        self.btn_debug_reset = ttk.Button(debug_frame, text="Сбросить отладку", command=self.reset_debug,
                                          state=tk.DISABLED)
        self.btn_debug_reset.pack(side=tk.TOP, fill=tk.X, pady=2)

        self.canvas = tk.Canvas(master, bg="white", width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.fill_canvas_item_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.fill_photo_image)
        self.clear_fill_image()  # Initialize with background color

        status_debug_frame = ttk.Frame(master)
        status_debug_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar()
        self.status_var.set("Готов. Выберите действие.")
        self.statusbar = ttk.Label(status_debug_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.debug_info_label = ttk.Label(status_debug_frame, textvariable=self.debug_info_var, relief=tk.SUNKEN,
                                          anchor=tk.W, width=40)
        self.debug_info_label.pack(side=tk.RIGHT, fill=tk.X)

        self.select_last_polygon_as_active()
        self.redraw_all()

    def clear_fill_image(self):
        self.fill_photo_image.put(self.BG_COLOR_HEX, to=(0, 0, self.canvas_width, self.canvas_height))
        if self.fill_canvas_item_id and self.canvas.winfo_exists():  # Check if canvas item exists
            self.canvas.itemconfig(self.fill_canvas_item_id, image=self.fill_photo_image)

    def on_poly_build_select(self, selection):
        if selection in self.poly_build_options:
            self.poly_build_options[selection]()
        self.poly_build_var.set("Построение полигонов")

    def clear_canvas_objects(self, tag_prefix=""):
        items_to_delete = []
        # Check if canvas is valid before finding items
        if not self.canvas.winfo_exists(): return

        for item_id in self.canvas.find_all():
            tags = self.canvas.gettags(item_id)
            if item_id == self.fill_canvas_item_id:
                continue
            if not tag_prefix:
                if item_id != self.fill_canvas_item_id: items_to_delete.append(item_id)
            else:
                if any(tag.startswith(tag_prefix) for tag in tags):
                    items_to_delete.append(item_id)
        for item_id in items_to_delete:
            if self.canvas.winfo_exists():  # Check again before deleting
                try:
                    self.canvas.delete(item_id)
                except tk.TclError:  # Item might have been deleted by other means
                    pass

    def redraw_all(self):
        if not self.canvas.winfo_exists(): return  # Don't redraw if canvas is gone

        self.clear_canvas_objects("polygon_")
        self.clear_canvas_objects("current_")
        self.clear_canvas_objects("line_")
        self.clear_canvas_objects("convex_hull_")
        self.clear_canvas_objects("temp_")
        self.clear_canvas_objects("seed_point_marker")

        self.canvas.itemconfig(self.fill_canvas_item_id, image=self.fill_photo_image)
        self.canvas.tag_lower(self.fill_canvas_item_id)

        for i, poly in enumerate(self.polygons):
            if len(poly) > 1:
                flat_poly = [coord for point in poly for coord in point]
                outline_fill_color = ""
                if i == self.active_polygon_index:
                    line_color = "blue"
                    line_width = 3
                else:
                    line_color = "black"
                    line_width = 2
                self.canvas.create_polygon(flat_poly, outline=line_color, fill=outline_fill_color, width=line_width,
                                           tags=(f"polygon_{i}", "polygon"))

        if self.current_polygon_points:
            for p_idx, p in enumerate(self.current_polygon_points):
                self.canvas.create_oval(p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3, fill="red",
                                        tags=("current_point", f"current_vertex_{p_idx}"))
            if len(self.current_polygon_points) > 1:
                for i in range(len(self.current_polygon_points) - 1):
                    p1, p2 = self.current_polygon_points[i], self.current_polygon_points[i + 1]
                    self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="red", dash=(4, 2),
                                            tags="current_poly_segment")

        for i, line_segment in enumerate(self.lines):
            p1, p2 = line_segment
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="green", width=2, tags=(f"line_{i}", "line"))

        if self.drawn_hull and len(self.drawn_hull) > 1:
            flat_hull = [coord for point in self.drawn_hull for coord in point]
            self.canvas.create_polygon(flat_hull, outline="purple", fill="", width=3, dash=(5, 5),
                                       tags="convex_hull_shape")

        if self.seed_point and (self.mode == "select_seed_point" or self.debug_generator):
            x, y = self.seed_point
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=self.SEED_POINT_COLOR_HEX, outline="black",
                                    tags="seed_point_marker")

        self.status_var.set(
            f"Режим: {self.mode}. Актив. полигон: {'#' + str(self.active_polygon_index + 1) if self.active_polygon_index != -1 else 'Нет'}. Заливка: {self.fill_algorithm_var.get()}")

    def on_canvas_click(self, event):
        x, y = event.x, event.y
        point = (x, y)

        if self.mode == "select_seed_point":
            if self.active_polygon_index != -1 and self.polygons:
                active_poly_vertices = self.polygons[self.active_polygon_index]
                if self.is_point_in_polygon(point, active_poly_vertices):
                    self.seed_point = point
                    self.status_var.set(f"Точка затравки: {self.seed_point}. Запускаем заполнение...")
                    self.mode = "idle"
                    self.redraw_all()
                    self.execute_fill_algorithm(active_poly_vertices, self.seed_point)
                else:
                    messagebox.showwarning("Затравка", "Точка затравки должна быть внутри активного полигона.")
            else:
                messagebox.showerror("Ошибка", "Сначала выберите активный полигон.")
            return

        if self.mode in ["idle", "check_convexity", "show_normals", "segment_polygon_intersection_poly_select",
                         "point_in_polygon_test_poly_select"]:
            clicked_on_polygon_index = -1
            if self.polygons:  # Only try to select if polygons exist
                for i, poly_verts in enumerate(self.polygons):
                    if self.is_point_in_polygon(point, poly_verts):
                        clicked_on_polygon_index = i
                        break

            if clicked_on_polygon_index != -1:
                self.active_polygon_index = clicked_on_polygon_index
                self.status_var.set(f"Выбран полигон #{self.active_polygon_index + 1}")
                self.redraw_all()

                # Handle sub-modes for actions
                if self.mode == "segment_polygon_intersection_poly_select":
                    self.status_var.set(f"Полигон #{self.active_polygon_index + 1} выбран. Нарисуйте отрезок.")
                    self.set_mode_draw_line(for_intersection=True)
                    return
                if self.mode == "point_in_polygon_test_poly_select":
                    self.status_var.set(f"Полигон #{self.active_polygon_index + 1} выбран. Кликните точку.")
                    self.mode = "point_in_polygon_test_point_select"
                    return
            # else: # Clicked outside any polygon
            # self.active_polygon_index = -1 # Optional: Deselect on click outside
            # self.redraw_all()

        if self.mode == "draw_polygon":
            self.current_polygon_points.append(point)
            self.status_var.set(
                f"Добавлена точка {point}. Всего: {len(self.current_polygon_points)}. ПКМ для завершения.")
        elif self.mode == "draw_line" or self.mode == "draw_line_for_intersection":
            self.current_line_points.append(point)
            if len(self.current_line_points) == 2:
                if self.mode == "draw_line_for_intersection":
                    self.perform_segment_polygon_intersection(self.current_line_points)
                    # self.current_line_points = [] # Cleared in perform_... or set_mode_idle
                else:
                    self.lines.append(tuple(self.current_line_points))
                self.current_line_points = []
                self.set_mode_idle()
            else:
                self.status_var.set(f"Первая точка отрезка: {point}.")
        elif self.mode == "point_in_polygon_test_point_select":
            if self.active_polygon_index != -1 and self.polygons:
                polygon = self.polygons[self.active_polygon_index]
                is_inside = self.is_point_in_polygon(point, polygon)
                self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="orange", outline="black",
                                        tags="temp_test_point")
                msg = f"Точка {point} {'ВНУТРИ' if is_inside else 'СНАРУЖИ'} полигона #{self.active_polygon_index + 1}."
                messagebox.showinfo("Результат проверки точки", msg)
                self.status_var.set(msg + " Выберите действие.")
                self.set_mode_idle()
            else:
                messagebox.showerror("Ошибка", "Сначала выберите полигон.")
                self.set_mode_point_in_polygon()

        self.redraw_all()

    def on_canvas_right_click(self, event):
        if self.mode == "draw_polygon":
            self.finish_polygon()

    def set_mode_idle(self):
        self.mode = "idle"
        self.status_var.set("Готов. Выберите действие или кликните на полигон.")
        self.redraw_all()

    def set_mode_draw_polygon(self):
        self.reset_debug()
        self.mode = "draw_polygon"
        self.current_polygon_points = []
        self.drawn_hull = []
        self.clear_canvas_objects("temp_")
        self.status_var.set("Режим: Рисование полигона. Кликайте. ПКМ для завершения.")
        self.redraw_all()

    def set_mode_draw_line(self, for_intersection=False):
        self.mode = "draw_line_for_intersection" if for_intersection else "draw_line"
        self.current_line_points = []
        self.drawn_hull = []
        self.clear_canvas_objects("temp_")
        status_msg = "Режим: Рисование линии для пересечения. " if for_intersection else "Режим: Рисование линии. "
        self.status_var.set(status_msg + "Кликните для первой точки.")
        self.redraw_all()

    def set_mode_point_in_polygon(self):
        self.clear_canvas_objects("temp_")
        if not self.polygons:
            messagebox.showinfo("Информация", "Сначала нарисуйте полигон.")
            self.set_mode_idle()
            return
        self.mode = "point_in_polygon_test_poly_select"
        self.status_var.set("Выберите полигон для проверки, кликнув по нему.")
        self.redraw_all()

    def set_mode_segment_polygon_intersection(self):
        self.clear_canvas_objects("temp_")
        if not self.polygons:
            messagebox.showinfo("Информация", "Сначала нарисуйте полигон.")
            self.set_mode_idle()
            return
        self.mode = "segment_polygon_intersection_poly_select"
        self.status_var.set("Выберите полигон для проверки пересечения, кликнув по нему.")
        self.redraw_all()

    def finish_polygon(self):
        if self.mode == "draw_polygon" and len(self.current_polygon_points) >= 3:
            self.polygons.append(list(self.current_polygon_points))
            self.active_polygon_index = len(self.polygons) - 1
            self.current_polygon_points = []
            self.status_var.set(f"Полигон #{self.active_polygon_index + 1} создан.")
            self.set_mode_idle()
        elif self.mode == "draw_polygon":
            messagebox.showwarning("Рисование полигона", "Нужно как минимум 3 точки.")
        self.redraw_all()

    def select_last_polygon_as_active(self):
        if self.polygons:
            self.active_polygon_index = len(self.polygons) - 1
        else:
            self.active_polygon_index = -1

    def is_point_in_polygon(self, point, polygon_points):
        if not polygon_points or len(polygon_points) < 3: return False
        n = len(polygon_points)
        x, y = point[0], point[1]
        inside = False
        p1x, p1y = polygon_points[0]
        for i in range(n + 1):
            p2x, p2y = polygon_points[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def clear_current_fill_and_redraw(self):
        self.clear_fill_image()
        self.reset_debug()
        self.redraw_all()
        self.status_var.set("Заливка очищена.")

    def start_fill_active_polygon(self):
        self.reset_debug()
        if self.active_polygon_index == -1 or not self.polygons:
            messagebox.showerror("Ошибка заполнения", "Нет активного полигона.")
            return

        active_poly_vertices = self.polygons[self.active_polygon_index]
        if len(active_poly_vertices) < 3:
            messagebox.showerror("Ошибка заполнения", "Активный полигон < 3 вершин.")
            return

        algo = self.fill_algorithm_var.get()
        self.clear_fill_image()

        if algo == "scanline_et_ael":
            self.execute_fill_algorithm(active_poly_vertices)
        elif algo in ["seed_fill_simple", "seed_fill_scanline"]:
            self.mode = "select_seed_point"
            self.seed_point = None
            self.status_var.set(
                f"Выберите точку затравки внутри полигона #{self.active_polygon_index + 1} для '{algo}'.")
            self.redraw_all()
        else:
            messagebox.showerror("Ошибка", f"Неизвестный алгоритм: {algo}")

    def execute_fill_algorithm(self, polygon_vertices, seed_point=None):
        algo = self.fill_algorithm_var.get()
        self.debug_info_var.set(f"Запуск: {algo}")

        try:
            if algo == "scanline_et_ael":
                self.debug_generator = self._scanline_fill_et_ael_generator(polygon_vertices)
            elif algo == "seed_fill_simple":
                if not seed_point:
                    messagebox.showerror("Ошибка", "Точка затравки не указана для seed_fill_simple.")
                    return
                self.debug_generator = self._seed_fill_simple_generator(polygon_vertices, seed_point)
            elif algo == "seed_fill_scanline":
                if not seed_point:
                    messagebox.showerror("Ошибка", "Точка затравки не указана для seed_fill_scanline.")
                    return
                self.debug_generator = self._seed_fill_scanline_generator(polygon_vertices, seed_point)
            else:
                return

            if self.debug_mode_var.get():
                self.debug_paused = True
                self.enable_debug_buttons()
                self.status_var.set(f"Отладка '{algo}'. Нажмите 'След. шаг'.")
                self.debug_next_step()
            else:
                if self.debug_generator:
                    for _ in self.debug_generator:
                        pass
                    self.debug_generator = None
                self.redraw_all()
                self.status_var.set(f"Полигон заполнен ({algo}).")

        except Exception as e:
            messagebox.showerror("Ошибка выполнения заливки",
                                 f"Произошла ошибка: {str(e)}\nTraceback: {traceback.format_exc()}")  # Added traceback
            self.reset_debug()

    def toggle_debug_mode(self):
        if not self.debug_mode_var.get():
            self.reset_debug()
            self.status_var.set("Отладочный режим выключен.")
        else:
            self.status_var.set("Отладочный режим включен.")

    def enable_debug_buttons(self, enabled=True):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_debug_next.config(state=state)
        self.btn_debug_run.config(state=state)
        self.btn_debug_reset.config(state=state)

    def reset_debug(self):
        self.debug_generator = None
        self.debug_paused = False
        self.enable_debug_buttons(False)
        self.debug_info_var.set("Отладка: нет данных")
        self.seed_point = None
        # self.clear_fill_image() # Don't clear fill on reset, user might want to see final state
        self.redraw_all()

    def debug_next_step(self):
        if self.debug_generator:
            try:
                status = next(self.debug_generator)
                self.debug_info_var.set(str(status) if status else "Шаг выполнен.")
                if self.canvas.winfo_exists():
                    self.canvas.itemconfig(self.fill_canvas_item_id, image=self.fill_photo_image)
                    self.master.update_idletasks()
            except StopIteration:
                self.debug_info_var.set("Отладка завершена.")
                self.debug_generator = None
                self.enable_debug_buttons(False)
                self.btn_debug_reset.config(state=tk.NORMAL)  # Keep reset enabled
                self.redraw_all()
            except Exception as e:
                messagebox.showerror("Ошибка отладки", f"Ошибка на шаге: {e}\n{traceback.format_exc()}")
                self.reset_debug()

    def debug_run_to_completion(self):
        if self.debug_generator:
            self.debug_paused = False
            current_next_state = self.btn_debug_next['state']
            current_run_state = self.btn_debug_run['state']
            self.btn_debug_next.config(state=tk.DISABLED)
            self.btn_debug_run.config(state=tk.DISABLED)

            try:
                while True:
                    status = next(self.debug_generator)
                    self.debug_info_var.set(str(status) if status else "Выполнение...")
                    if self.canvas.winfo_exists():
                        self.canvas.itemconfig(self.fill_canvas_item_id, image=self.fill_photo_image)
                        self.master.update_idletasks()
            except StopIteration:
                self.debug_info_var.set("Отладка завершена (запуск до конца).")
                self.debug_generator = None
                self.enable_debug_buttons(False)
                self.btn_debug_reset.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Ошибка отладки", f"Ошибка при запуске: {e}\n{traceback.format_exc()}")
                self.reset_debug()
            finally:
                if self.debug_generator:
                    self.btn_debug_next.config(state=current_next_state)
                    self.btn_debug_run.config(state=current_run_state)
                self.redraw_all()

    # --- Fill Algorithm Implementations (Generators) ---
    def _scanline_fill_et_ael_generator(self, polygon_vertices):
        if not polygon_vertices or len(polygon_vertices) < 3:
            yield "Ошибка: недостаточно вершин"
            return

        # Ensure integer coordinates for scanline algorithm if not already
        poly_int = [(int(v[0]), int(v[1])) for v in polygon_vertices]

        min_y = int(min(v[1] for v in poly_int))
        max_y = int(max(v[1] for v in poly_int))

        if min_y > self.canvas_height or max_y < 0:  # Polygon entirely off-screen
            yield "Полигон вне холста (Y)"
            return

        edge_table = [[] for _ in range(max_y - min_y + 1)]

        for i in range(len(poly_int)):
            p1 = poly_int[i]
            p2 = poly_int[(i + 1) % len(poly_int)]

            y1_orig, y2_orig = p1[1], p2[1]
            x1_orig, x2_orig = p1[0], p2[0]

            if y1_orig == y2_orig: continue

            y1, y2 = min(y1_orig, y2_orig), max(y1_orig, y2_orig)
            x1 = x1_orig if y1_orig < y2_orig else x2_orig
            # x2 corresponding to y2 will be handled by ymax

            inverse_slope = (x2_orig - x1_orig) / (y2_orig - y1_orig) if (y2_orig - y1_orig) != 0 else float(
                'inf')  # Use inf for vertical

            et_index = y1 - min_y
            if 0 <= et_index < len(edge_table):
                edge_table[et_index].append([y2, x1, inverse_slope])  # [ymax, x_at_ymin, 1/m]

        yield f"ET построен. min_y={min_y}, max_y={max_y}. Скан-линий: {max_y - min_y + 1}"

        active_edge_list = []
        for y_scan_abs in range(min_y, max_y + 1):
            if not (0 <= y_scan_abs < self.canvas_height): continue  # Clip scanline to canvas

            et_current_y_index = y_scan_abs - min_y

            if 0 <= et_current_y_index < len(edge_table):
                for edge_data in edge_table[et_current_y_index]:
                    active_edge_list.append(list(edge_data))

            active_edge_list.sort(key=lambda edge: edge[1])  # Sort by x_current

            # For debugging: Show AEL structure
            ael_debug_str = "AEL: " + ", ".join(
                f"[yMax:{int(e[0])}, xCur:{e[1]:.1f}, 1/m:{e[2]:.2f}]" for e in active_edge_list)
            yield f"y={y_scan_abs}. {ael_debug_str}"

            for i in range(0, len(active_edge_list) - 1, 2):
                x_start_float = active_edge_list[i][1]
                x_end_float = active_edge_list[i + 1][1]

                # Pixel centers: use ceil for start, floor for end
                x_start_pixel = math.ceil(x_start_float)
                x_end_pixel = math.floor(x_end_float)  # Inclusive if x_end_float is integer
                # Or x_end_pixel = math.floor(x_end_float - epsilon) for strict <

                # Ensure correct span, especially for thin parts
                if x_start_pixel > x_end_pixel: continue  # No pixels to fill in this span

                for x_pixel in range(int(x_start_pixel), int(x_end_pixel) + 1):  # +1 for inclusive end
                    if 0 <= x_pixel < self.canvas_width:  # Clip to canvas width
                        self.fill_photo_image.put(self.FILL_COLOR_HEX, (x_pixel, y_scan_abs))

            if active_edge_list:
                # yield f"y={y_scan_abs}: Заполнены промежутки." # Can be too verbose
                if self.debug_paused: self.canvas.itemconfig(self.fill_canvas_item_id, image=self.fill_photo_image)

            active_edge_list = [edge for edge in active_edge_list if edge[0] > y_scan_abs]  # ymax > current_y

            for edge in active_edge_list:
                if edge[2] != float('inf'):  # Not vertical
                    edge[1] += edge[2]

            if self.debug_paused and (y_scan_abs - min_y) % 5 == 0:
                self.master.update()

        yield "Заполнение (Развертка ET/AEL) завершено."

    def _seed_fill_simple_generator(self, polygon_vertices, seed_point_tuple):
        seed_x, seed_y = int(seed_point_tuple[0]), int(seed_point_tuple[1])

        if not (0 <= seed_x < self.canvas_width and 0 <= seed_y < self.canvas_height):
            yield "Ошибка: Точка затравки вне холста."
            return
        if not self.is_point_in_polygon((seed_x + 0.5, seed_y + 0.5), polygon_vertices):  # Check center
            yield "Ошибка: Точка затравки вне полигона (проверка по центру)."
            return

        q = [(seed_x, seed_y)]

        try:
            if self.fill_photo_image.get(seed_x, seed_y) == self.FILL_COLOR_RGB:
                yield "Затравка уже заполнена."
                return
        except tk.TclError:
            yield "Ошибка: Не удалось получить цвет точки затравки."
            return

        self.fill_photo_image.put(self.FILL_COLOR_HEX, (seed_x, seed_y))
        yield f"Затравка ({seed_x},{seed_y}). Стек: {len(q)}"

        count = 0
        visited_in_algo = set([(seed_x, seed_y)])  # Keep track of pixels pushed to queue to avoid re-adding

        while q:
            curr_x, curr_y = q.pop(0)

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                next_x, next_y = curr_x + dx, curr_y + dy

                if not (0 <= next_x < self.canvas_width and 0 <= next_y < self.canvas_height):
                    continue
                if (next_x, next_y) in visited_in_algo:
                    continue

                try:
                    neighbor_color_rgb = self.fill_photo_image.get(next_x, next_y)
                except tk.TclError:
                    continue

                    # Check if neighbor is NOT fill color AND is inside polygon
                if neighbor_color_rgb != self.FILL_COLOR_RGB and \
                        self.is_point_in_polygon((next_x + 0.5, next_y + 0.5), polygon_vertices):

                    self.fill_photo_image.put(self.FILL_COLOR_HEX, (next_x, next_y))
                    q.append((next_x, next_y))
                    visited_in_algo.add((next_x, next_y))
                    count += 1
                    if count % 50 == 0:
                        yield f"Обработано: ({next_x},{next_y}). Стек: {len(q)}"
                        if self.debug_paused:
                            self.canvas.itemconfig(self.fill_canvas_item_id, image=self.fill_photo_image)
                            self.master.update()

        yield "Заполнение (простая затравка) завершено."

    def _seed_fill_scanline_generator(self, polygon_vertices, seed_point_tuple):
        seed_x, seed_y = int(seed_point_tuple[0]), int(seed_point_tuple[1])

        if not (0 <= seed_x < self.canvas_width and 0 <= seed_y < self.canvas_height):
            yield "Ошибка: Точка затравки вне холста."
            return
        if not self.is_point_in_polygon((seed_x + 0.5, seed_y + 0.5), polygon_vertices):
            yield "Ошибка: Точка затравки вне полигона."
            return

        stack = [(seed_x, seed_y)]

        yield f"Начальная затравка ({seed_x},{seed_y})"

        processed_pixels_total = 0

        while stack:
            curr_x_from_stack, curr_y_scan = stack.pop()

            try:
                if self.fill_photo_image.get(curr_x_from_stack, curr_y_scan) == self.FILL_COLOR_RGB:
                    continue
                if not self.is_point_in_polygon((curr_x_from_stack + 0.5, curr_y_scan + 0.5), polygon_vertices):
                    continue
            except tk.TclError:
                continue

            x_left = curr_x_from_stack
            while x_left >= 0:
                try:
                    if self.fill_photo_image.get(x_left, curr_y_scan) == self.FILL_COLOR_RGB: break
                    if not self.is_point_in_polygon((x_left + 0.5, curr_y_scan + 0.5), polygon_vertices): break
                except tk.TclError:
                    break
                x_left -= 1
            x_left += 1

            x_right = curr_x_from_stack
            while x_right < self.canvas_width:
                try:
                    if self.fill_photo_image.get(x_right, curr_y_scan) == self.FILL_COLOR_RGB: break
                    if not self.is_point_in_polygon((x_right + 0.5, curr_y_scan + 0.5), polygon_vertices): break
                except tk.TclError:
                    break
                x_right += 1
            x_right -= 1

            if x_left > x_right: continue  # No valid span from this seed on this line

            for x_fill in range(x_left, x_right + 1):
                self.fill_photo_image.put(self.FILL_COLOR_HEX, (x_fill, curr_y_scan))
                processed_pixels_total += 1

            yield f"y={curr_y_scan}, пролет [{x_left}-{x_right}]. Стек: {len(stack)}. Всего: {processed_pixels_total}"
            if self.debug_paused:
                self.canvas.itemconfig(self.fill_canvas_item_id, image=self.fill_photo_image)
                self.master.update()

            for y_offset in [-1, 1]:
                next_y_scan = curr_y_scan + y_offset
                if not (0 <= next_y_scan < self.canvas_height): continue

                in_span_on_next_line = False
                for x_check in range(x_left, x_right + 1):  # Check above/below the filled span
                    try:
                        is_inside = self.is_point_in_polygon((x_check + 0.5, next_y_scan + 0.5), polygon_vertices)
                        is_not_filled = (self.fill_photo_image.get(x_check, next_y_scan) != self.FILL_COLOR_RGB)

                        if is_inside and is_not_filled:
                            if not in_span_on_next_line:
                                stack.append((x_check, next_y_scan))
                                in_span_on_next_line = True
                        else:
                            in_span_on_next_line = False
                    except tk.TclError:
                        in_span_on_next_line = False
                        continue

            if self.debug_paused and processed_pixels_total % 200 == 0:
                self.master.update()

        yield f"Заполнение (построчная затравка) завершено. Всего пикс: {processed_pixels_total}"

    # --- Methods from previous version (Normals, Convex Hull) ---
    def get_internal_normals(self, polygon_points):
        if not polygon_points or len(polygon_points) < 3:
            return []

        normals = []
        n = len(polygon_points)
        for i in range(n):
            p1 = polygon_points[i]
            p2 = polygon_points[(i + 1) % n]

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            normal_vec = (dy, -dx)  # Assumes CCW for "internal"
            length = math.sqrt(normal_vec[0] ** 2 + normal_vec[1] ** 2)
            unit_normal = (normal_vec[0] / length, normal_vec[1] / length) if length != 0 else (0, 0)

            mid_point = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            normals.append({'mid': mid_point, 'normal': unit_normal})
        return normals

    def show_normals_selected(self):
        self.clear_canvas_objects("temp_normal")
        if self.active_polygon_index == -1 or not self.polygons:
            messagebox.showerror("Ошибка", "Нет активного полигона.")
            return

        polygon = self.polygons[self.active_polygon_index]
        if len(polygon) < 3:
            self.status_var.set(f"Полигон #{self.active_polygon_index + 1} слишком мал.")
            return

        normals_data = self.get_internal_normals(polygon)
        normal_display_length = 20

        for n_data in normals_data:
            mid = n_data['mid']
            unit_normal = n_data['normal']

            start_x, start_y = mid
            end_x = start_x + unit_normal[0] * normal_display_length
            end_y = start_y + unit_normal[1] * normal_display_length

            self.canvas.create_line(start_x, start_y, end_x, end_y, fill="orange", width=2, arrow=tk.LAST,
                                    tags="temp_normal")

        self.status_var.set(f"Показаны нормали для полигона #{self.active_polygon_index + 1}.")
        self.redraw_all()  # Redraw to show normals on top

    def is_polygon_convex(self, polygon_points):
        if not polygon_points or len(polygon_points) < 3: return False
        n = len(polygon_points)
        got_negative = False;
        got_positive = False
        for i in range(n):
            p1, p2, p3 = polygon_points[i], polygon_points[(i + 1) % n], polygon_points[(i + 2) % n]
            current_orientation = orientation(p1, p2, p3)
            if current_orientation == 1:
                got_positive = True
            elif current_orientation == 2:
                got_negative = True
            if got_positive and got_negative: return False
        return True

    def check_convexity_selected(self):
        self.clear_canvas_objects("temp_")
        if self.active_polygon_index == -1 or not self.polygons:
            messagebox.showerror("Ошибка", "Нет активного полигона.")
            return
        poly = self.polygons[self.active_polygon_index]
        if len(poly) < 3:
            messagebox.showinfo("Выпуклость", f"Полигон #{self.active_polygon_index + 1} слишком мал.")
            return
        convex = self.is_polygon_convex(poly)
        msg = f"Полигон #{self.active_polygon_index + 1} {'ВЫПУКЛЫЙ' if convex else 'НЕВЫПУКЛЫЙ'}."
        messagebox.showinfo("Выпуклость", msg);
        self.status_var.set(msg)
        self.redraw_all()

    def _graham_scan(self, points_to_hull_input):
        # Operate on a copy if modification is needed, or ensure points are tuples if hashability is used
        points_to_hull = [list(p) for p in points_to_hull_input]  # Ensure points are lists [x,y]

        if not points_to_hull or len(points_to_hull) < 3:
            # If less than 3 unique points, hull is just these points (or line/point)
            return points_to_hull

            # Find P0: point with min y, then min x
        P0 = min(points_to_hull, key=lambda p: (p[1], p[0]))

        # Sort points by polar angle with P0.
        # Tie-breaking: if angles are equal, sort by distance (closer first, though stack logic handles it).
        # For robustness, ensure P0 is treated correctly.
        def sort_key_graham(p):
            if p == P0:
                # P0 should have the smallest angle, and 0 distance to itself for sorting.
                return (-float('inf'), 0)
            angle = math.atan2(p[1] - P0[1], p[0] - P0[0])
            distance = dist_sq(P0, p)  # (p[0]-P0[0])**2 + (p[1]-P0[1])**2
            return (angle, distance)  # Sort by angle, then by distance

        sorted_points = sorted(points_to_hull, key=sort_key_graham)

        # Filter `sorted_points` to `points_for_stack`.
        # This step removes points that are collinear with P0 and another point, keeping the farthest.
        # P0 is sorted_points[0].
        if len(sorted_points) <= 1:
            return sorted_points  # Handles 0 or 1 point cases

        points_for_stack = [sorted_points[0]]  # Start with P0

        # Add the first point after P0 to the stack if it exists and is different from P0
        # (uniqueness of points should be handled before calling _graham_scan,
        # but `unique_points_for_hull` does this)
        if len(sorted_points) > 1:
            # We need to ensure P0 is not added twice if it was the only point.
            # The check `p == P0` in sort_key and P0 being min ensures it's first.
            # The filtering of unique_points_for_hull ensures P0 is not duplicated in input.
            points_for_stack.append(sorted_points[1])

        for i in range(2, len(sorted_points)):
            p_current = sorted_points[i]
            # points_for_stack[-2] is P0 (if len > 1)
            # points_for_stack[-1] is the last point kept for a given angle from P0
            # p_current is the next candidate from sorted_points.
            # If P0, points_for_stack[-1], and p_current are collinear,
            # p_current has the same angle to P0 as points_for_stack[-1].
            # Since sorted_points is sorted by distance for same angles, p_current is further.
            # So, replace points_for_stack[-1] with p_current.

            # Ensure there are at least two points in points_for_stack to check orientation with P0
            # The first point in points_for_stack is P0.
            # The second point (points_for_stack[1] or points_for_stack[-1] if len is 2) is the reference.
            if len(points_for_stack) < 2:  # Should not happen if sorted_points had >1 and we added sorted_points[1]
                points_for_stack.append(p_current)  # Should be P0, then first angular point, then this
                continue

            # Check orientation relative to P0 (which is points_for_stack[0]) and the last point added for an angle streak
            # This logic is to ensure that for points collinear with P0, only the furthest is kept.
            # `points_for_stack[0]` is P0. `points_for_stack[-1]` is the current "farthest" for the current angle.
            if orientation(points_for_stack[0], points_for_stack[-1], p_current) == 0:  # Collinear wrt P0
                points_for_stack[-1] = p_current  # Replace with the further point p_current
            else:
                points_for_stack.append(p_current)  # New angle, add it

        # If after filtering, not enough points for a polygon, return what we have
        if len(points_for_stack) < 3:
            return points_for_stack

            # Main Graham scan stack logic
        hull = []
        for p_candidate in points_for_stack:
            # While hull has at least 2 points and turn (hull[-2], hull[-1], p_candidate) is not CCW (left)
            # A CCW turn is type 2 in our orientation function.
            while len(hull) >= 2 and orientation(hull[-2], hull[-1], p_candidate) != 2:
                hull.pop()
            hull.append(p_candidate)

        return hull

    def _jarvis_march(self, points_to_hull):
        if not points_to_hull or len(points_to_hull) < 3:
            return points_to_hull

        # Find the leftmost point (min x, then min y)
        start_point = min(points_to_hull, key=lambda p: (p[0], p[1]))

        hull = []
        current_point = start_point

        while True:
            hull.append(current_point)

            # Find the next point in the hull
            next_point_candidate = points_to_hull[0]
            if next_point_candidate == current_point:  # Ensure it's not the current point itself
                if len(points_to_hull) > 1:
                    next_point_candidate = points_to_hull[1]
                else:  # Only one point, hull is just that point
                    break

            for test_point in points_to_hull:
                if test_point == current_point:
                    continue

                # o > 0 is CW, o < 0 is CCW (left turn)
                # We want the point that makes the "most counter-clockwise" turn
                # or is the "leftmost" with respect to current_point -> next_point_candidate
                o = orientation(current_point, next_point_candidate, test_point)

                if o == 2:  # test_point is CCW (left) of current_point -> next_point_candidate
                    next_point_candidate = test_point
                elif o == 0:  # Collinear
                    # If collinear, choose the one further away
                    if dist_sq(current_point, test_point) > dist_sq(current_point, next_point_candidate):
                        next_point_candidate = test_point

            current_point = next_point_candidate
            if current_point == start_point:  # Completed the hull
                break
            if len(hull) > len(points_to_hull):  # Safety break for degenerate cases
                messagebox.showerror("Jarvis March", "Превышено количество точек, возможна ошибка в данных.")
                return hull  # return what we have

        return hull
    def calculate_convex_hull(self, method_name):
        self.clear_canvas_objects("temp_")
        self.clear_canvas_objects("convex_hull_")  # Clear old hull drawings
        self.drawn_hull = []

        points_for_hull_calc = []
        if self.active_polygon_index != -1 and self.polygons:
            # Use vertices of the active polygon
            points_for_hull_calc.extend(self.polygons[self.active_polygon_index])
            source_msg = f"полигона #{self.active_polygon_index + 1}"
        elif self.current_polygon_points:
            # Use points of polygon being currently drawn
            points_for_hull_calc.extend(self.current_polygon_points)
            source_msg = "текущего набора точек"
        else:
            # If no active polygon and no current points, collect all vertices from all polygons
            for poly in self.polygons:
                points_for_hull_calc.extend(poly)
            if not points_for_hull_calc:  # Still no points? Check if any lines exist.
                for line in self.lines:
                    points_for_hull_calc.extend(line)  # Add line endpoints

            if not points_for_hull_calc:
                messagebox.showinfo("Выпуклая оболочка",
                                    "Нет точек для построения оболочки. Нарисуйте полигон или точки.")
                return
            source_msg = "всех нарисованных вершин"

        # Remove duplicate points for hull calculation
        unique_points_for_hull = list(set(map(tuple, points_for_hull_calc)))  # Make points hashable for set
        unique_points_for_hull = [list(p) for p in
                                  unique_points_for_hull]  # Convert back to lists if needed, or keep as tuples

        if len(unique_points_for_hull) < 3:
            messagebox.showinfo("Выпуклая оболочка",
                                f"Недостаточно уникальных точек ({len(unique_points_for_hull)}) для построения оболочки из {source_msg}.")
            self.drawn_hull = unique_points_for_hull  # Draw the points/line if <3
            self.redraw_all()
            return

        if method_name == "graham":
            self.drawn_hull = self._graham_scan(unique_points_for_hull)
            method_str = "Обход Грэхема"
        elif method_name == "jarvis":
            self.drawn_hull = self._jarvis_march(unique_points_for_hull)
            method_str = "Метод Джарвиса"
        else:
            return

        self.status_var.set(
            f"Построена выпуклая оболочка ({method_str}) для {source_msg}. Вершин в оболочке: {len(self.drawn_hull)}")
        self.redraw_all()

    def perform_segment_polygon_intersection(self, line_segment_pts):
        self.clear_canvas_objects("temp_intersection")
        if self.active_polygon_index == -1 or not self.polygons:
            messagebox.showerror("Ошибка", "Нет активного полигона.")
            self.set_mode_idle()
            return

        if not line_segment_pts or len(line_segment_pts) != 2:
            messagebox.showerror("Ошибка", "Нужен отрезок (2 точки).")
            self.set_mode_idle()
            return

        polygon = self.polygons[self.active_polygon_index]
        p_line1, p_line2 = line_segment_pts
        intersections_found = []

        for i in range(len(polygon)):
            p_poly1 = polygon[i]
            p_poly2 = polygon[(i + 1) % len(polygon)]

            if segments_intersect(p_line1, p_line2, p_poly1, p_poly2):
                intersection_pt = get_intersection_point(p_line1, p_line2, p_poly1, p_poly2)
                if intersection_pt:
                    intersections_found.append(intersection_pt)
                    self.canvas.create_oval(
                        intersection_pt[0] - 5, intersection_pt[1] - 5,
                        intersection_pt[0] + 5, intersection_pt[1] + 5,
                        fill="red", outline="black", tags="temp_intersection_point"
                    )

        if intersections_found:
            msg = f"Найдено пересечений: {len(intersections_found)}."
            self.canvas.create_line(p_line1[0], p_line1[1], p_line2[0], p_line2[1], fill="orange", width=2, dash=(2, 2),
                                    tags="temp_intersection_line")
        else:
            msg = f"Пересечений не найдено."
            # messagebox.showinfo("Пересечение", msg) # Can be annoying if no intersection often
        self.status_var.set(msg)
        self.set_mode_idle()
        self.redraw_all()

    def clear_all(self):
        self.reset_debug()
        self.clear_fill_image()

        self.current_polygon_points = []
        self.polygons = []
        self.active_polygon_index = -1
        self.current_line_points = []
        self.lines = []
        self.drawn_hull = []

        all_items = self.canvas.find_all()
        for item_id in all_items:
            if item_id != self.fill_canvas_item_id:
                try:  # Add try-except for robustness during clear all
                    if self.canvas.winfo_exists(): self.canvas.delete(item_id)
                except tk.TclError:
                    pass

        self.set_mode_idle()
        self.status_var.set("Все очищено. Готов.")
        self.redraw_all()



if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonEditor(root)
    root.mainloop()
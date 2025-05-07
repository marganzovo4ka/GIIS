import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import math


# --- Helper Geometric Functions ---

def orientation(p, q, r):
    """
    Determines the orientation of an ordered triplet (p, q, r).
    Returns:
    0 --> p, q, r are collinear
    1 --> Clockwise
    2 --> Counterclockwise
    """
    if p is None or q is None or r is None: return 0  # Should not happen with valid inputs
    val = (q[1] - p[1]) * (r[0] - q[0]) - \
          (q[0] - p[0]) * (r[1] - q[1])
    if val == 0: return 0  # Collinear
    return 1 if val > 0 else 2  # Clockwise or Counterclockwise


def dist_sq(p1, p2):
    """Squared Euclidean distance between p1 and p2."""
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


def on_segment(p, q, r):
    """Given three collinear points p, q, r, check if point q lies on segment pr."""
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))


def segments_intersect(p1, q1, p2, q2):
    """Check if line segment 'p1q1' and 'p2q2' intersect."""
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        if o1 != o2 and o3 != o4:
            return True

    # Special Cases for collinearity
    # p1, q1, p2 are collinear and p2 lies on segment p1q1
    if o1 == 0 and on_segment(p1, p2, q1): return True
    # p1, q1, q2 are collinear and q2 lies on segment p1q1
    if o2 == 0 and on_segment(p1, q2, q1): return True
    # p2, q2, p1 are collinear and p1 lies on segment p2q2
    if o3 == 0 and on_segment(p2, p1, q2): return True
    # p2, q2, q1 are collinear and q1 lies on segment p2q2
    if o4 == 0 and on_segment(p2, q1, q2): return True

    return False  # Doesn't fall in any of the above cases


def get_intersection_point(p1, q1, p2, q2):
    """
    Finds the intersection point of two line segments p1q1 and p2q2.
    Returns the intersection point (x, y) or None if they don't intersect or are collinear.
    Assumes segments_intersect has already confirmed they do intersect and are not collinear for a unique point.
    """
    # Line AB represented as A + r(B - A)
    # Line CD represented as C + s(D - C)
    # If they intersect, then A + r(B - A) = C + s(D - C)

    # (x1, y1) = p1, (x2, y2) = q1
    # (x3, y3) = p2, (x4, y4) = q2

    x1, y1 = p1
    x2, y2 = q1
    x3, y3 = p2
    x4, y4 = q2

    # Denominator for both t and u
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        return None  # Lines are parallel or collinear

    # Numerator for t
    t_num = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
    # Numerator for u
    u_num = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3))

    t = t_num / den
    u = u_num / den

    if 0 <= t <= 1 and 0 <= u <= 1:
        # Intersection point
        intersect_x = x1 + t * (x2 - x1)
        intersect_y = y1 + t * (y2 - y1)
        return (intersect_x, intersect_y)

    return None  # No intersection within the segments


# --- Main Application Class ---
class PolygonEditor:
    def __init__(self, master):
        self.master = master
        master.title("Элементарный Графический Редактор Полигонов")

        self.current_polygon_points = []
        self.polygons = []  # List of lists of points
        self.active_polygon_index = -1  # Index of the polygon currently being operated on

        self.current_line_points = []
        self.lines = []  # List of line segments [(p1, p2), ...]

        self.hull_points = []  # Points for convex hull
        self.drawn_hull = []  # The calculated hull polygon

        self.mode = "idle"  # "draw_polygon", "draw_line", "point_in_polygon_test"

        # --- Menu ---
        self.menubar = tk.Menu(master)

        filemenu = tk.Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Очистить всё", command=self.clear_all)
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=master.quit)
        self.menubar.add_cascade(label="Файл", menu=filemenu)

        self.polygon_menu = tk.Menu(self.menubar, tearoff=0)  # Used by toolbar too
        self.polygon_menu.add_command(label="Завершить полигон", command=self.finish_polygon)
        self.polygon_menu.add_command(label="Проверить на выпуклость", command=self.check_convexity_selected)
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

        master.config(menu=self.menubar)

        # --- Toolbar ---
        self.toolbar = ttk.Frame(master, padding="2")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_draw_poly = ttk.Button(self.toolbar, text="Рисовать полигон", command=self.set_mode_draw_polygon)
        btn_draw_poly.pack(side=tk.LEFT, padx=2, pady=2)

        # "Построение полигонов" dropdown
        self.poly_build_var = tk.StringVar()
        self.poly_build_options = {
            "Обход Грэхема": lambda: self.calculate_convex_hull("graham"),
            "Метод Джарвиса": lambda: self.calculate_convex_hull("jarvis"),
            "Завершить полигон": self.finish_polygon,
            "Проверить выпуклость": self.check_convexity_selected,
            "Показать нормали": self.show_normals_selected
        }
        # Using OptionMenu for simplicity as a toolbar item
        poly_build_om = ttk.OptionMenu(self.toolbar, self.poly_build_var, "Построение полигонов",
                                       *self.poly_build_options.keys(), command=self.on_poly_build_select)
        poly_build_om.pack(side=tk.LEFT, padx=2, pady=2)

        btn_draw_line = ttk.Button(self.toolbar, text="Рисовать линию", command=self.set_mode_draw_line)
        btn_draw_line.pack(side=tk.LEFT, padx=2, pady=2)

        btn_intersect = ttk.Button(self.toolbar, text="Пересечение линии/полигона",
                                   command=self.set_mode_segment_polygon_intersection)
        btn_intersect.pack(side=tk.LEFT, padx=2, pady=2)

        btn_point_in_poly = ttk.Button(self.toolbar, text="Точка в полигоне?", command=self.set_mode_point_in_polygon)
        btn_point_in_poly.pack(side=tk.LEFT, padx=2, pady=2)

        btn_clear = ttk.Button(self.toolbar, text="Очистить", command=self.clear_all)
        btn_clear.pack(side=tk.LEFT, padx=2, pady=2)

        # --- Canvas ---
        self.canvas = tk.Canvas(master, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # For finishing polygon typically

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Готов. Выберите действие.")
        self.statusbar = ttk.Label(master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.select_last_polygon_as_active()

    def on_poly_build_select(self, selection):
        if selection in self.poly_build_options:
            self.poly_build_options[selection]()
        self.poly_build_var.set("Построение полигонов")  # Reset dropdown text

    def clear_canvas_objects(self, tag_prefix=""):
        if not tag_prefix:
            self.canvas.delete("all")
        else:
            items_to_delete = []
            for item_id in self.canvas.find_all():
                tags = self.canvas.gettags(item_id)
                if any(tag.startswith(tag_prefix) for tag in tags):
                    items_to_delete.append(item_id)
            for item_id in items_to_delete:
                self.canvas.delete(item_id)

    def redraw_all(self):
        self.clear_canvas_objects()  # Clear previous drawings

        # Draw all completed polygons
        for i, poly in enumerate(self.polygons):
            if len(poly) > 1:
                # Create a flat list for tk.Canvas.create_polygon
                flat_poly = [coord for point in poly for coord in point]
                fill_color = "lightblue" if i == self.active_polygon_index else "lightgray"
                self.canvas.create_polygon(flat_poly, outline="black", fill=fill_color, width=2, tags=f"polygon_{i}")
                for p_idx, p in enumerate(poly):
                    self.canvas.create_oval(p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3, fill="blue",
                                            tags=f"polygon_{i}_vertex_{p_idx}")

        # Draw current polygon being built
        if self.current_polygon_points:
            for p in self.current_polygon_points:
                self.canvas.create_oval(p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3, fill="red", tags="current_point")
            if len(self.current_polygon_points) > 1:
                for i in range(len(self.current_polygon_points) - 1):
                    p1 = self.current_polygon_points[i]
                    p2 = self.current_polygon_points[i + 1]
                    self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="red", dash=(4, 2),
                                            tags="current_poly_segment")

        # Draw all lines
        for i, line_segment in enumerate(self.lines):
            p1, p2 = line_segment
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="green", width=2, tags=f"line_{i}")
            self.canvas.create_oval(p1[0] - 2, p1[1] - 2, p1[0] + 2, p1[1] + 2, fill="darkgreen", tags=f"line_{i}_p1")
            self.canvas.create_oval(p2[0] - 2, p2[1] - 2, p2[0] + 2, p2[1] + 2, fill="darkgreen", tags=f"line_{i}_p2")

        # Draw current line being built
        if self.current_line_points:
            for p in self.current_line_points:
                self.canvas.create_oval(p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3, fill="darkgreen",
                                        tags="current_line_point")

        # Draw convex hull if present
        if self.drawn_hull and len(self.drawn_hull) > 1:
            flat_hull = [coord for point in self.drawn_hull for coord in point]
            self.canvas.create_polygon(flat_hull, outline="purple", fill="", width=3, dash=(5, 5),
                                       tags="convex_hull_shape")
            for p in self.drawn_hull:
                self.canvas.create_oval(p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4, outline="purple", fill="magenta",
                                        tags="convex_hull_point")

        self.status_var.set(
            f"Режим: {self.mode}. Активный полигон: {'#' + str(self.active_polygon_index + 1) if self.active_polygon_index != -1 else 'Нет'}")

    def on_canvas_click(self, event):
        x, y = event.x, event.y
        point = (x, y)

        # Try to select a polygon if idle or related mode
        if self.mode in ["idle", "check_convexity", "show_normals", "segment_polygon_intersection_poly_select",
                         "point_in_polygon_test_poly_select"]:
            clicked_on_polygon_index = -1
            for i, poly in enumerate(self.polygons):
                if self.is_point_in_polygon(point, poly):  # A simple check
                    clicked_on_polygon_index = i
                    break
            if clicked_on_polygon_index != -1:
                self.active_polygon_index = clicked_on_polygon_index
                self.status_var.set(f"Выбран полигон #{self.active_polygon_index + 1}")
                self.redraw_all()
                # If we were in a selection mode, proceed
                if self.mode == "segment_polygon_intersection_poly_select":
                    self.status_var.set(
                        f"Полигон #{self.active_polygon_index + 1} выбран. Теперь нарисуйте отрезок (2 клика).")
                    self.set_mode_draw_line(for_intersection=True)  # Special sub-mode
                    return
                if self.mode == "point_in_polygon_test_poly_select":
                    self.status_var.set(
                        f"Полигон #{self.active_polygon_index + 1} выбран. Кликните точку для проверки.")
                    self.mode = "point_in_polygon_test_point_select"  # Special sub-mode
                    return
            # else: # Clicked outside any polygon
            # self.active_polygon_index = -1 # Deselect? Or keep current? Let's keep current.

        if self.mode == "draw_polygon":
            self.current_polygon_points.append(point)
            self.status_var.set(
                f"Добавлена точка {point}. Всего точек: {len(self.current_polygon_points)}. ПКМ для завершения.")
        elif self.mode == "draw_line" or self.mode == "draw_line_for_intersection":
            self.current_line_points.append(point)
            if len(self.current_line_points) == 2:
                if self.mode == "draw_line_for_intersection":
                    self.perform_segment_polygon_intersection(self.current_line_points)
                    self.current_line_points = []
                    self.set_mode_idle()  # Or back to selection
                else:
                    self.lines.append(tuple(self.current_line_points))
                    self.current_line_points = []
                    self.status_var.set("Отрезок нарисован.")
                self.mode = "idle"  # Reset mode after line is drawn
            else:
                self.status_var.set(f"Первая точка отрезка: {point}. Кликните для второй точки.")
        elif self.mode == "point_in_polygon_test_point_select":
            if self.active_polygon_index != -1:
                polygon = self.polygons[self.active_polygon_index]
                is_inside = self.is_point_in_polygon(point, polygon)
                self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="orange", outline="black", tags="test_point")
                msg = f"Точка {point} {'ВНУТРИ' if is_inside else 'СНАРУЖИ'} полигона #{self.active_polygon_index + 1}."
                messagebox.showinfo("Результат проверки точки", msg)
                self.status_var.set(msg + " Выберите действие.")
                self.set_mode_idle()
            else:
                messagebox.showerror("Ошибка", "Сначала выберите полигон.")
                self.set_mode_point_in_polygon()  # Go back to polygon selection step

        self.redraw_all()

    def on_canvas_right_click(self, event):
        if self.mode == "draw_polygon":
            self.finish_polygon()
            self.status_var.set("Полигон завершен. Выберите действие.")
            self.set_mode_idle()  # Reset mode
            self.redraw_all()

    def select_last_polygon_as_active(self):
        if self.polygons:
            self.active_polygon_index = len(self.polygons) - 1
        else:
            self.active_polygon_index = -1

    # --- Mode Setters ---
    def set_mode_idle(self):
        self.mode = "idle"
        self.current_polygon_points = []  # Clear any partial polygon
        self.current_line_points = []  # Clear any partial line
        self.status_var.set("Готов. Выберите действие или кликните на полигон для выбора.")
        self.redraw_all()

    def set_mode_draw_polygon(self):
        self.mode = "draw_polygon"
        self.current_polygon_points = []
        self.drawn_hull = []  # Clear previous hull if any
        self.clear_canvas_objects("temp_")  # Clear temporary drawings like normals, intersections
        self.status_var.set("Режим: Рисование полигона. Кликайте для добавления вершин. ПКМ для завершения.")
        self.redraw_all()

    def set_mode_draw_line(self, for_intersection=False):
        self.mode = "draw_line_for_intersection" if for_intersection else "draw_line"
        self.current_line_points = []
        self.drawn_hull = []
        self.clear_canvas_objects("temp_")
        self.status_var.set("Режим: Рисование линии. Кликните для первой точки.")
        self.redraw_all()

    def set_mode_point_in_polygon(self):
        self.clear_canvas_objects("temp_")
        if not self.polygons:
            messagebox.showinfo("Информация", "Сначала нарисуйте хотя бы один полигон.")
            self.set_mode_idle()
            return
        self.mode = "point_in_polygon_test_poly_select"  # First select polygon
        self.status_var.set("Выберите полигон для проверки, кликнув по нему.")
        self.redraw_all()

    def set_mode_segment_polygon_intersection(self):
        self.clear_canvas_objects("temp_")
        if not self.polygons:
            messagebox.showinfo("Информация", "Сначала нарисуйте хотя бы один полигон.")
            self.set_mode_idle()
            return
        self.mode = "segment_polygon_intersection_poly_select"
        self.status_var.set("Выберите полигон для проверки пересечения, кликнув по нему.")
        self.redraw_all()

    # --- Polygon Operations ---
    def finish_polygon(self):
        if self.mode == "draw_polygon" and len(self.current_polygon_points) >= 3:
            self.polygons.append(list(self.current_polygon_points))  # Make a copy
            self.active_polygon_index = len(self.polygons) - 1
            self.current_polygon_points = []
            self.status_var.set(
                f"Полигон #{self.active_polygon_index + 1} создан. Вершин: {len(self.polygons[self.active_polygon_index])}")
            self.set_mode_idle()
        elif self.mode == "draw_polygon":
            messagebox.showwarning("Рисование полигона", "Нужно как минимум 3 точки для полигона.")
        self.redraw_all()

    def is_polygon_convex(self, polygon_points):
        if not polygon_points or len(polygon_points) < 3:
            return False  # Not a polygon or degenerate

        n = len(polygon_points)
        got_negative = False
        got_positive = False

        for i in range(n):
            p1 = polygon_points[i]
            p2 = polygon_points[(i + 1) % n]
            p3 = polygon_points[(i + 2) % n]

            # Using orientation; for Tkinter's coordinate system (y down):
            # Left turn (CCW) will be val < 0
            # Right turn (CW) will be val > 0
            # We need all turns to be the same (e.g. all CCW or all CW)
            # Let's assume CCW drawing for "standard" convexity.

            # Cross product: (x2-x1)(y3-y1) - (y2-y1)(x3-x1)
            # If using our orientation helper: orientation(p1,p2,p3)
            # For CCW: all should be type 2 (or 0 for collinear on boundary)
            # For CW: all should be type 1 (or 0 for collinear on boundary)

            current_orientation = orientation(p1, p2, p3)

            if current_orientation == 1:  # Clockwise
                got_positive = True
            elif current_orientation == 2:  # Counter-clockwise
                got_negative = True

            # If we have both positive and negative turns, it's concave
            if got_positive and got_negative:
                return False

        # If we reach here, all turns were in the same direction (or collinear)
        return True

    def check_convexity_selected(self):
        self.clear_canvas_objects("temp_")
        if self.active_polygon_index == -1 or not self.polygons:
            messagebox.showerror("Ошибка", "Нет активного полигона для проверки.")
            return

        polygon = self.polygons[self.active_polygon_index]
        if len(polygon) < 3:
            messagebox.showinfo("Проверка на выпуклость",
                                f"Полигон #{self.active_polygon_index + 1} имеет менее 3 вершин, не может быть проверен.")
            return

        convex = self.is_polygon_convex(polygon)
        msg = f"Полигон #{self.active_polygon_index + 1} {'ВЫПУКЛЫЙ' if convex else 'НЕВЫПУКЛЫЙ'}."
        messagebox.showinfo("Проверка на выпуклость", msg)
        self.status_var.set(msg)

    def get_internal_normals(self, polygon_points):
        """
        Calculates internal normals. Assumes polygon is CCW for simplicity.
        If polygon is CW, these will be external.
        For non-convex, "internal" is still defined locally.
        """
        if not polygon_points or len(polygon_points) < 3:
            return []

        normals = []
        n = len(polygon_points)

        # Determine winding order to correctly orient normals if needed
        # For now, assume CCW for "internal" meaning.
        # A more robust way would be to check if midpoint + normal_epsilon is inside.

        for i in range(n):
            p1 = polygon_points[i]
            p2 = polygon_points[(i + 1) % n]

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            # For CCW polygon, internal normal is (dy, -dx)
            # For CW polygon, internal normal is (-dy, dx)
            # Let's assume CCW for now. If the user draws CW, they will point outwards.
            # For a robust solution, one might enforce CCW winding or check.
            normal_vec = (dy, -dx)

            length = math.sqrt(normal_vec[0] ** 2 + normal_vec[1] ** 2)
            if length == 0:  # Should not happen for distinct points
                unit_normal = (0, 0)
            else:
                unit_normal = (normal_vec[0] / length, normal_vec[1] / length)

            mid_point = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            normals.append({'mid': mid_point, 'normal': unit_normal, 'original_vec': normal_vec})

        return normals

    def show_normals_selected(self):
        self.clear_canvas_objects("temp_normal")
        if self.active_polygon_index == -1 or not self.polygons:
            messagebox.showerror("Ошибка", "Нет активного полигона для показа нормалей.")
            return

        polygon = self.polygons[self.active_polygon_index]
        if len(polygon) < 3:
            self.status_var.set(f"Полигон #{self.active_polygon_index + 1} слишком мал для нормалей.")
            return

        normals = self.get_internal_normals(polygon)
        normal_display_length = 30  # pixels

        for n_data in normals:
            mid = n_data['mid']
            unit_normal = n_data['normal']

            start_x, start_y = mid
            end_x = start_x + unit_normal[0] * normal_display_length
            end_y = start_y + unit_normal[1] * normal_display_length

            self.canvas.create_line(start_x, start_y, end_x, end_y, fill="orange", width=2, arrow=tk.LAST,
                                    tags="temp_normal")

        self.status_var.set(
            f"Показаны внутренние нормали для полигона #{self.active_polygon_index + 1} (предполагая CCW обход).")

    # --- Convex Hull ---
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

    # --- Line-Polygon Interaction ---
    def perform_segment_polygon_intersection(self, line_segment):
        self.clear_canvas_objects("temp_intersection")
        if self.active_polygon_index == -1 or not self.polygons:
            messagebox.showerror("Ошибка", "Нет активного полигона для проверки пересечений.")
            self.set_mode_idle()
            return

        if not line_segment or len(line_segment) != 2:
            messagebox.showerror("Ошибка", "Нужен отрезок (2 точки) для проверки.")
            self.set_mode_idle()
            return

        polygon = self.polygons[self.active_polygon_index]
        if len(polygon) < 1:  # Should be >= 3 for a polygon
            self.set_mode_idle()
            return

        p_line1, p_line2 = line_segment
        intersections_found = []

        for i in range(len(polygon)):
            p_poly1 = polygon[i]
            p_poly2 = polygon[(i + 1) % len(polygon)]  # Next vertex, wraps around

            # Check basic intersection first
            if segments_intersect(p_line1, p_line2, p_poly1, p_poly2):
                # If they intersect, find the point
                intersection_pt = get_intersection_point(p_line1, p_line2, p_poly1, p_poly2)
                if intersection_pt:
                    intersections_found.append(intersection_pt)
                    self.canvas.create_oval(
                        intersection_pt[0] - 5, intersection_pt[1] - 5,
                        intersection_pt[0] + 5, intersection_pt[1] + 5,
                        fill="red", outline="black", tags="temp_intersection_point"
                    )

        if intersections_found:
            msg = f"Найдено пересечений: {len(intersections_found)} с полигоном #{self.active_polygon_index + 1}."
            self.status_var.set(msg)
            # Also draw the test line segment itself
            self.canvas.create_line(p_line1[0], p_line1[1], p_line2[0], p_line2[1], fill="orange", width=2, dash=(2, 2),
                                    tags="temp_intersection_line")
        else:
            msg = f"Пересечений отрезка с полигоном #{self.active_polygon_index + 1} не найдено."
            self.status_var.set(msg)
            messagebox.showinfo("Пересечение", msg)

        self.set_mode_idle()  # Back to idle after test
        self.redraw_all()  # Ensure main elements are there

    def is_point_in_polygon(self, point, polygon_points):
        """
        Ray casting algorithm to check if point is inside polygon.
        """
        if not polygon_points or len(polygon_points) < 3:
            return False

        n = len(polygon_points)
        x, y = point
        inside = False

        p1x, p1y = polygon_points[0]
        for i in range(n + 1):
            p2x, p2y = polygon_points[i % n]  # Loop back to the first point
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:  # Edge is not horizontal
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:  # Edge is vertical or point is to the left of intersection
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    # --- General Utility ---
    def clear_all(self):
        self.current_polygon_points = []
        self.polygons = []
        self.active_polygon_index = -1
        self.current_line_points = []
        self.lines = []
        self.hull_points = []
        self.drawn_hull = []
        self.canvas.delete("all")
        self.set_mode_idle()
        self.status_var.set("Все очищено. Готов.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonEditor(root)
    root.mainloop()
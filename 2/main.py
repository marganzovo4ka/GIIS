import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
import time

# --- Configuration ---
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 500
DEBUG_GRID_SIZE = 300
DEBUG_CELL_SIZE = 10 # Size of each cell in the debug grid
DEBUG_DELAY_MS = 100 # Delay between ALGORITHM STEPS in debug mode (ms). 0 for instant.

# --- Drawing Algorithms (Midpoint/Bresenham variations) ---

class CurveDrawer:
    """Handles plotting pixels on main and debug canvases."""
    def __init__(self, main_canvas, debug_canvas, debug_origin_offset):
        self.main_canvas = main_canvas
        self.debug_canvas = debug_canvas
        self.debug_origin_x, self.debug_origin_y = debug_origin_offset
        # Определяем активность debug режима сразу при создании
        self.debug_active = self.debug_canvas is not None and self.debug_canvas.winfo_exists()
        # Убираем буфер шагов
        # self.steps_buffer = []

    def _plot_on_main(self, x, y, color="black"):
        """Plots a single 'pixel' on the main canvas."""
        # Use create_rectangle for a 1x1 pixel or create_oval
        if self.main_canvas: # Проверка, что канвас существует
            self.main_canvas.create_rectangle(x, y, x+1, y+1, fill=color, outline=color)

    def _plot_on_debug(self, grid_x, grid_y, step_info=""):
        """Highlights a cell on the debug grid."""
        if not self.debug_active:
            return

        # Convert algorithm grid coordinates to debug canvas coordinates
        canvas_x = self.debug_origin_x + grid_x * DEBUG_CELL_SIZE
        canvas_y = self.debug_origin_y - grid_y * DEBUG_CELL_SIZE # Y is inverted

        # Ensure it's within reasonable bounds for the debug grid display
        if abs(grid_x) * DEBUG_CELL_SIZE > DEBUG_GRID_SIZE // 2 or \
           abs(grid_y) * DEBUG_CELL_SIZE > DEBUG_GRID_SIZE // 2:
           return # Skip plotting if too far from origin

        # Проверка, что debug канвас существует
        if self.debug_canvas and self.debug_canvas.winfo_exists():
            self.debug_canvas.create_rectangle(
                canvas_x - DEBUG_CELL_SIZE // 2, canvas_y - DEBUG_CELL_SIZE // 2,
                canvas_x + DEBUG_CELL_SIZE // 2, canvas_y + DEBUG_CELL_SIZE // 2,
                fill="red", outline="darkred", tags="debug_step"
            )

    def plot_pixel(self, center_x, center_y, x, y, color="black", step_info=""):
        """ Plots a single point relative to the center on both canvases IMMEDIATELY. """
        main_x, main_y = center_x + x, center_y + y
        self._plot_on_main(main_x, main_y, color)
        self._plot_on_debug(x, y, step_info)
        # self.steps_buffer.append((center_x, center_y, x, y, color, step_info))

    # Функции plot_..._points вызывают plot_pixel для каждой симметричной точки
    def plot_circle_points(self, xc, yc, x, y, color="black"):
        """Plots all 8 symmetric points for a circle centered at (xc, yc)."""
        points = [
            (x, y), (-x, y), (x, -y), (-x, -y),
            (y, x), (-y, x), (y, -x), (-y, -x)
        ]
        for dx, dy in points:
             self.plot_pixel(xc, yc, dx, dy, color)

    def plot_ellipse_points(self, xc, yc, x, y, color="black"):
        """Plots all 4 symmetric points for an ellipse centered at (xc, yc)."""
        points = [(x, y), (-x, y), (x, -y), (-x, -y)]
        for dx, dy in points:
             self.plot_pixel(xc, yc, dx, dy, color)

    def plot_hyperbola_points(self, xc, yc, x, y, color="black"):
        """Plots symmetric points for a hyperbola (x^2/a^2 - y^2/b^2 = 1) centered at (xc, yc).
           Assumes (x, y) is in the first quadrant relative to the center.
        """
        # Plots points for both branches based on the calculated point (x,y) for the right branch, first quadrant
        points = [
            (x, y), (x, -y),   # Right branch (upper and lower)
            (-x, y), (-x, -y) # Left branch (upper and lower)
        ]
        for dx, dy in points:
             self.plot_pixel(xc, yc, dx, dy, color)

    def plot_parabola_points(self, vx, vy, x, y, orientation="y=ax^2", color="black"):
        """Plots symmetric points for a parabola with vertex (vx, vy)."""
        points = []
        if orientation == "y=ax^2":
            # For y=ax^2, symmetry is across the y-axis (relative to vertex)
            points = [(x, y), (-x, y)]
        elif orientation == "x=ay^2":
             # For x=ay^2, symmetry is across the x-axis (relative to vertex)
             points = [(x, y), (x, -y)]
        else:
             points = [(x,y)] # Default if orientation unknown

        # Filter duplicate points if x or y is 0 for the symmetric pair
        unique_points = []
        seen = set()
        for p in points:
            if p not in seen:
                unique_points.append(p)
                seen.add(p)

        for dx, dy in unique_points:
             # Plot relative to vertex
             self.plot_pixel(vx, vy, dx, dy, color)

    # Убираем finalize_drawing, т.к. буфера нет
    # def finalize_drawing(self): ...

    def step_delay(self):
        """Introduces a delay and forces canvas update if debug mode is active."""
        if self.debug_active and DEBUG_DELAY_MS > 0:
            # Force update on both canvases to show the plotted pixel immediately
            if self.main_canvas and self.main_canvas.winfo_exists():
                self.main_canvas.update() # or update_idletasks()
            if self.debug_canvas and self.debug_canvas.winfo_exists():
                self.debug_canvas.update() # or update_idletasks()
            # Pause execution - WARNING: Freezes GUI
            time.sleep(DEBUG_DELAY_MS / 1000.0)


# --- Midpoint Algorithms ---

def draw_circle_midpoint(drawer, xc, yc, r):
    """Draws a circle using the Midpoint algorithm."""
    if r < 0: return
    x = 0
    y = r
    p = 1 - r

    # Plot initial point and symmetric points
    drawer.plot_circle_points(xc, yc, x, y)
    drawer.step_delay() # <-- Add delay after plotting step

    while x < y:
        x += 1
        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1

        drawer.plot_circle_points(xc, yc, x, y)
        drawer.step_delay() # <-- Add delay after plotting step

def draw_ellipse_midpoint(drawer, xc, yc, rx, ry):
    """Draws an ellipse using the Midpoint algorithm."""
    if rx <= 0 or ry <= 0: return
    rx2 = rx * rx
    ry2 = ry * ry
    two_rx2 = 2 * rx2
    two_ry2 = 2 * ry2

    # --- Region 1 ---
    x = 0
    y = ry
    p = round(ry2 - rx2 * ry + 0.25 * rx2)
    px = 0
    py = two_rx2 * y

    drawer.plot_ellipse_points(xc, yc, x, y)
    drawer.step_delay() # <-- Add delay

    while px < py:
        x += 1
        px += two_ry2
        if p < 0:
            p += ry2 + px
        else:
            y -= 1
            py -= two_rx2
            p += ry2 + px - py
        drawer.plot_ellipse_points(xc, yc, x, y)
        drawer.step_delay() # <-- Add delay

    # --- Region 2 ---
    p = round(ry2 * (x + 0.5)**2 + rx2 * (y - 1)**2 - rx2 * ry2)

    while y >= 0: # Change condition to y >= 0 to include the last point
        y -= 1
        py -= two_rx2
        if p > 0:
            p += rx2 - py
        else:
            x += 1
            px += two_ry2
            p += rx2 - py + px
        drawer.plot_ellipse_points(xc, yc, x, y)
        drawer.step_delay() # <-- Add delay

def draw_hyperbola_midpoint(drawer, xc, yc, a, b):
    """Draws a hyperbola (x^2/a^2 - y^2/b^2 = 1) using direct calculation."""
    if a <= 0 or b <= 0: return

    a2 = a * a
    b2 = b * b

    # --- Используем прямое вычисление точек ---
    # Рисуем только правую ветвь, первая координатная четверть (x>0, y>0)
    # plot_hyperbola_points затем отразит их симметрично для полной картины
    print(f"Drawing hyperbola using direct calculation (not Midpoint algorithm steps)")

    # Установим разумный предел отрисовки, чтобы не уходить в бесконечность
    x_limit_canvas = CANVAS_WIDTH * 1.5 # Рисуем немного за пределы видимой части
    y_limit_canvas = CANVAS_HEIGHT * 1.5

    last_plot_x, last_plot_y = -1, -1

    # Итерация по X для основной части ветви
    x_rel = a
    while xc + x_rel < x_limit_canvas :
        y_rel_exact = b * math.sqrt(max(0, (x_rel * x_rel / a2) - 1.0))
        y_rel = round(y_rel_exact)

        if yc + y_rel > y_limit_canvas and yc - y_rel < -y_limit_canvas : # Выход если ушли далеко по Y
             break

        # Избегаем повторной отрисовки одной и той же точки (особенно в начале)
        if x_rel != last_plot_x or y_rel != last_plot_y:
             drawer.plot_hyperbola_points(xc, yc, x_rel, y_rel)
             drawer.step_delay() # <-- Задержка после отрисовки симметричных точек
             last_plot_x, last_plot_y = x_rel, y_rel

        # Увеличиваем X. Шаг может быть адаптивным, но для простоты +1
        x_rel += 1

    # Можно добавить итерацию по Y для участков, где кривая идет почти вертикально,
    # но для элементарного редактора текущий подход достаточен для демонстрации формы.


def draw_parabola_midpoint(drawer, vx, vy, p_focus, orientation="y=ax^2"):
    """Draws a parabola using Midpoint."""
    if p_focus == 0: return # Degenerate case
    p_abs = abs(p_focus) # Algorithm usually uses distance

    if orientation == "y=ax^2":
        # y = x^2 / (4p) -> x^2 = 4py
        x = 0
        y = 0
        # Decision parameter F(1, 0.5) = 1 - 4*p*0.5 = 1 - 2p
        d = 1 - 2 * p_abs
        drawer.plot_parabola_points(vx, vy, x, y, orientation)
        drawer.step_delay()
        limit_y = CANVAS_HEIGHT * 1.5 # Arbitrary limit

        # Region 1: slope |m| < 1 (iterate x)
        # Condition where slope = 1: dy/dx = 2x/(4p) = 1 -> x = 2p
        while 2 * x < 4 * p_abs and y < limit_y :
            x += 1
            if d < 0: # Choose E (East)
                d += 2 * x + 1
            else: # Choose NE (North-East)
                y += 1
                d += 2 * x + 1 - 4 * p_abs
            drawer.plot_parabola_points(vx, vy, x, y, orientation)
            drawer.step_delay()

        # Region 2: slope |m| >= 1 (iterate y)
        # Decision parameter F(x+0.5, y+1) = (x+0.5)^2 - 4*p*(y+1)
        # Simplified relative decision: check F(x+1, y+1) vs F(x, y+1)?
        # Let's recalculate d based on midpoint F(x+0.5, y+1) relative to last point
        d = (x + 0.5)**2 - 4*p_abs*(y+1) # Needs careful check

        while y < limit_y: # Iterate until out of bounds
            y += 1
            if d <= 0: # Midpoint inside or on curve - Choose NE
                x += 1
                # Update d based on moving from (x,y) to (x+1, y+1)
                # d_new = d_old + (2x+1) - 4p --> Check derivation
                d += 2*x + 1 - 4*p_abs # Simplified update based on F(x+1.5, y+1) - F(x+0.5, y+1)? No.
                # d_new = F(x+1+0.5, y+1+1) ?? Complex. Use relative test.
                # d = (x+0.5)**2 - 4*p_abs*(y+1) # Recalculate instead of incremental (less efficient but safer)
            else: # Midpoint outside - Choose N
                 # Update d based on moving from (x,y) to (x, y+1)
                 # d_new = d_old - 4p
                 d -= 4*p_abs # Simplified update based on F(x+0.5, y+1+1) - F(x+0.5, y+1)

            # Recalculate d to be safe, midpoint approach detail is tricky
            d = (x + 0.5)**2 - 4*p_abs*(y+1)

            drawer.plot_parabola_points(vx, vy, x, y, orientation)
            drawer.step_delay()

    elif orientation == "x=ay^2":
        # x = y^2 / (4p) -> y^2 = 4px
        x = 0
        y = 0
        # Decision param F(0.5, 1) = 1 - 4*p*0.5 = 1 - 2p
        d = 1 - 2 * p_abs
        drawer.plot_parabola_points(vx, vy, x, y, orientation)
        drawer.step_delay()
        limit_x = CANVAS_WIDTH * 1.5

        # Region 1: slope |m| > 1 (iterate y)
        # Condition slope = 1: dx/dy = 2y/(4p) = 1 -> y = 2p
        while 2 * y < 4 * p_abs and x < limit_x:
            y += 1
            if d < 0: # Choose N (North)
                d += 2 * y + 1
            else: # Choose NE
                x += 1
                d += 2 * y + 1 - 4 * p_abs
            drawer.plot_parabola_points(vx, vy, x, y, orientation)
            drawer.step_delay()

        # Region 2: slope |m| <= 1 (iterate x)
        # Decision param F(x+1, y+0.5) = (y+0.5)^2 - 4p(x+1)
        d = (y + 0.5)**2 - 4*p_abs*(x+1)

        while x < limit_x:
            x += 1
            if d <= 0: # Midpoint inside or on curve - Choose NE
                y += 1
                d += 2*y + 1 - 4*p_abs # Update based on moving NE
            else: # Midpoint outside - Choose E
                 d -= 4 * p_abs # Update based on moving E

            # Recalculate d for safety
            d = (y + 0.5)**2 - 4*p_abs*(x+1)

            drawer.plot_parabola_points(vx, vy, x, y, orientation)
            drawer.step_delay()
    else:
        print("Unsupported parabola orientation")


# --- Main Application Class ---

class GraphicsEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Second Order Curve Editor")
        # Adjust size slightly if needed
        self.geometry(f"{CANVAS_WIDTH+60}x{CANVAS_HEIGHT+110}")

        # State variables
        self.current_mode = None
        self.click_points = []
        self.debug_window = None
        self.debug_canvas = None
        # self.debug_grid_drawn = False # Not strictly needed anymore
        self.debug_origin_offset = (DEBUG_GRID_SIZE // 2, DEBUG_GRID_SIZE // 2)

        # UI Elements
        self._setup_ui()
        # Добавим обработчик закрытия основного окна
        self.protocol("WM_DELETE_WINDOW", self._on_closing)


    def _setup_ui(self):
        # --- Menu ---
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Clear Canvas", command=self.clear_canvas)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing) # Use consistent closing logic
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        curves_menu = tk.Menu(self.menu_bar, tearoff=0)
        # Связываем команды с _set_mode
        curves_menu.add_command(label="Circle", command=lambda: self._set_mode('circle'))
        curves_menu.add_command(label="Ellipse", command=lambda: self._set_mode('ellipse'))
        curves_menu.add_command(label="Hyperbola", command=lambda: self._set_mode('hyperbola'))
        curves_menu.add_command(label="Parabola", command=lambda: self._set_mode('parabola'))
        self.menu_bar.add_cascade(label="Curves", menu=curves_menu)

        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Toggle Debug Window", command=self._toggle_debug_window)
        self.menu_bar.add_cascade(label="View", menu=view_menu)

        # --- Toolbar ---
        toolbar = ttk.Frame(self, padding="5 5 5 5")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(toolbar, text="Lines Second Order:").pack(side=tk.LEFT, padx=5)
        # Связываем кнопки с _set_mode
        ttk.Button(toolbar, text="Circle", command=lambda: self._set_mode('circle')).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Ellipse", command=lambda: self._set_mode('ellipse')).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Hyperbola", command=lambda: self._set_mode('hyperbola')).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Parabola", command=lambda: self._set_mode('parabola')).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Clear", command=self.clear_canvas).pack(side=tk.LEFT, padx=10)

        # --- Main Canvas ---
        self.main_canvas = tk.Canvas(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white", relief=tk.SUNKEN, borderwidth=1)
        self.main_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.main_canvas.bind("<Button-1>", self._on_canvas_click)
        # Optional: Bind right-click to cancel current point selection
        self.main_canvas.bind("<Button-3>", self._cancel_clicks)


        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2 5 2 5")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready. Select a curve type from the menu or toolbar.")

    def _set_mode(self, mode):
        self.current_mode = mode
        self.click_points = []
        # Очистим маркеры от предыдущего режима
        self.main_canvas.delete("click_marker")
        instructions = {
            'circle': "Click 1: Center, Click 2: Point on circumference",
            'ellipse': "Click 1: Center, Click 2: Point on X-axis extent, Click 3: Point on Y-axis extent",
            'hyperbola': "Click 1: Center, Click 2: Vertex (defines 'a'), Click 3: Point defining 'b' distance on conjugate axis",
            'parabola': "Click 1: Vertex, Click 2: Focus point (defines 'p' and orientation)",
        }
        self.status_var.set(f"Mode: {mode.capitalize()}. {instructions.get(mode, '')} (Right-click to cancel)")

    def _on_canvas_click(self, event):
        if not self.current_mode:
            self.status_var.set("Select a curve type first!")
            return

        x, y = event.x, event.y
        self.click_points.append((x, y))
        self._draw_click_marker(x, y, len(self.click_points)) # Show feedback with number
        self.status_var.set(f"Clicked point {len(self.click_points)} at ({x}, {y}) for {self.current_mode}. (Right-click to cancel)")

        # Check if enough points are collected for the current mode
        required_points = {
            'circle': 2, 'ellipse': 3, 'hyperbola': 3, 'parabola': 2
        }

        if len(self.click_points) == required_points.get(self.current_mode):
            # Очистим маркеры перед рисованием основной фигуры
            self.main_canvas.delete("click_marker")
            self._draw_selected_curve()
            self.click_points = [] # Reset for next curve
            # Keep the mode active, update status
            self._set_mode(self.current_mode) # Refresh instructions
        elif len(self.click_points) > required_points.get(self.current_mode, 0):
            # Should not happen with reset, but as safety
             self.click_points = []
             self.main_canvas.delete("click_marker")
             self.status_var.set(f"Too many points clicked. Resetting for {self.current_mode}. Click point 1.")
             self._set_mode(self.current_mode) # Refresh instructions


    def _cancel_clicks(self, event=None):
         """Cancels the current point selection process."""
         if self.click_points:
             self.click_points = []
             self.main_canvas.delete("click_marker")
             mode = self.current_mode if self.current_mode else "None"
             self.status_var.set(f"Point selection cancelled. Mode: {mode.capitalize()}. Click point 1.")
             # Ensure instructions are reset if mode was active
             if self.current_mode:
                  self._set_mode(self.current_mode)


    def _draw_click_marker(self, x, y, number):
         """Draws a small temporary marker where the user clicked, with number."""
         marker_tag = f"click_marker_{number}" # Unique tag for each marker
         # Consider removing only the *last* marker if user re-clicks? No, keep all visible.
         self.main_canvas.create_oval(x-4, y-4, x+4, y+4, outline="blue", width=1, tags=("click_marker", marker_tag))
         self.main_canvas.create_text(x, y, text=str(number), fill="blue", font=("Arial", 8), tags=("click_marker", marker_tag))

    def _get_drawer(self):
        """Creates a CurveDrawer instance with current debug canvas state."""
        # Clear previous debug steps ONLY when starting a NEW curve drawing
        if self.debug_canvas and self.debug_canvas.winfo_exists():
            self.debug_canvas.delete("debug_step") # Clear old steps but keep grid
            # Ensure grid is drawn if debug window was just opened
            if not self.debug_canvas.find_withtag("grid_line"):
                 self._draw_debug_grid()


        # Check if debug window exists when creating drawer
        current_debug_canvas = self.debug_canvas if (self.debug_window and self.debug_window.winfo_exists()) else None

        return CurveDrawer(
            self.main_canvas,
            current_debug_canvas, # Pass current state
            self.debug_origin_offset
        )

    def _draw_selected_curve(self):
        if not self.current_mode or not self.click_points:
            return

        drawer = self._get_drawer() # Get drawer with current debug state
        pts = self.click_points

        try:
            # --- Circle ---
            if self.current_mode == 'circle' and len(pts) == 2:
                xc, yc = pts[0]
                xp, yp = pts[1]
                r = round(math.hypot(xp - xc, yp - yc)) # Use hypot for distance
                if r == 0:
                     messagebox.showwarning("Input Error", "Radius cannot be zero.")
                     return
                self.status_var.set(f"Drawing Circle: Center=({xc},{yc}), Radius={r}")
                draw_circle_midpoint(drawer, xc, yc, r)

            # --- Ellipse ---
            elif self.current_mode == 'ellipse' and len(pts) == 3:
                xc, yc = pts[0]
                x_pt, y_pt1 = pts[1] # Point defining rx-ish distance
                x_pt2, y_pt2 = pts[2] # Point defining ry-ish distance
                # Use distance from center for radii - assumes orthogonal clicks
                rx = round(math.hypot(x_pt - xc, y_pt1 - yc))
                ry = round(math.hypot(x_pt2 - xc, y_pt2 - yc))
                # More robust: Project onto axes relative to center? Or just use simple dist:
                rx_alt = round(abs(x_pt - xc)) # Simplest interpretation
                ry_alt = round(abs(y_pt2 - yc)) # Simplest interpretation
                # Lets use the simpler interpretation for clarity of input expectation
                rx, ry = rx_alt, ry_alt

                if rx == 0 or ry == 0:
                    messagebox.showwarning("Input Error", "Ellipse radii cannot be zero.")
                    return
                self.status_var.set(f"Drawing Ellipse: Center=({xc},{yc}), Rx={rx}, Ry={ry}")
                draw_ellipse_midpoint(drawer, xc, yc, rx, ry)

            # --- Hyperbola ---
            elif self.current_mode == 'hyperbola' and len(pts) == 3:
                 xc, yc = pts[0]
                 xv, yv = pts[1] # Vertex
                 xb_pt, yb_pt = pts[2] # Point defining 'b' distance

                 # Assume standard orientation (horizontal opening x^2/a^2 - y^2/b^2 = 1)
                 # 'a' is distance from center to vertex (along transverse axis)
                 a = round(math.hypot(xv - xc, yv - yc))
                 # Check if vertex is primarily horizontal or vertical from center
                 if abs(xv - xc) < abs(yv - yc):
                      messagebox.showwarning("Orientation", "Assuming horizontal hyperbola. Vertex seems vertical?")
                      # Could add logic to switch orientation based on vertex position

                 # 'b' distance is defined by the third point's distance from the center *along the conjugate axis*.
                 # Simple approach: assume 3rd point is roughly on the conjugate axis.
                 b = round(math.hypot(xb_pt - xc, yb_pt - yc))
                 # A better way: Calculate distance from 3rd point to the *transverse axis line*.
                 # But let's stick to simple distance for now. User needs to click appropriately.
                 b_alt = round(abs(yb_pt-yc)) # Simplest if assuming horizontal opening

                 # Let's use the direct distances 'a' from vertex click, 'b' from third click
                 a = round(math.hypot(xv-xc, yv-yc))
                 b = round(math.hypot(xb_pt-xc, yb_pt-yc))
                 # Ensure a refers to the distance along the axis from center to *vertex*
                 a = round(abs(xv - xc)) # Re-calculate 'a' as horizontal distance to vertex for x^2/a^2..

                 if a == 0 or b == 0:
                     messagebox.showwarning("Input Error", "Hyperbola 'a' and 'b' must be non-zero.")
                     return
                 self.status_var.set(f"Drawing Hyperbola: Center=({xc},{yc}), a={a}, b={b} (direct calculation)")
                 draw_hyperbola_midpoint(drawer, xc, yc, a, b) # Uses direct calculation version

            # --- Parabola ---
            elif self.current_mode == 'parabola' and len(pts) == 2:
                 vx, vy = pts[0] # Vertex
                 fx, fy = pts[1] # Focus

                 dx = fx - vx
                 dy = fy - vy

                 if dx == 0 and dy == 0:
                      messagebox.showwarning("Input Error", "Vertex and Focus cannot be the same point.")
                      return

                 # Determine orientation and signed focus distance 'p' for formula
                 # Use p_algo for the absolute distance needed by the midpoint algorithm
                 p_algo = 0
                 orientation = None

                 # If difference is primarily vertical -> opens vertically (y=ax^2 type)
                 if abs(dy) >= abs(dx):
                     orientation = "y=ax^2"
                     # Algorithm needs distance |VF| along the axis of symmetry
                     p_algo = round(abs(dy))
                     # For formula: 4p = distance^2 / other_coord_diff? No.
                     # For formula y=x^2/(4p) relative to vertex, p is distance V-F if F=(vx, vy+p)
                     # p_formula = dy # Signed distance
                 # If difference is primarily horizontal -> opens horizontally (x=ay^2 type)
                 else: # abs(dx) > abs(dy)
                     orientation = "x=ay^2"
                     p_algo = round(abs(dx)) # Algorithm needs |VF| along axis
                     # p_formula = dx # Signed distance for x=y^2/(4p)

                 if p_algo == 0:
                      # This case should be caught by dx==0 and dy==0, but double check
                      messagebox.showwarning("Input Error", "Focus distance 'p' calculated as zero.")
                      return

                 self.status_var.set(f"Drawing Parabola: V=({vx},{vy}), p={p_algo}, Orient={orientation}")
                 draw_parabola_midpoint(drawer, vx, vy, p_algo, orientation) # Pass absolute p needed by algo

            else:
                # This should not happen if point collection logic is correct
                print(f"State error: Incorrect points ({len(pts)}) for mode {self.current_mode}")
                self._cancel_clicks() # Reset state

            # No need for finalize_drawing anymore
            # drawer.finalize_drawing()

        except Exception as e:
            messagebox.showerror("Drawing Error", f"An error occurred during drawing:\n{e}")
            print(f"Error drawing {self.current_mode}: {e}") # Log detailed error
            import traceback
            traceback.print_exc() # Print stack trace to console
        finally:
            # Clean up markers AFTER drawing attempt (success or fail)
             self.main_canvas.delete("click_marker")
             # Do NOT reset mode or points here, handled by _on_canvas_click success


    def clear_canvas(self):
        self.main_canvas.delete("all")
        # Also clear markers if any were left
        self.click_points = []
        if self.debug_canvas and self.debug_canvas.winfo_exists():
            self.debug_canvas.delete("debug_step") # Clear steps but keep grid
        self.status_var.set("Canvas cleared. Select a curve type.")
        # Keep current mode active or reset? Let's keep it active.
        if self.current_mode:
             self._set_mode(self.current_mode) # Refresh instructions


    def _toggle_debug_window(self):
        if self.debug_window and self.debug_window.winfo_exists():
            # If exists, destroy it
            self._on_debug_close() # Use the close handler
        else:
            # If not exists, create it
            self._create_debug_window()
            self.status_var.set("Debug window opened. Drawing will be step-by-step.")


    def _create_debug_window(self):
        if self.debug_window and self.debug_window.winfo_exists():
            self.debug_window.lift() # Bring to front if already exists but hidden
            return

        self.debug_window = tk.Toplevel(self)
        self.debug_window.title("Debug View - Algorithm Steps")
        self.debug_window.geometry(f"{DEBUG_GRID_SIZE + 40}x{DEBUG_GRID_SIZE + 60}") # Extra space for label
        # Make it non-modal
        self.debug_window.transient(self)

        # Add label about GUI freeze
        ttk.Label(self.debug_window, text="Note: GUI may freeze during step delays.", font=("Arial", 8)).pack(pady=(5,0))

        self.debug_canvas = tk.Canvas(self.debug_window, width=DEBUG_GRID_SIZE, height=DEBUG_GRID_SIZE, bg="lightgrey")
        self.debug_canvas.pack(padx=10, pady=10)

        # Draw the grid immediately
        self._draw_debug_grid()

        # Handle closing the debug window via 'X' button
        self.debug_window.protocol("WM_DELETE_WINDOW", self._on_debug_close)

    def _on_debug_close(self):
         # Called when debug window 'X' is clicked or toggled off
         if self.debug_window and self.debug_window.winfo_exists():
             self.debug_window.destroy()
         # Crucially, reset the references
         self.debug_window = None
         self.debug_canvas = None
         self.status_var.set("Debug window closed.")


    def _draw_debug_grid(self):
        if not self.debug_canvas: return
        self.debug_canvas.delete("grid_line") # Clear only grid lines

        center_x, center_y = self.debug_origin_offset
        step = DEBUG_CELL_SIZE

        # Draw grid lines
        for i in range(step, DEBUG_GRID_SIZE // 2 + step, step):
             # Positive X lines
            self.debug_canvas.create_line(center_x + i, 0, center_x + i, DEBUG_GRID_SIZE, fill="grey", tags="grid_line", dash=(1, 3))
            # Negative X lines
            self.debug_canvas.create_line(center_x - i, 0, center_x - i, DEBUG_GRID_SIZE, fill="grey", tags="grid_line", dash=(1, 3))
            # Positive Y lines (Canvas Y is down)
            self.debug_canvas.create_line(0, center_y - i, DEBUG_GRID_SIZE, center_y - i, fill="grey", tags="grid_line", dash=(1, 3))
            # Negative Y lines
            self.debug_canvas.create_line(0, center_y + i, DEBUG_GRID_SIZE, center_y + i, fill="grey", tags="grid_line", dash=(1, 3))

        # Draw thicker axis lines
        self.debug_canvas.create_line(center_x, 0, center_x, DEBUG_GRID_SIZE, fill="black", width=1, tags="grid_line") # Y-axis
        self.debug_canvas.create_line(0, center_y, DEBUG_GRID_SIZE, center_y, fill="black", width=1, tags="grid_line") # X-axis

        # Add origin label
        self.debug_canvas.create_text(center_x + 2, center_y - 2, text="(0,0)", anchor=tk.NW, font=("Arial", 7, "italic"), fill="black", tags="grid_line")


    def _on_closing(self):
        if self.debug_window and self.debug_window.winfo_exists():
            self.debug_window.destroy()
        self.destroy() # Close the main window


# --- Run the Application ---
if __name__ == "__main__":
    app = GraphicsEditor()
    app.mainloop()
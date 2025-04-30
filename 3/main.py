import tkinter as tk
from tkinter import messagebox, Frame, Button, Menu, Canvas, Label, StringVar, Radiobutton, SUNKEN, W
import math
import matrix_utils as mu

# --- Константы (остаются прежними) ---
CONTROL_POINT_RADIUS = 4
SNAP_DISTANCE = 10
NUM_STEPS = 30

# --- Классы кривых (HermiteCurve, BezierCurve, BSplineCurve) - БЕЗ ИЗМЕНЕНИЙ ---
# ... (вставьте сюда полные классы BaseCurve, HermiteCurve, BezierCurve, BSplineCurve из предыдущего ответа) ...
class BaseCurve:
    def __init__(self, points, curve_type):
        self.points = points # Control points (list of tuples (x, y))
        self.curve_type = curve_type
        self.calculated_points = [] # Cache calculated points for drawing

    def draw(self, canvas, color="black", width=2):
        if not self.calculated_points:
            self.calculate_curve_points()

        if len(self.calculated_points) > 1:
            # Use tuple unpacking for create_line points
            flat_points = [coord for point in self.calculated_points for coord in point]
            canvas.create_line(flat_points, fill=color, width=width, tags="curve", smooth=False) # smooth=True can look nice

    def draw_control_points(self, canvas, color="red", outline="black"):
        for i, p in enumerate(self.points):
            x0, y0 = p[0] - CONTROL_POINT_RADIUS, p[1] - CONTROL_POINT_RADIUS
            x1, y1 = p[0] + CONTROL_POINT_RADIUS, p[1] + CONTROL_POINT_RADIUS
            # Store index info in tag for easy retrieval
            canvas.create_oval(x0, y0, x1, y1, fill=color, outline=outline, tags=("control_point", f"cp_{id(self)}_{i}"))

    def draw_control_polygon(self, canvas, color="gray", dash=(2, 2)):
         if len(self.points) > 1:
            flat_points = [coord for point in self.points for coord in point]
            canvas.create_line(flat_points, fill=color, dash=dash, tags="control_polygon")

    def calculate_curve_points(self, num_steps=NUM_STEPS):
        # Implemented by subclasses
        raise NotImplementedError

    def get_point_at_t(self, t):
         # Implemented by subclasses
        raise NotImplementedError

    def update_point(self, index, new_pos):
        if 0 <= index < len(self.points):
            self.points[index] = new_pos
            self.calculated_points = [] # Invalidate cache

    def get_start_point(self):
        # Needs specific implementation per curve type!
        # For Bezier/Hermite (4 points), it's points[0]
        # For B-Spline, it's the start of the first segment Q(0)
        if self.curve_type in ['hermite', 'bezier'] and len(self.points) == 4:
            return self.points[0]
        elif self.curve_type == 'bspline' and len(self.points) >= 4:
             if not self.calculated_points: self.calculate_curve_points()
             return self.calculated_points[0] if self.calculated_points else None
        return self.points[0] if self.points else None


    def get_end_point(self):
         # Needs specific implementation per curve type!
         # For Bezier/Hermite (4 points), it's points[3]
         # For B-Spline, it's the end of the last segment Q(1)
        if self.curve_type in ['hermite', 'bezier'] and len(self.points) == 4:
            return self.points[3]
        elif self.curve_type == 'bspline' and len(self.points) >= 4:
             if not self.calculated_points: self.calculate_curve_points()
             return self.calculated_points[-1] if self.calculated_points else None
        return self.points[-1] if self.points else None


class HermiteCurve(BaseCurve):
    M_H = [[2, -2, 1, 1], [-3, 3, -2, -1], [0, 0, 1, 0], [1, 0, 0, 0]]

    def __init__(self, points):
        if len(points) != 4:
            raise ValueError("Hermite curve requires exactly 4 control points.")
        super().__init__(points, 'hermite')
        self._update_geometry_vectors()

    def _update_geometry_vectors(self):
        """Helper to recalculate geometry vectors."""
        self.P1 = self.points[0]
        self.P4 = self.points[3]
        # Use safe subtraction in case points are identical initially during drag
        self.R1 = mu.subtract_vectors(self.points[1], self.points[0])
        self.R4 = mu.subtract_vectors(self.points[3], self.points[2])
        self.G_H_x = [self.P1[0], self.P4[0], self.R1[0], self.R4[0]]
        self.G_H_y = [self.P1[1], self.P4[1], self.R1[1], self.R4[1]]

    def calculate_curve_points(self, num_steps=NUM_STEPS):
        self.calculated_points = []
        for i in range(num_steps + 1):
            t = i / num_steps
            T = [t**3, t**2, t, 1]
            TMH = mu.multiply_vector_matrix(T, self.M_H)
            x = sum(tmh * gx for tmh, gx in zip(TMH, self.G_H_x))
            y = sum(tmh * gy for tmh, gy in zip(TMH, self.G_H_y))
            self.calculated_points.append((x, y))
        return self.calculated_points

    def update_point(self, index, new_pos):
        super().update_point(index, new_pos)
        self._update_geometry_vectors() # Recalculate G vectors after point update
        self.calculated_points = [] # Invalidate cache


class BezierCurve(BaseCurve):
    M_B = [[-1, 3, -3, 1], [3, -6, 3, 0], [-3, 3, 0, 0], [1, 0, 0, 0]]

    def __init__(self, points):
        if len(points) != 4:
            raise ValueError("Cubic Bezier curve requires exactly 4 control points.")
        super().__init__(points, 'bezier')
        self._update_geometry_vectors()

    def _update_geometry_vectors(self):
        """Helper to recalculate geometry vectors."""
        self.G_B_x = [p[0] for p in self.points]
        self.G_B_y = [p[1] for p in self.points]

    def calculate_curve_points(self, num_steps=NUM_STEPS):
        self.calculated_points = []
        for i in range(num_steps + 1):
            t = i / num_steps
            T = [t**3, t**2, t, 1]
            TMB = mu.multiply_vector_matrix(T, self.M_B)
            x = sum(tmb * gx for tmb, gx in zip(TMB, self.G_B_x))
            y = sum(tmb * gy for tmb, gy in zip(TMB, self.G_B_y))
            self.calculated_points.append((x, y))
        return self.calculated_points

    def update_point(self, index, new_pos):
        super().update_point(index, new_pos)
        self._update_geometry_vectors()
        self.calculated_points = []


class BSplineCurve(BaseCurve):
    # Uniform Cubic B-Spline Matrix
    M_BS = [
        [-1/6,  3/6, -3/6, 1/6],
        [ 3/6, -6/6,  3/6, 0],
        [-3/6,  0,    3/6, 0],
        [ 1/6,  4/6,  1/6, 0]
    ]

    def __init__(self, points):
        if len(points) < 4:
            raise ValueError("Uniform Cubic B-Spline requires at least 4 control points.")
        # Ensure points are mutable list
        super().__init__(list(points), 'bspline')

    def calculate_curve_points(self, num_steps=NUM_STEPS):
        self.calculated_points = []
        if len(self.points) < 4:
             return self.calculated_points # Not enough points to draw anything

        num_segments = len(self.points) - 3

        # Estimate steps per segment to keep density somewhat constant
        steps_per_segment = max(1, num_steps // num_segments) if num_segments > 0 else num_steps

        for seg_idx in range(num_segments):
            # Control points for this segment
            p0, p1, p2, p3 = self.points[seg_idx : seg_idx + 4]
            G_BS_x = [p0[0], p1[0], p2[0], p3[0]]
            G_BS_y = [p0[1], p1[1], p2[1], p3[1]]

            # Calculate points within this segment (t from 0 to 1)
            is_last_segment = (seg_idx == num_segments - 1)
            # Add the final point only for the very last segment
            num_steps_this_segment = steps_per_segment + (1 if is_last_segment else 0)

            for i in range(num_steps_this_segment):
                 # Ensure t goes from 0 to 1 inclusive for the last point if needed
                t = i / steps_per_segment
                if t > 1.0: t = 1.0

                T = [t**3, t**2, t, 1]
                TMBS = mu.multiply_vector_matrix(T, self.M_BS)
                x = sum(tmbs * gx for tmbs, gx in zip(TMBS, G_BS_x))
                y = sum(tmbs * gy for tmbs, gy in zip(TMBS, G_BS_y))

                # Add point if it's the very first point, or not identical to the last one
                # (Avoids duplicates at segment joins due to floating point)
                if not self.calculated_points or (abs(x - self.calculated_points[-1][0]) > 1e-6 or abs(y - self.calculated_points[-1][1]) > 1e-6):
                     self.calculated_points.append((x, y))
                 # Handle the case where the loop finishes exactly on the duplicate point
                elif i == num_steps_this_segment -1 and is_last_segment and len(self.calculated_points) > 0:
                    # Ensure the very last point is included if it was skipped
                    if (abs(x - self.calculated_points[-1][0]) > 1e-6 or abs(y - self.calculated_points[-1][1]) > 1e-6):
                        self.calculated_points.append((x,y))


        # If only 4 points, calculated_points might be empty if steps_per_segment is 0. Draw single segment.
        if not self.calculated_points and len(self.points) == 4:
             p0, p1, p2, p3 = self.points[0:4]
             G_BS_x = [p0[0], p1[0], p2[0], p3[0]]
             G_BS_y = [p0[1], p1[1], p2[1], p3[1]]
             for i in range(num_steps + 1):
                 t = i / num_steps
                 T = [t**3, t**2, t, 1]
                 TMBS = mu.multiply_vector_matrix(T, self.M_BS)
                 x = sum(tmbs * gx for tmbs, gx in zip(TMBS, G_BS_x))
                 y = sum(tmbs * gy for tmbs, gy in zip(TMBS, G_BS_y))
                 self.calculated_points.append((x, y))


        return self.calculated_points

    def update_point(self, index, new_pos):
        super().update_point(index, new_pos)
        # Recalculation happens on demand via calculate_curve_points


# --- Main Application Class ---
class CurveEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parametric Curve Editor")
        self.root.geometry("800x650")

        self.curve_type = StringVar(value="bezier") # Default curve type
        self.mode = StringVar(value="draw")        # 'draw' or 'edit'
        self.temp_points = []
        self.curves = []
        self.selected_curve_index = None
        self.selected_point_index = None
        self.dragging = False
        self.start_drag_pos = None
        self.snapped_start_point = None # Store endpoint we snapped to

        self._create_menu()
        self._create_toolbar()
        self._create_canvas()
        self._create_statusbar()

        # Bind curve type change to clear temp points and update status
        self.curve_type.trace_add("write", self.on_curve_type_change)
        # Bind mode change to clear temp points and update status
        self.mode.trace_add("write", self.on_mode_change)

        self.redraw_canvas()
        self.update_status() # Initial status update

    def _create_menu(self):
        # ... (menu creation code remains the same) ...
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Clear Canvas", command=self.clear_canvas)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        curve_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Curves", menu=curve_menu)
        # Use command=lambda for radiobuttons as well if direct action needed,
        # but trace_add on the variable is often cleaner
        curve_menu.add_radiobutton(label="Hermite", variable=self.curve_type, value="hermite")
        curve_menu.add_radiobutton(label="Bézier", variable=self.curve_type, value="bezier")
        curve_menu.add_radiobutton(label="B-Spline", variable=self.curve_type, value="bspline")

        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Mode", menu=edit_menu)
        edit_menu.add_radiobutton(label="Draw", variable=self.mode, value="draw")
        edit_menu.add_radiobutton(label="Edit Points", variable=self.mode, value="edit")

    def _create_toolbar(self):
        # ... (toolbar creation code remains the same) ...
        toolbar = Frame(self.root, bd=1, relief=SUNKEN)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_hermite = Button(toolbar, text="Hermite", command=lambda: self.curve_type.set("hermite"))
        btn_hermite.pack(side=tk.LEFT, padx=2, pady=2)

        btn_bezier = Button(toolbar, text="Bézier", command=lambda: self.curve_type.set("bezier"))
        btn_bezier.pack(side=tk.LEFT, padx=2, pady=2)

        btn_bspline = Button(toolbar, text="B-Spline", command=lambda: self.curve_type.set("bspline"))
        btn_bspline.pack(side=tk.LEFT, padx=2, pady=2)

        btn_clear = Button(toolbar, text="Clear", command=self.clear_canvas)
        btn_clear.pack(side=tk.RIGHT, padx=2, pady=2)

    def _create_canvas(self):
        # ... (canvas creation code remains the same) ...
        self.canvas = Canvas(self.root, bg="white", width=800, height=550)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

    def _create_statusbar(self):
        # ... (statusbar creation code remains the same) ...
        self.status_var = StringVar()
        statusbar = Label(self.root, textvariable=self.status_var, bd=1, relief=SUNKEN, anchor=W)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- Callback methods for variable changes ---
    def on_curve_type_change(self, *args):
        """Called when self.curve_type changes."""
        # print(f"Curve type changed to: {self.curve_type.get()}")
        self.temp_points = [] # Clear temp points when changing type
        self.snapped_start_point = None
        self.clear_selection()
        self.update_status()
        self.redraw_canvas() # Redraw to clear temp points visually

    def on_mode_change(self, *args):
        """Called when self.mode changes."""
        # print(f"Mode changed to: {self.mode.get()}")
        self.temp_points = [] # Clear temp points when changing mode
        self.snapped_start_point = None
        self.clear_selection()
        self.update_status()
        self.redraw_canvas() # Redraw to clear temp points visually


    def update_status(self):
        """UPDATED status logic"""
        ctype = self.curve_type.get()
        status = f"Mode: {self.mode.get().capitalize()} | Curve: {ctype.capitalize()} "

        if self.mode.get() == 'draw':
            needed_str = ""
            # Check if we are set to B-Spline AND the last curve drawn was also a B-Spline
            is_continuing_bspline = (ctype == 'bspline' and self.curves and
                                     self.curves[-1].curve_type == 'bspline')

            if is_continuing_bspline:
                # If continuing B-spline, we only need 1 more point to extend
                needed_str = "(Click to add point to extend)"
            else:
                # Otherwise, we need 4 points for a new curve (Hermite, Bezier, or initial B-Spline)
                needed = 4
                needed_str = f"({len(self.temp_points)}/{needed} needed)"

            status += f"| {needed_str}"
            if self.snapped_start_point:
                 status += " (Snapped to end point)"

        elif self.mode.get() == 'edit' and self.selected_point_index is not None:
             status += f"| Editing Point {self.selected_point_index} of Curve {self.selected_curve_index}"
        elif self.mode.get() == 'edit':
            status += "| Click near a control point to select and drag."
        else: # Should not happen?
             status += "| Select mode and curve type."


        self.status_var.set(status)

    def clear_canvas(self):
        # ... (remains the same) ...
        self.curves = []
        self.temp_points = []
        self.clear_selection()
        self.snapped_start_point = None
        self.redraw_canvas()
        self.update_status()

    def clear_selection(self):
        # ... (remains the same) ...
         self.selected_curve_index = None
         self.selected_point_index = None
         self.dragging = False
         # Redraw needed to remove highlight if deselected by clicking background
         self.redraw_canvas()

    # Removed get_needed_points as logic is now in update_status and on_canvas_press

    def find_nearby_control_point(self, x, y, tolerance=CONTROL_POINT_RADIUS * 2.5): # Slightly larger tolerance
        # ... (remains the same) ...
        for curve_idx, curve in enumerate(self.curves):
            for point_idx, p in enumerate(curve.points):
                dist_sq = (p[0] - x)**2 + (p[1] - y)**2
                if dist_sq < tolerance**2:
                    return curve_idx, point_idx
        return None, None


    def find_nearby_endpoint(self, x, y, tolerance=SNAP_DISTANCE):
        # ... (remains the same) ...
        nearest_dist_sq = tolerance**2
        found_point = None
        for curve_idx, curve in enumerate(self.curves):
            endpoint = curve.get_end_point()
            if endpoint:
                dist_sq = (endpoint[0] - x)**2 + (endpoint[1] - y)**2
                if dist_sq < nearest_dist_sq:
                    nearest_dist_sq = dist_sq
                    found_point = endpoint

            startpoint = curve.get_start_point()
            if startpoint:
                 dist_sq = (startpoint[0] - x)**2 + (startpoint[1] - y)**2
                 if dist_sq < nearest_dist_sq:
                     nearest_dist_sq = dist_sq
                     found_point = startpoint
        return found_point # Return the coordinates of the nearest endpoint found (or None)


    def on_canvas_press(self, event):
        """UPDATED press logic for B-Spline continuation"""
        x, y = event.x, event.y
        self.start_drag_pos = (x, y)
        self.dragging = False # Reset dragging flag

        if self.mode.get() == 'edit':
            # --- Edit Mode ---
            selected_before = self.selected_point_index is not None
            curve_idx_before = self.selected_curve_index
            point_idx_before = self.selected_point_index

            self.clear_selection() # Clear previous selection visually first
            curve_idx, point_idx = self.find_nearby_control_point(x, y)

            if curve_idx is not None:
                self.selected_curve_index = curve_idx
                self.selected_point_index = point_idx
                self.dragging = True # Ready to drag this point
                # print(f"Selected point {point_idx} of curve {curve_idx}")
                self.redraw_canvas() # Redraw to show new selection highlight
            # If clicked on background, clear_selection already happened and redraw removes highlight

        elif self.mode.get() == 'draw':
            # --- Draw Mode ---
            current_point = (x, y)
            ctype = self.curve_type.get()

            # Check if we are continuing an existing B-spline
            is_continuing_bspline = (ctype == 'bspline' and self.curves and
                                     self.curves[-1].curve_type == 'bspline')

            # --- Snapping Logic ---
            # Snap ONLY if we are starting a potentially NEW curve segment
            if not self.temp_points and not is_continuing_bspline:
                # Try to snap the first point of a new segment
                snapped_point = self.find_nearby_endpoint(x, y)
                if snapped_point:
                    current_point = snapped_point
                    self.snapped_start_point = snapped_point # Store the snapped position
                    print(f"Snapped start point to {current_point}")
                else:
                    self.snapped_start_point = None # Ensure it's cleared if no snap

            # --- Point Handling Logic ---
            if is_continuing_bspline:
                # --- Append point to existing B-Spline ---
                last_curve = self.curves[-1]
                # Optional: Snap the extending point to existing endpoints?
                snapped_extend_point = self.find_nearby_endpoint(x, y)
                if snapped_extend_point:
                     # Don't snap to the B-spline's own last point usually
                     # Check if the snap target is the *current* end of the spline being extended
                     current_b_spline_end = last_curve.get_end_point()
                     if not (current_b_spline_end and
                           abs(snapped_extend_point[0] - current_b_spline_end[0]) < 1e-6 and
                           abs(snapped_extend_point[1] - current_b_spline_end[1]) < 1e-6) :
                         current_point = snapped_extend_point
                         print(f"Snapped extending point to {current_point}")


                last_curve.points.append(current_point)
                last_curve.calculated_points = [] # Invalidate cache for redraw
                print(f"Appended point to B-spline. Total points: {len(last_curve.points)}")
                # Do NOT add to temp_points, temp_points should be empty
                self.temp_points = []
                # Snap state is only relevant for the *start* of a segment
                self.snapped_start_point = None
            else:
                # --- Collect points for a NEW curve (Hermite, Bezier, or initial B-Spline) ---
                self.temp_points.append(current_point)
                needed = 4 # Required points for these types

                if len(self.temp_points) == needed:
                    # Create the new curve
                    try:
                        new_curve = None
                        points_to_use = list(self.temp_points) # Use a copy

                        if ctype == 'hermite':
                            new_curve = HermiteCurve(points_to_use)
                        elif ctype == 'bezier':
                            new_curve = BezierCurve(points_to_use)
                        elif ctype == 'bspline':
                            # This is the *initial* B-Spline segment
                            new_curve = BSplineCurve(points_to_use)

                        if new_curve:
                            self.curves.append(new_curve)
                            print(f"Created new {ctype} curve. Total curves: {len(self.curves)}")

                    except ValueError as e:
                        messagebox.showerror("Error", f"Could not create curve: {e}")
                        # Keep temp points? Or clear? Clearing seems safer.
                        # self.temp_points = []
                    finally:
                        # Clear temp points AFTER attempting creation, regardless of success/failure
                        # Ensures we start fresh for the next curve or B-spline extension
                        self.temp_points = []
                        self.snapped_start_point = None # Clear snap state after curve creation


            self.redraw_canvas()

        self.update_status()


    def on_canvas_drag(self, event):
        # ... (drag logic remains mostly the same) ...
        if self.mode.get() == 'edit' and self.dragging and self.selected_curve_index is not None:
            x, y = event.x, event.y
            curve = self.curves[self.selected_curve_index]
            original_pos = curve.points[self.selected_point_index]

            # --- Optional: Snap during drag ---
            snapped_pos = self.find_nearby_endpoint(x, y)
            target_pos = snapped_pos if snapped_pos else (x, y)

             # Update the point position
            if target_pos != original_pos:
                curve.update_point(self.selected_point_index, target_pos)

                # --- Special Handling for Joined Curves ---
                # If this point *was* snapped (i.e., it matches the start/end of another curve),
                # we might need to update the adjacent curve's point too.
                # This requires finding which other curve/point matches the *original* position.
                # Simpler approach: Just let the user manually edit the other point if needed.
                # Advanced: Implement linked points.

                self.redraw_canvas() # Redraw only if position actually changed
                self.update_status() # Update status during drag


    def on_canvas_release(self, event):
        # ... (release logic remains the same) ...
        # Stop dragging, but keep selection active for potential further edits
        if self.mode.get() == 'edit' and self.dragging:
            # Final redraw might be needed if snapping occurred exactly on release
            # Check if position changed between press and release or during drag
             self.redraw_canvas()

        self.dragging = False # Stop dragging state
        self.update_status()


    def redraw_canvas(self):
        # ... (redraw logic remains the same - draws curves, points, temp points, selection) ...
        self.canvas.delete("all")

        # Draw all completed curves
        for idx, curve in enumerate(self.curves):
            try:
                curve.draw(self.canvas, color="blue", width=2)
                curve.draw_control_polygon(self.canvas, color="lightgrey")
                # Highlight selected curve's points
                point_color = "magenta" if idx == self.selected_curve_index and self.mode.get() == 'edit' else "red"
                curve.draw_control_points(self.canvas, color=point_color)
            except Exception as e:
                 print(f"Error drawing curve {idx} ({curve.curve_type}): {e}") # Basic error logging


        # Draw temporary points being placed (only relevant for new curves)
        for i, p in enumerate(self.temp_points):
            x0, y0 = p[0] - CONTROL_POINT_RADIUS, p[1] - CONTROL_POINT_RADIUS
            x1, y1 = p[0] + CONTROL_POINT_RADIUS, p[1] + CONTROL_POINT_RADIUS
            self.canvas.create_oval(x0, y0, x1, y1, fill="orange", outline="black", tags="temp_point")

        # Draw temporary polygon for points being placed
        if len(self.temp_points) > 1:
             flat_points = [coord for point in self.temp_points for coord in point]
             self.canvas.create_line(flat_points, fill="darkgrey", dash=(2,2), tags="temp_polygon")

        # Highlight the currently selected control point in edit mode
        if self.mode.get() == 'edit' and self.selected_point_index is not None and self.selected_curve_index is not None:
             # Check if selected curve still exists (safety for clear canvas etc.)
             if self.selected_curve_index < len(self.curves):
                 curve = self.curves[self.selected_curve_index]
                 # Check if selected point index is valid for the curve
                 if self.selected_point_index < len(curve.points):
                     p = curve.points[self.selected_point_index]
                     r = CONTROL_POINT_RADIUS + 2 # Make highlight slightly larger
                     x0, y0 = p[0] - r, p[1] - r
                     x1, y1 = p[0] + r, p[1] + r
                     self.canvas.create_oval(x0, y0, x1, y1, outline="cyan", width=2, tags="selection_highlight")



# --- Main Execution ---
if __name__ == "__main__":
    # Убедитесь, что файл matrix_utils.py находится в той же директории
    try:
        import matrix_utils as mu
    except ImportError:
        print("Ошибка: Файл matrix_utils.py не найден.")
        print("Пожалуйста, убедитесь, что он находится в той же директории, что и этот скрипт.")
        exit()

    root = tk.Tk()
    app = CurveEditorApp(root)
    root.mainloop()
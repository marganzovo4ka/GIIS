import tkinter as tk

class LineEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор")

        # Панель инструментов
        toolbar = tk.Frame(root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Кнопки для выбора алгоритма
        algorithms = ["ЦДА", "Брезенхем", "Ву"]
        self.algorithm_var = tk.StringVar(value=algorithms[0])
        for alg in algorithms:
            btn = tk.Radiobutton(toolbar, text=alg, variable=self.algorithm_var, value=alg)
            btn.pack(side=tk.LEFT)

        # Флажок для включения отладочного режима
        self.debug_mode = tk.BooleanVar(value=False)
        debug_checkbox = tk.Checkbutton(toolbar, text="Отладочный режим", variable=self.debug_mode)
        debug_checkbox.pack(side=tk.LEFT)

        # Кнопка "Шаг"
        self.step_button = tk.Button(toolbar, text="Шаг", command=self.step_through_algorithm, state=tk.DISABLED)
        self.step_button.pack(side=tk.LEFT)

        # Холст для рисования
        self.canvas = tk.Canvas(root, width=600, height=400, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Текстовое поле для отладочной информации
        self.debug_text = tk.Text(root, height=10, width=80)
        self.debug_text.pack(side=tk.BOTTOM, fill=tk.X)
        self.debug_text.config(state=tk.DISABLED)  # Заблокировать редактирование

        # Лупа (увеличенное изображение)
        self.magnifier_window = None
        self.magnifier_canvas = None
        self.magnification_factor = 10  # Масштаб увеличения
        self.magnifier_size = 100  # Размер лупы (в пикселях)

        # Переменные для хранения координат
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.steps = []  # Список шагов для текущего алгоритма
        self.current_step = 0  # Текущий шаг

        # Привязка событий мыши
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.update_magnifier)

        # Рисуем сетку
        self.draw_grid()

    def draw_grid(self):
        """Рисует сетку в один пиксель."""
        width, height = 600, 400
        for x in range(0, width, 1):
            self.canvas.create_line(x, 0, x, height, fill="#f0f0f0")  # Очень светло-серые линии
        for y in range(0, height, 1):
            self.canvas.create_line(0, y, width, y, fill="#f0f0f0")

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_mouse_drag(self, event):
        pass  # Можно добавить предварительное отображение линии

    def on_mouse_up(self, event):
        self.end_x = event.x
        self.end_y = event.y

        # Очистить текущие шаги
        self.steps = []
        self.current_step = 0

        # Выбрать алгоритм
        algorithm = self.algorithm_var.get()
        if algorithm == "ЦДА":
            self.steps = self.generate_line_dda(self.start_x, self.start_y, self.end_x, self.end_y)
        elif algorithm == "Брезенхем":
            self.steps = self.generate_line_bresenham(self.start_x, self.start_y, self.end_x, self.end_y)
        elif algorithm == "Ву":
            self.steps = self.generate_line_wu(self.start_x, self.start_y, self.end_x, self.end_y)

        # Если отладочный режим выключен, рисуем всю линию сразу
        if not self.debug_mode.get():
            self.draw_entire_line()
        else:
            # Включаем кнопку "Шаг" в отладочном режиме
            self.step_button.config(state=tk.NORMAL)

    def draw_entire_line(self):
        """Рисует всю линию сразу."""
        for step in self.steps:
            x, y, brightness = step
            self.draw_pixel_with_brightness(x, y, brightness)

    def step_through_algorithm(self):
        """Выполняет один шаг алгоритма."""
        if self.current_step < len(self.steps):
            x, y, brightness = self.steps[self.current_step]
            self.draw_pixel_with_brightness(x, y, brightness)
            self.log_debug(f"Шаг {self.current_step}: Рисуем точку ({x}, {y}) с яркостью {brightness:.2f}")
            self.current_step += 1
        else:
            self.log_debug("Конец линии.")

    def draw_pixel_with_brightness(self, x, y, brightness):
        """Рисует пиксель с заданной яркостью."""
        color = f"#{int(255 * brightness):02x}{int(255 * brightness):02x}{int(255 * brightness):02x}"
        self.canvas.create_oval(x, y, x + 1, y + 1, fill=color)

    def log_debug(self, message):
        """Добавляет сообщение в текстовое поле для отладки."""
        if not self.debug_mode.get():
            return  # Если отладочный режим выключен, ничего не делаем

        self.debug_text.config(state=tk.NORMAL)  # Разблокировать текстовое поле
        self.debug_text.insert(tk.END, message + "\n")  # Добавить сообщение
        self.debug_text.see(tk.END)  # Прокрутить до конца
        self.debug_text.config(state=tk.DISABLED)  # Заблокировать текстовое поле снова

    def update_magnifier(self, event):
        """Обновляет лупу при движении мыши."""
        if self.magnifier_window is None or not self.magnifier_window.winfo_exists():
            self.create_magnifier_window()

        # Получаем координаты курсора
        x, y = event.x, event.y

        # Ограничиваем область, чтобы не выходить за границы холста
        x_min = max(0, x - self.magnifier_size // (2 * self.magnification_factor))
        y_min = max(0, y - self.magnifier_size // (2 * self.magnification_factor))
        x_max = min(600, x + self.magnifier_size // (2 * self.magnification_factor))
        y_max = min(400, y + self.magnifier_size // (2 * self.magnification_factor))

        # Очищаем лупу
        self.magnifier_canvas.delete("all")

        # Рисуем увеличенную область
        for px in range(x_min, x_max):
            for py in range(y_min, y_max):
                # Получаем цвет пикселя
                color = self.canvas.itemcget(self.canvas.find_closest(px, py), "fill")
                if not color:
                    color = "white"  # Если пиксель не найден, используем белый цвет

                # Рисуем увеличенный пиксель
                mx = (px - x_min) * self.magnification_factor
                my = (py - y_min) * self.magnification_factor
                self.magnifier_canvas.create_rectangle(
                    mx, my,
                    mx + self.magnification_factor, my + self.magnification_factor,
                    fill=color, outline=""
                )

    def create_magnifier_window(self):
        """Создает окно лупы."""
        self.magnifier_window = tk.Toplevel(self.root)
        self.magnifier_window.title("Лупа")
        self.magnifier_window.geometry(f"{self.magnifier_size}x{self.magnifier_size}")
        self.magnifier_canvas = tk.Canvas(self.magnifier_window, width=self.magnifier_size, height=self.magnifier_size)
        self.magnifier_canvas.pack()

    # Алгоритм ЦДА
    def generate_line_dda(self, x1, y1, x2, y2):
        steps_list = []
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return [(x1, y1, 1)]
        x_increment = dx / steps
        y_increment = dy / steps
        x, y = x1, y1
        for _ in range(steps + 1):
            steps_list.append((round(x), round(y), 1))
            x += x_increment
            y += y_increment
        return steps_list

    # Целочисленный алгоритм Брезенхема
    def generate_line_bresenham(self, x1, y1, x2, y2):
        steps_list = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            steps_list.append((x1, y1, 1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
        return steps_list

    # Алгоритм Ву
    def generate_line_wu(self, x1, y1, x2, y2):
        steps_list = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        steep = dy > dx

        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1

        dx = x2 - x1
        dy = y2 - y1
        gradient = dy / dx if dx != 0 else 1

        xend = round(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = 1 - (x1 + 0.5) % 1
        xpxl1 = xend
        ypxl1 = int(yend)
        if steep:
            steps_list.append((ypxl1, xpxl1, 1 - (yend - int(yend))))
            steps_list.append((ypxl1 + 1, xpxl1, yend - int(yend)))
        else:
            steps_list.append((xpxl1, ypxl1, 1 - (yend - int(yend))))
            steps_list.append((xpxl1, ypxl1 + 1, yend - int(yend)))

        intery = yend + gradient

        xend = round(x2)
        yend = y2 + gradient * (xend - x2)
        xgap = (x2 + 0.5) % 1
        xpxl2 = xend
        ypxl2 = int(yend)
        if steep:
            steps_list.append((ypxl2, xpxl2, 1 - (yend - int(yend))))
            steps_list.append((ypxl2 + 1, xpxl2, yend - int(yend)))
        else:
            steps_list.append((xpxl2, ypxl2, 1 - (yend - int(yend))))
            steps_list.append((xpxl2, ypxl2 + 1, yend - int(yend)))

        for x in range(xpxl1 + 1, xpxl2):
            if steep:
                steps_list.append((int(intery), x, 1 - (intery - int(intery))))
                steps_list.append((int(intery) + 1, x, intery - int(intery)))
            else:
                steps_list.append((x, int(intery), 1 - (intery - int(intery))))
                steps_list.append((x, int(intery) + 1, intery - int(intery)))
            intery += gradient
        return steps_list


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = LineEditorApp(root)
    root.mainloop()
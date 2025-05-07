import pygame
import numpy as np
import math


# --- Матричные функции (для операций с ВЕКТОРАМИ-СТОЛБЦАМИ: v' = M * v) ---
def translation_matrix(tx, ty, tz):
    return np.array([
        [1, 0, 0, tx],
        [0, 1, 0, ty],
        [0, 0, 1, tz],
        [0, 0, 0, 1]
    ], dtype=float)


def rotation_x_matrix(angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([
        [1, 0, 0, 0],
        [0, c, -s, 0],
        [0, s, c, 0],
        [0, 0, 0, 1]
    ], dtype=float)


def rotation_y_matrix(angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s, 0, c, 0],
        [0, 0, 0, 1]
    ], dtype=float)


def rotation_z_matrix(angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([
        [c, -s, 0, 0],
        [s, c, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], dtype=float)


def scaling_matrix(sx, sy, sz):
    return np.array([
        [sx, 0, 0, 0],
        [0, sy, 0, 0],
        [0, 0, sz, 0],
        [0, 0, 0, 1]
    ], dtype=float)


def reflection_matrix(axis='xy'):
    if axis == 'xy':  # Отражение относительно плоскости XY (меняется Z)
        return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]], dtype=float)
    elif axis == 'yz':  # Отражение относительно плоскости YZ (меняется X)
        return np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
    elif axis == 'xz':  # Отражение относительно плоскости XZ (меняется Y)
        return np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
    return np.identity(4, dtype=float)


# Простая перспективная проекция
# d - расстояние от камеры до плоскости проекции (фокусное расстояние)
def perspective_projection_matrix(d):
    # Эта матрица предполагает, что камера смотрит вдоль оси Z,
    # плоскость проекции находится на z=d.
    # Координаты x,y проецируются как x*d/z, y*d/z.
    # W-компонента после умножения будет z.
    # Затем при делении на w (т.е. на z) получим нужные x', y'.
    # Чтобы использовать d как "зум", можно умножить x, y на d в матрице.
    return np.array([
        [d, 0, 0, 0],
        [0, d, 0, 0],
        [0, 0, d, 0],  # Сохраняем Z для возможной сортировки по глубине (здесь не используется)
        [0, 0, 1, 0]  # Важно: w' = z
    ], dtype=float)


# --- Класс для 3D объекта ---
class Object3D:
    def __init__(self, vertices, edges):
        # Добавляем 1 для однородных координат
        self.original_vertices = np.hstack([
            np.array(vertices, dtype=float),
            np.ones((len(vertices), 1), dtype=float)
        ])
        self.edges = edges
        self.model_matrix = np.identity(4, dtype=float)

    @classmethod
    def load_from_file(cls, filename):
        vertices = []
        edges = []
        with open(filename, 'r') as f:
            num_vertices = int(f.readline())
            for _ in range(num_vertices):
                parts = f.readline().split()
                vertices.append([float(parts[0]), float(parts[1]), float(parts[2])])

            num_edges = int(f.readline())
            for _ in range(num_edges):
                parts = f.readline().split()
                edges.append((int(parts[0]), int(parts[1])))
        return cls(vertices, edges)

    def reset_transformations(self):
        self.model_matrix = np.identity(4, dtype=float)
        # Небольшой сдвиг назад, чтобы объект был виден
        self.apply_world_translation(0, 0, 5)  # Отодвинем от камеры

    def apply_local_translation(self, tx, ty, tz):
        # Перемещение относительно локальных осей объекта
        self.model_matrix = self.model_matrix @ translation_matrix(tx, ty, tz)

    def apply_world_translation(self, tx, ty, tz):
        # Перемещение относительно мировых осей
        self.model_matrix = translation_matrix(tx, ty, tz) @ self.model_matrix

    def apply_local_rotation_x(self, angle_rad):
        self.model_matrix = self.model_matrix @ rotation_x_matrix(angle_rad)

    def apply_local_rotation_y(self, angle_rad):
        self.model_matrix = self.model_matrix @ rotation_y_matrix(angle_rad)

    def apply_local_rotation_z(self, angle_rad):
        self.model_matrix = self.model_matrix @ rotation_z_matrix(angle_rad)

    def apply_local_scaling(self, sx, sy, sz):
        # Масштабирование относительно локального центра (0,0,0) объекта
        self.model_matrix = self.model_matrix @ scaling_matrix(sx, sy, sz)

    def apply_local_reflection(self, axis='xy'):
        self.model_matrix = self.model_matrix @ reflection_matrix(axis)

    def get_transformed_vertices(self, projection_matrix, screen_width, screen_height):
        # 1. Применяем Model матрицу (объект -> мир)
        #    Вершины хранятся как строки (N,4). M - матрица для столбцов.
        #    v_world_col = Model @ v_obj_col
        #    (Model @ Vertices_obj.T).T  ->  N x 4
        world_coords = (self.model_matrix @ self.original_vertices.T).T

        # 2. Применяем Projection матрицу (мир -> клиппинг спейс)
        #    v_clip_col = Projection @ v_world_col
        projected_coords_homogeneous = (projection_matrix @ world_coords.T).T

        projected_2d = []
        for vertex_h in projected_coords_homogeneous:
            x, y, z, w = vertex_h
            if w != 0:  # Перспективное деление
                # Если w (которое часто равно z из world_coords) близко к 0 или отрицательно (за камерой),
                # точка не должна отображаться или обрабатываться особо.
                # Для простой проекции, где w=z, z<0 означает "за камерой" если камера смотрит в -Z
                # В нашей projection_matrix, w = z_world. Если z_world <= 0, точка за или на плоскости камеры.
                if w > 0.1:  # Небольшой near-clipping plane
                    px = x / w
                    py = y / w

                    # Преобразование в экранные координаты Pygame (центр экрана - начало координат)
                    # Y инвертируется, так как в Pygame Y растет вниз
                    screen_x = int(px + screen_width / 2)
                    screen_y = int(-py + screen_height / 2)
                    projected_2d.append((screen_x, screen_y))
                else:
                    projected_2d.append(None)  # Точка за камерой или слишком близко
            else:
                projected_2d.append(None)  # Избегаем деления на ноль
        return projected_2d


# --- Основная программа ---
def main():
    pygame.init()

    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("3D Geometric Transformations")
    font = pygame.font.SysFont("Arial", 18)

    # Загрузка объекта
    try:
        obj = Object3D.load_from_file("cube.txt")  # Убедитесь, что файл cube.txt существует
    except FileNotFoundError:
        print("Ошибка: Файл 'cube.txt' не найден. Создайте его или укажите другой путь.")
        # Создаем куб по умолчанию, если файл не найден
        default_vertices = [
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
        ]
        default_edges = [
            (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        obj = Object3D(default_vertices, default_edges)
        print("Создан куб по умолчанию.")

    obj.reset_transformations()  # Исходное положение объекта

    # Параметры проекции
    focal_length = 300  # Расстояние до плоскости проекции, влияет на "зум"
    projection_mat = perspective_projection_matrix(focal_length)

    # Параметры управления
    move_speed = 0.2
    rotation_speed = math.radians(2)  # 2 градуса в радианы
    scale_factor_delta = 0.05

    clock = pygame.time.Clock()
    running = True
    show_help = True

    help_text_lines = [
        "Управление:",
        "Перемещение: Стрелки (X,Y), PgUp/PgDn (Z - мировые)",
        "Вращение: W/S (X), A/D (Y), Q/E (Z - локальные)",
        "Масштаб: +/- (равномерно), Num7/Num1 (X), Num8/Num2 (Y), Num9/Num3 (Z)",
        "Отражение: F1 (XY), F2 (YZ), F3 (XZ - локальные)",
        "Перспектива: Z/X (изменить фокусное расстояние)",
        "R: Сброс всех трансформаций",
        "H: Показать/скрыть помощь"
    ]

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    obj.reset_transformations()
                elif event.key == pygame.K_t:
                    show_help = not show_help
                # Отражения (применяются один раз при нажатии)
                elif event.key == pygame.K_F1:
                    obj.apply_local_reflection('xy')
                elif event.key == pygame.K_F2:
                    obj.apply_local_reflection('yz')
                elif event.key == pygame.K_F3:
                    obj.apply_local_reflection('xz')

        keys = pygame.key.get_pressed()

        # Перемещение (относительно мировых осей)
        if keys[pygame.K_LEFT]: obj.apply_world_translation(-move_speed, 0, 0)
        if keys[pygame.K_RIGHT]: obj.apply_world_translation(move_speed, 0, 0)
        if keys[pygame.K_UP]: obj.apply_world_translation(0, move_speed, 0)
        if keys[pygame.K_DOWN]: obj.apply_world_translation(0, -move_speed, 0)
        if keys[pygame.K_PAGEUP]: obj.apply_world_translation(0, 0, -move_speed)  # К камере
        if keys[pygame.K_PAGEDOWN]: obj.apply_world_translation(0, 0, move_speed)  # От камеры

        # Вращение (относительно локальных осей объекта)
        if keys[pygame.K_w]: obj.apply_local_rotation_x(rotation_speed)
        if keys[pygame.K_s]: obj.apply_local_rotation_x(-rotation_speed)
        if keys[pygame.K_a]: obj.apply_local_rotation_y(rotation_speed)
        if keys[pygame.K_d]: obj.apply_local_rotation_y(-rotation_speed)
        if keys[pygame.K_q]: obj.apply_local_rotation_z(rotation_speed)
        if keys[pygame.K_e]: obj.apply_local_rotation_z(-rotation_speed)

        # Масштабирование (относительно локального центра объекта)
        current_scale_x, current_scale_y, current_scale_z = 1, 1, 1
        if keys[pygame.K_PLUS] or keys[pygame.K_KP_PLUS]:
            current_scale_x += scale_factor_delta
            current_scale_y += scale_factor_delta
            current_scale_z += scale_factor_delta
        if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            current_scale_x -= scale_factor_delta
            current_scale_y -= scale_factor_delta
            current_scale_z -= scale_factor_delta

        if keys[pygame.K_KP_7]: current_scale_x += scale_factor_delta
        if keys[pygame.K_KP_1]: current_scale_x -= scale_factor_delta
        if keys[pygame.K_KP_8]: current_scale_y += scale_factor_delta
        if keys[pygame.K_KP_2]: current_scale_y -= scale_factor_delta
        if keys[pygame.K_KP_9]: current_scale_z += scale_factor_delta
        if keys[pygame.K_KP_3]: current_scale_z -= scale_factor_delta

        # Применяем масштабирование если оно изменилось
        if not (math.isclose(current_scale_x, 1) and \
                math.isclose(current_scale_y, 1) and \
                math.isclose(current_scale_z, 1)):
            obj.apply_local_scaling(current_scale_x, current_scale_y, current_scale_z)

        # Изменение перспективы (фокусного расстояния)
        if keys[pygame.K_z]:
            focal_length -= 5
            if focal_length < 10: focal_length = 10  # Ограничение
            projection_mat = perspective_projection_matrix(focal_length)
        if keys[pygame.K_x]:
            focal_length += 5
            projection_mat = perspective_projection_matrix(focal_length)

        # Отрисовка
        screen.fill((30, 30, 30))  # Темно-серый фон

        transformed_and_projected_vertices = obj.get_transformed_vertices(
            projection_mat, screen_width, screen_height
        )

        for edge in obj.edges:
            p1_idx, p2_idx = edge
            # Проверяем, что обе точки видимы
            if transformed_and_projected_vertices[p1_idx] and \
                    transformed_and_projected_vertices[p2_idx]:
                start_pos = transformed_and_projected_vertices[p1_idx]
                end_pos = transformed_and_projected_vertices[p2_idx]
                pygame.draw.line(screen, (200, 200, 200), start_pos, end_pos, 1)

        # Отрисовка подсказки
        if show_help:
            for i, line in enumerate(help_text_lines):
                text_surface = font.render(line, True, (220, 220, 200))
                screen.blit(text_surface, (10, 10 + i * 20))

        # Отображение фокусного расстояния
        focal_text = font.render(f"Focal Length (Z/X): {focal_length:.0f}", True, (220, 220, 200))
        screen.blit(focal_text, (screen_width - focal_text.get_width() - 10, 10))

        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    pygame.quit()


if __name__ == '__main__':
    main()
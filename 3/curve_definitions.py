from matrix_utils import build_geometry_matrix, calculate_point

"""
Определения базисных матриц и функций для расчета точек кривых.
"""

# --- Базисные матрицы ---

# Эрмит (P1, P4, R1, R4)
M_HERMITE = [
    [ 2.0, -3.0,  0.0,  1.0],
    [-2.0,  3.0,  0.0,  0.0],
    [ 1.0, -2.0,  1.0,  0.0],
    [ 1.0, -1.0,  0.0,  0.0]
]
# Примечание: Транспонировано для удобства умножения [t^3, t^2, t, 1] * M * G

# Безье (P0, P1, P2, P3)
M_BEZIER = [
    [-1.0,  3.0, -3.0,  1.0],
    [ 3.0, -6.0,  3.0,  0.0],
    [-3.0,  3.0,  0.0,  0.0],
    [ 1.0,  0.0,  0.0,  0.0]
] # Транспонировано

# B-сплайн (кубический равномерный, для сегмента Pi, Pi+1, Pi+2, Pi+3)
M_BSPLINE_UNIFORM = [
    [-1.0/6.0,  3.0/6.0, -3.0/6.0,  1.0/6.0],
    [ 3.0/6.0, -6.0/6.0,  0.0/6.0,  4.0/6.0],
    [-3.0/6.0,  3.0/6.0,  3.0/6.0,  1.0/6.0],
    [ 1.0/6.0,  0.0/6.0,  0.0/6.0,  0.0/6.0]
] # Транспонировано


# --- Функции расчета точек ---

def get_hermite_point(t, p1, p4, r1, r4):
    """
    Вычисляет точку на кривой Эрмита.
    p1, p4: начальная и конечная точки (кортежи (x, y))
    r1, r4: начальный и конечный векторы касательных (кортежи (dx, dy))
    """
    t_vector = [t**3, t**2, t, 1.0]
    # Матрица геометрии для Эрмита: [[P1x, P1y], [P4x, P4y], [R1x, R1y], [R4x, R4y]]
    geom_matrix = [
        [p1[0], p1[1]],
        [p4[0], p4[1]],
        [r1[0], r1[1]],
        [r4[0], r4[1]]
    ]
    return calculate_point(t_vector, M_HERMITE, geom_matrix)

def get_bezier_point(t, p0, p1, p2, p3):
    """
    Вычисляет точку на кривой Безье 3-го порядка.
    p0, p1, p2, p3: контрольные точки (кортежи (x, y))
    """
    t_vector = [t**3, t**2, t, 1.0]
    geom_matrix = build_geometry_matrix([p0, p1, p2, p3])
    return calculate_point(t_vector, M_BEZIER, geom_matrix)

def get_bspline_segment_point(t, p_i_minus_1, p_i, p_i_plus_1, p_i_plus_2):
    """
    Вычисляет точку на сегменте равномерного кубического B-сплайна.
    p_*: Контрольные точки для текущего сегмента (кортежи (x, y))
    t: Параметр внутри сегмента (0 <= t <= 1)
    """
    t_vector = [t**3, t**2, t, 1.0]
    geom_matrix = build_geometry_matrix([p_i_minus_1, p_i, p_i_plus_1, p_i_plus_2])
    return calculate_point(t_vector, M_BSPLINE_UNIFORM, geom_matrix)

# --- Параметры кривых ---
CURVE_TYPES = {
    "hermite": {"name": "Эрмит", "points_needed": 4},
    "bezier": {"name": "Безье", "points_needed": 4},
    "bspline": {"name": "B-Сплайн", "points_needed": 4} # Минимально 4 для первого сегмента
}

# Количество шагов для отрисовки кривой
CURVE_DETAIL = 30
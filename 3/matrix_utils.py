def multiply_vector_matrix(vec, matrix):
    """Multiplies a row vector (list) by a matrix (list of lists)."""
    if len(vec) != len(matrix):
        raise ValueError("Vector length must match number of matrix rows.")
    result = [0] * len(matrix[0])
    for j in range(len(matrix[0])): # Iterate columns of matrix
        sum_val = 0
        for i in range(len(vec)):   # Iterate elements of vector / rows of matrix
            sum_val += vec[i] * matrix[i][j]
        result[j] = sum_val
    return result

def add_vectors(v1, v2):
    """Adds two vectors (lists or tuples)."""
    return [a + b for a, b in zip(v1, v2)]

def subtract_vectors(v1, v2):
    """Subtracts vector v2 from v1."""
    return [a - b for a, b in zip(v1, v2)]

def scalar_multiply(scalar, vec):
    """Multiplies a vector by a scalar."""
    return [scalar * x for x in vec]

# Optional: Matrix * Matrix (if needed later)
def multiply_matrices(mat1, mat2):
    # ... implementation ...
    pass
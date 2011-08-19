def create2DArray(w, h, v=None):
    return [[v for y in range(h)] for x in range(w)]

def clamped(min_v, max_v, v):
    if v < min_v:
        return min_v
    if v > max_v:
        return max_v
    return v

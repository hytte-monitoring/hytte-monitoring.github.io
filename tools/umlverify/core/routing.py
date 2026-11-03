"""Orthogonal routing around boxes, for lines nobody drew.

When a comparison drawing has to add a line that is not in the person's drawing —
a relation the AI added, say — draw.io's own router would draw it straight through
whatever is in the way. route() searches a grid instead, treating every box as an
obstacle with a margin around it, and prefers short paths with few bends. It leaves
and enters boxes at right angles, as UML diagrams do.

Boxes are (x, y, width, height). Diagram-agnostic.
"""
import heapq

STEP = 10      # grid spacing
MARGIN = 10    # clearance kept around every box
BEND = 12      # a bend costs as much as this many grid steps

_DIRS = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}
_OUT = {"left": "left", "right": "right", "top": "up", "bottom": "down"}      # leaving a side
_IN = {"left": "right", "right": "left", "top": "down", "bottom": "up"}       # entering a side


def _inside(point, box, margin):
    x, y, w, h = box
    return x - margin < point[0] < x + w + margin and y - margin < point[1] < y + h + margin


def segment_clear(a, b, boxes, margin=4):
    """True when the axis-aligned segment a-b stays clear of every box."""
    (ax, ay), (bx, by) = a, b
    for x, y, w, h in boxes:
        if ax == bx:   # vertical
            if x - margin < ax < x + w + margin and min(ay, by) < y + h + margin and max(ay, by) > y - margin:
                return False
        elif ay == by:  # horizontal
            if y - margin < ay < y + h + margin and min(ax, bx) < x + w + margin and max(ax, bx) > x - margin:
                return False
        else:
            return False
    return True


def _ports(box, sides):
    """(border point, first grid point outside the margin, side) for every grid step along each side."""
    x, y, w, h = box
    out = []
    for side in sides:
        if side in ("left", "right"):
            bx = x if side == "left" else x + w
            gx = (bx - MARGIN) // STEP * STEP if side == "left" else -((-(bx + MARGIN)) // STEP) * STEP
            for gy in range(int(-(-(y + 12) // STEP) * STEP), int(y + h - 12), STEP):
                out.append(((bx, gy), (gx, gy), side))
        else:
            by = y if side == "top" else y + h
            gy = (by - MARGIN) // STEP * STEP if side == "top" else -((-(by + MARGIN)) // STEP) * STEP
            for gx in range(int(-(-(x + 12) // STEP) * STEP), int(x + w - 12), STEP):
                out.append(((gx, by), (gx, gy), side))
    return out


def route(src, dst, obstacles):
    """-> (exit, entry, points) or None when no path exists.

    exit and entry are attachment points as fractions of the box, (fx, fy), with
    fx or fy at 0 or 1 for the side; points are the waypoints between them.
    """
    sides = ("left", "right", "top", "bottom")
    boxes = list(obstacles)
    xs = [b[0] for b in boxes] + [b[0] + b[2] for b in boxes]
    ys = [b[1] for b in boxes] + [b[1] + b[3] for b in boxes]
    lo_x, hi_x = min(xs) - 80, max(xs) + 80
    lo_y, hi_y = min(ys) - 80, max(ys) + 80

    def free(p):
        return lo_x <= p[0] <= hi_x and lo_y <= p[1] <= hi_y and not any(_inside(p, b, MARGIN) for b in boxes)

    targets = {}
    for border, grid, side in _ports(dst, sides):
        if free(grid):
            targets.setdefault(grid, []).append((side, border))
    if not targets:
        return None
    tx, ty = dst[0] + dst[2] / 2, dst[1] + dst[3] / 2

    def h(p):
        return (abs(p[0] - tx) + abs(p[1] - ty)) / STEP

    frontier, came, best = [], {}, {}
    for border, grid, side in _ports(src, sides):
        if free(grid):
            state = (grid, _OUT[side])
            best[state] = 0
            came[state] = ("start", border, side)
            heapq.heappush(frontier, (h(grid), 0, grid, _OUT[side]))

    while frontier:
        _, cost, p, d = heapq.heappop(frontier)
        if cost > best.get((p, d), float("inf")):
            continue
        for side, border in targets.get(p, ()):
            if _IN[side] == d:
                return _finish(came, (p, d), border, side, src, dst)
        for nd, (dx, dy) in _DIRS.items():
            if (dx, dy) == tuple(-v for v in _DIRS[d]):
                continue                       # no U-turns
            q = (p[0] + dx * STEP, p[1] + dy * STEP)
            if not free(q):
                continue
            c = cost + 1 + (BEND if nd != d else 0)
            if c < best.get((q, nd), float("inf")):
                best[(q, nd)] = c
                came[(q, nd)] = (p, d)
                heapq.heappush(frontier, (c + h(q), c, q, nd))
    return None


def _finish(came, state, end_border, end_side, src, dst):
    cells = []
    while True:
        prev = came[state]
        cells.append(state[0])
        if prev[0] == "start":
            start_border, start_side = prev[1], prev[2]
            break
        state = prev
    path = [start_border] + cells[::-1] + [end_border]
    points = []                               # keep only the corners
    for a, b, c in zip(path, path[1:], path[2:]):
        if (a[0] == b[0]) != (b[0] == c[0]) or (a[1] == b[1]) != (b[1] == c[1]):
            points.append(b)
    return _fraction(src, start_border, start_side), _fraction(dst, end_border, end_side), points


def _fraction(box, point, side):
    x, y, w, h = box
    if side in ("left", "right"):
        return (0.0 if side == "left" else 1.0, round((point[1] - y) / h, 4))
    return (round((point[0] - x) / w, 4), 0.0 if side == "top" else 1.0)

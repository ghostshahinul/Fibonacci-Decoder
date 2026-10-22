"""Classical Fibonacci-code decoder extracted from the accompanying walkthrough.

See README.md for attribution, assumptions, and the exact-recovery metric.
"""

import math
import random
from collections import deque

try:
    import networkx as _nx
    _HAVE_NX = True
except ImportError:
    _HAVE_NX = False



# Distance is the baseline; degeneracy is an experimental reconstruction.
WEIGHT_MODE = "distance"


def positive_modulo(num, modulo):
    x = num % modulo
    return x + modulo if x < 0 else x

def vertex_x_position(vertex, L):
    return positive_modulo(vertex, L)

def vertex_y_position(vertex, L):
    return vertex // L

def east_vertex(vertex, L):
    if positive_modulo(vertex, L) == L - 1:
        return vertex - (L - 1)
    return vertex + 1

def west_vertex(vertex, L):
    if vertex % L == 0:
        return vertex + (L - 1)
    return vertex - 1

def north_vertex(vertex, L, H):
    if (vertex - L) < 0:
        return vertex - L + L * H
    return vertex - L

def south_vertex(vertex, L, H):
    return positive_modulo(vertex + L, L * H)

def south_row(row, H):
    return positive_modulo(row + 1, H)

def switchbool(b):
    return 1 - b


def star_measurement(qubits, vertex, L, H):
    nv = north_vertex(vertex, L, H)
    ev = east_vertex(vertex, L)
    wv = west_vertex(vertex, L)
    return qubits[nv] ^ qubits[ev] ^ qubits[wv] ^ qubits[vertex]

def measure_all_stabilizers(qubits, L, H):
    return [star_measurement(qubits, j, L, H) for j in range(L * H)]


def create_symmetry(L, H, top_row):
    if not isinstance(L, int) or L < 4 or L & (L - 1) or H != L // 2:
        raise ValueError("Use a power-of-two L >= 4 and H = L // 2")
    if len(top_row) != L or any(x not in (0, 1) for x in top_row):
        raise ValueError("top_row must contain L binary entries")
    all_rows = [list(top_row)]
    for i in range(H - 1):
        row_above = all_rows[i]
        next_row = [(row_above[j] + row_above[(j + 1) % L]
                     + row_above[positive_modulo(j - 1, L)]) % 2
                    for j in range(L)]
        all_rows.append(next_row)
    symmetry = [i * L + j for i in range(H) for j in range(L) if all_rows[i][j]]
    # The periodic CA condition must hold in every column.
    last = all_rows[-1]
    if any((last[(j-1) % L] ^ last[j] ^ last[(j+1) % L]) != top_row[j]
           for j in range(L)):
        raise ValueError("top_row does not close under the periodic CA")
    return symmetry

def create_symmetry_reverse(symmetry, LxH):
    rev = [-1] * LxH
    for i, v in enumerate(symmetry):
        rev[v] = i
    return rev

def find_corresponding_indices(symmetry, stabilizers, N):
    on_sym = [0] * N
    for v in symmetry:
        on_sym[v] = 1
    return [i for i in range(N) if on_sym[i] and stabilizers[i]]

def index_defects_by_symmetry_num(symmetry_reverse, defect_lattice_locations):
    return [symmetry_reverse[d] for d in defect_lattice_locations]


def create_adjacency_list_symmetry(symmetry, L, H):
    n = len(symmetry)
    adj = [set() for _ in range(n)]
    sym_set = set(symmetry)
    for i in range(n - 1):
        for j in range(i + 1, n):
            v0, v1 = symmetry[i], symmetry[j]
            xp0, yp0 = vertex_x_position(v0, L), vertex_y_position(v0, L)
            xp1, yp1 = vertex_x_position(v1, L), vertex_y_position(v1, L)
            wrap_x = (2 * abs(yp1 - yp0)) > H
            wrap_y = (2 * abs(xp1 - xp0)) > L
            yd = abs(abs(yp0 - yp1) - H) if wrap_x else abs(yp0 - yp1)
            xd = abs(abs(xp0 - xp1) - L) if wrap_y else abs(xp0 - xp1)
            step_away = False
            if yd <= 1 and xd <= 1:
                step_away = True
            elif xd == 2 and yd == 0:
                if not wrap_y:
                    mid = east_vertex(v0, L) if xp0 < xp1 else east_vertex(v1, L)
                else:
                    mid = east_vertex(v1, L) if xp0 < xp1 else east_vertex(v0, L)
                if mid not in sym_set:
                    step_away = True
            if step_away:
                adj[i].add(j); adj[j].add(i)
    return adj


def shortest_paths_from(source, adj, n):
    dist = [-1] * n; cnt = [0] * n
    dist[source] = 0; cnt[source] = 1
    q = deque([source])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1; cnt[v] = cnt[u]; q.append(v)
            elif dist[v] == dist[u] + 1:
                cnt[v] += cnt[u]
    return dist, cnt

def build_edge_weight_matrix(symmetry, L, H, p, mode=None):
    if mode is None:
        mode = WEIGHT_MODE
    if mode not in ("distance", "degeneracy"):
        raise ValueError("mode must be distance or degeneracy")
    if not 0 < p < 1:
        raise ValueError("p must be strictly between 0 and 1")
    n = len(symmetry)
    adj = create_adjacency_list_symmetry(symmetry, L, H)
    BIG = 10 ** 9
    W = [[0] * n for _ in range(n)]
    c = math.log(p / (1.0 - p))
    for i in range(n):
        dist, cnt = shortest_paths_from(i, adj, n)
        for j in range(i + 1, n):
            d, Nij = dist[j], cnt[j]
            if d < 0 or Nij <= 0:
                w = BIG
            elif mode == "distance":
                w = d
            else:
                w = int(round((-math.log(Nij) - d * c) * 1000.0))
            W[i][j] = W[j][i] = w
    return W


def _matching_via_networkx(node_w):
    n = len(node_w)
    G = _nx.Graph(); G.add_nodes_from(range(n))
    for a in range(n):
        for b in range(a + 1, n):
            G.add_edge(a, b, weight=-node_w[a][b])
    mate = _nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)
    return sorted((min(a, b), max(a, b)) for (a, b) in mate)

def _matching_via_dp(node_w):
    n = len(node_w)
    if n % 2 or n > 20:
        raise ValueError("DP requires an even number of nodes <= 20")
    full = (1 << n) - 1
    INF = float("inf")
    dp = [INF] * (1 << n); par = [None] * (1 << n); dp[0] = 0
    for mask in range(1 << n):
        if dp[mask] == INF:
            continue
        i = 0
        while i < n and (mask >> i) & 1:
            i += 1
        if i == n:
            continue
        for j in range(i + 1, n):
            if not (mask >> j) & 1:
                nm = mask | (1 << i) | (1 << j)
                cost = dp[mask] + node_w[i][j]
                if cost < dp[nm]:
                    dp[nm] = cost; par[nm] = (i, j)
    pairs = []; mask = full
    while mask:
        i, j = par[mask]; pairs.append((i, j)); mask ^= (1 << i) | (1 << j)
    return pairs

def minimum_weight_matching_symmetry_index(defect_sym_locations, W):
    node_num = len(defect_sym_locations)
    if node_num == 0:
        return [], []
    if node_num % 2:
        raise ValueError("Odd defect count on symmetry: invalid syndrome or geometry")
    node_w = [[0] * node_num for _ in range(node_num)]
    for a in range(node_num):
        for b in range(a + 1, node_num):
            w = W[defect_sym_locations[a]][defect_sym_locations[b]]
            node_w[a][b] = node_w[b][a] = w
    if _HAVE_NX:
        pairs = _matching_via_networkx(node_w)
    elif node_num <= 20:
        pairs = _matching_via_dp(node_w)
    else:
        raise RuntimeError("Install networkx (%d defects too many for DP)." % node_num)
    A = [defect_sym_locations[a] for (a, b) in pairs]
    B = [defect_sym_locations[b] for (a, b) in pairs]
    return A, B


def find_y_cover_from_pair(v0, v1, L, H):
    yp0, yp1 = vertex_y_position(v0, L), vertex_y_position(v1, L)
    y_top, y_bottom = (yp0, yp1) if yp0 < yp1 else (yp1, yp0)
    wrap_y = (2 * abs(yp1 - yp0)) > H
    cover = set()
    if not wrap_y:
        for i in range(y_top, y_bottom + 1):
            cover.add(i)
    else:
        for i in range(y_bottom, y_top + H + 1):
            cover.add(positive_modulo(i, H))
    return cover

def find_x_cover_from_pair(v0, v1, L, H):
    xp0, xp1 = vertex_x_position(v0, L), vertex_x_position(v1, L)
    x_left, x_right = (xp0, xp1) if xp0 < xp1 else (xp1, xp0)
    wrap = (2 * abs(xp1 - xp0)) > L
    cover = set()
    if not wrap:
        for i in range(x_left, x_right + 1):
            cover.add(i)
    else:
        for i in range(x_right, x_left + L + 1):
            cover.add(positive_modulo(i, L))
    return cover


def test_code(p, L, H, min_tries, symmetry, weight_matrix, verbose=False,
              preset_error=None, snapshots=None, rng=None):
    if not isinstance(L, int) or L < 4 or L & (L - 1) or H != L // 2:
        raise ValueError("Use a power-of-two L >= 4 and H = L // 2")
    if not 0 <= p <= 1:
        raise ValueError("p must lie in [0, 1]")
    if not isinstance(min_tries, int) or min_tries < 0:
        raise ValueError("min_tries must be a nonnegative integer")
    rng = random if rng is None else rng
    LxH = L * H
    qubits = [0] * LxH
    if preset_error is not None:
        for idx in preset_error:
            if not isinstance(idx, int) or not 0 <= idx < LxH:
                raise ValueError("preset_error indices must be inside the lattice")
            qubits[idx] = 1
    else:
        for j in range(LxH):
            if rng.random() < p:
                qubits[j] = 1

    stabilizers = measure_all_stabilizers(qubits, L, H)
    mid_vertex = L * (H - 1) + L // 2
    bottom_vertex = L * (H - 1)
    error_prediction = [0] * LxH
    give_up = 0; round_number = 0
    stabilizers_left = list(stabilizers)
    sym = list(symmetry)

    if snapshots is not None:
        snapshots.append({"round": 0, "residual": list(stabilizers_left),
                          "prediction": list(error_prediction),
                          "applied": [0] * LxH, "defects": sum(stabilizers_left)})

    # No-error inputs are already decoded and need no matching rounds.
    if not any(stabilizers_left):
        return (1 if error_prediction == qubits else 0), 0

    while give_up == 0:
        num_old = sum(stabilizers_left)
        new_pred_v = [0] * LxH; new_pred_h = [0] * LxH; new_pred_b = [0] * LxH
        pred_v = list(error_prediction); pred_h = list(error_prediction); pred_b = list(error_prediction)
        should_we_flip = [0] * LxH

        for j in range(LxH):
            if j != 0:
                sym = [east_vertex(d, L) for d in sym]
                mid_vertex = east_vertex(mid_vertex, L)
                bottom_vertex = east_vertex(bottom_vertex, L)
                if j % L == 0:
                    sym = [south_vertex(d, L, H) for d in sym]
                    mid_vertex = south_vertex(mid_vertex, L, H)
                    bottom_vertex = south_vertex(bottom_vertex, L, H)

            defect_lattice = find_corresponding_indices(sym, stabilizers_left, LxH)
            sym_reverse = create_symmetry_reverse(sym, LxH)
            defect_sym = index_defects_by_symmetry_num(sym_reverse, defect_lattice)
            A_sym, B_sym = minimum_weight_matching_symmetry_index(defect_sym, weight_matrix)
            A = [sym[a] for a in A_sym]; B = [sym[b] for b in B_sym]

            column = vertex_x_position(mid_vertex, L)
            row = vertex_y_position(bottom_vertex, L)
            n_vert = n_horiz = 0
            for a, b in zip(A, B):
                xcover = find_x_cover_from_pair(a, b, L, H)
                ycover = find_y_cover_from_pair(a, b, L, H)
                if column in xcover:
                    n_vert += 1
                if (south_row(row, H) in ycover) and (row in ycover):
                    n_horiz += 1

            if n_vert % 2 == 1:
                new_pred_v[mid_vertex] = switchbool(new_pred_v[mid_vertex])
                pred_v[mid_vertex] = switchbool(pred_v[mid_vertex])
                should_we_flip[mid_vertex] += 1
            if n_horiz % 2 == 1:
                new_pred_h[bottom_vertex] = switchbool(new_pred_h[bottom_vertex])
                pred_h[bottom_vertex] = switchbool(pred_h[bottom_vertex])
                should_we_flip[bottom_vertex] += 1

        for j in range(LxH):
            if should_we_flip[j] == 2:
                pred_b[j] = switchbool(pred_b[j])
                new_pred_b[j] = switchbool(new_pred_b[j])

        stab_try_v = list(stabilizers_left); stab_try_h = list(stabilizers_left); stab_try_b = list(stabilizers_left)
        def _apply(stab, new_pred):
            for q in range(LxH):
                if new_pred[q]:
                    for s in (q, west_vertex(q, L), east_vertex(q, L), south_vertex(q, L, H)):
                        stab[s] = switchbool(stab[s])
        _apply(stab_try_v, new_pred_v); _apply(stab_try_h, new_pred_h); _apply(stab_try_b, new_pred_b)

        n_v = sum(stab_try_v); n_h = sum(stab_try_h); n_b = sum(stab_try_b)
        min_new = min(n_v, n_h, n_b)
        if min_new == n_b:
            stabilizers_left, error_prediction, chosen_new = stab_try_b, pred_b, new_pred_b
        elif min_new == n_v:
            stabilizers_left, error_prediction, chosen_new = stab_try_v, pred_v, new_pred_v
        else:
            stabilizers_left, error_prediction, chosen_new = stab_try_h, pred_h, new_pred_h

        num_stab = sum(stabilizers_left)
        if num_stab == 0:
            give_up = 1
        elif num_stab >= num_old and round_number >= min_tries:
            give_up = 2
        round_number += 1
        if verbose:
            print("  round %d: defects %d -> %d" % (round_number, num_old, num_stab))
        if snapshots is not None:
            snapshots.append({"round": round_number, "residual": list(stabilizers_left),
                              "prediction": list(error_prediction),
                              "applied": list(chosen_new), "defects": num_stab})

    if error_prediction == qubits:
        success = 1
    elif give_up == 1:
        success = 0
    else:
        success = 2
    return success, round_number


def compute_failure_number(p, L, H, min_tries, sample_size, symmetry, weight_matrix, rng=None):
    if not isinstance(sample_size, int) or sample_size <= 0:
        raise ValueError("sample_size must be a positive integer")
    out = {"incorrect": 0, "success": 0, "give_up": 0, "samples": sample_size}
    for _ in range(sample_size):
        s, _ = test_code(p, L, H, min_tries, symmetry, weight_matrix, rng=rng)
        out[{0: "incorrect", 1: "success", 2: "give_up"}[s]] += 1
    return out

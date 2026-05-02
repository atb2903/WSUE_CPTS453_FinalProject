import heapq
from math import sqrt

from map.graph import CampusGraph


def edge_pixel_length(graph: CampusGraph, from_id: int, to_id: int) -> float:
    """Euclidean pixel distance between two nodes."""
    a = graph.get_node(from_id)
    b = graph.get_node(to_id)
    if a is None:
        raise KeyError(f"From node missing: {from_id}")
    elif b is None:
        raise KeyError(f"To node missing: {to_id}")
    else:
        return sqrt((a.y - b.y) ** 2 + (a.x - b.x) ** 2)


def dijkstra_shortest_path(
    graph: CampusGraph, start_id: int, end_id: int
) -> list[int] | None:
    """
    Return the ordered node ids of the shortest path from start_id to end_id,
    or None if no path exists. Edge weight is Euclidean pixel distance.
    """
    if graph.get_node(start_id) is None or graph.get_node(end_id) is None:
        # TODO: add a warning to the user instead of silently failing.
        return None
    if start_id == end_id:
        # Technically this should never happen, but it's a good idea to handle it anyway.
        return [start_id]

    # Because user can edit the graph, this must be recomputed on every run.
    adjacency: dict[int, list[int]] = {n.id: [] for n in graph.nodes}
    for edge in graph.edges:
        if edge.from_id in adjacency and edge.to_id in adjacency:
            adjacency[edge.from_id].append(edge.to_id)
            adjacency[edge.to_id].append(edge.from_id)

    distances: dict[int, float] = {start_id: 0.0}
    predecessors: dict[int, int] = {}
    visited: set[int] = set()
    heap: list[tuple[float, int]] = [(0.0, start_id)]

    while heap:
        current_distance, current_id = heapq.heappop(heap)
        if current_id in visited:
            continue
        visited.add(current_id)
        if current_id == end_id:
            break
        for neighbor_id in adjacency.get(current_id, []):
            if neighbor_id in visited:
                continue
            tentative = current_distance + edge_pixel_length(graph, current_id, neighbor_id)
            if tentative < distances.get(neighbor_id, float("inf")):
                distances[neighbor_id] = tentative
                predecessors[neighbor_id] = current_id
                heapq.heappush(heap, (tentative, neighbor_id))

    if end_id not in distances:
        return None

    path: list[int] = []
    cursor = end_id
    while cursor != start_id:
        path.append(cursor)
        if cursor not in predecessors:
            return None
        cursor = predecessors[cursor]
    path.append(start_id)
    return path

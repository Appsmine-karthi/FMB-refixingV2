from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize
from typing import List, Tuple

def get_subdivision_edges(polygons,seed_points):

    result = []

    for seed in seed_points:
        seed_pt = Point(seed)
        containing_polygons = []

        # Find all polygons containing the seed
        for poly in polygons:
            if poly.contains(seed_pt):
                containing_polygons.append(poly)

        # Choose the innermost (smallest area) polygon if multiple
        if containing_polygons:
            selected_poly = min(containing_polygons, key=lambda p: p.area)
            
            # Convert polygon exterior back to line segments
            coords = list(selected_poly.exterior.coords)
            polygon_lines = [
                (tuple(coords[i]), tuple(coords[i + 1]))
                for i in range(len(coords) - 1)
            ]
            result.append(polygon_lines)
        else:
            result.append([])  # No matching polygon found

    return result


def CreateSubDivWalls(lines):
    line_strings = [LineString([start, end]) for start, end in lines]
    return list(polygonize(line_strings))
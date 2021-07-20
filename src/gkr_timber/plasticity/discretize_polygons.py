from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import math
import shapely.geometry

def get_polygon_corner(polygon):
    bottom_z = polygon[0][1]
    top_z = polygon[2][1]
    left_y = polygon[0][0]
    right_y = polygon[1][0]
    return [left_y, right_y, bottom_z, top_z]


def create_rectangle(left_y, right_y, bottom_z, top_z):
    return [[left_y, bottom_z],
            [right_y, bottom_z],
            [right_y, top_z],
            [left_y, top_z]]

# all polygons are in the yOz plane
def measure_polygons_width_along_yaxis(polygons):
    y_intervals = []
    for polygon in polygons:
        y_coordinates = []
        for pt in polygon:
            y_coordinates.append(pt[0])
        y_coordinates.sort()
        y_intervals.append([y_coordinates[0], y_coordinates[-1]])
    return y_intervals

def boolean_intersection_polygon_vertical_rectangle(polygon, y_interval, tolerance = 1E-4):
    z_coordinates = []
    for pt in polygon:
        z_coordinates.append(pt[1])
    z_coordinates.sort()

    vertical_rectangle = create_rectangle(y_interval[0], y_interval[1], z_coordinates[0], z_coordinates[-1])

    shapely_vertical_rectangle = shapely.geometry.Polygon(vertical_rectangle)
    shapely_polygon = shapely.geometry.Polygon(polygon)
    shapely_intersec_polygon =  shapely_polygon.intersection(shapely_vertical_rectangle)

    intersection = []
    for pt in shapely_intersec_polygon.exterior.coords:
        intersection.append([pt[0], pt[1]])

    # find the maximum rectange inside the intersection polygon
    pt_at_left_z = []
    pt_at_right_z = []
    for pt in intersection:
        if abs(pt[0] - y_interval[0]) < tolerance:
            pt_at_left_z.append(pt[1])
        if (abs(pt[0] - y_interval[1]) < tolerance):
            pt_at_right_z.append(pt[1])

    rectangle_minimum_z = max(min(pt_at_left_z), min(pt_at_right_z))
    rectangle_maximum_z = min(max(pt_at_left_z), max(pt_at_right_z))

    maximize_inscribe_rectangle = create_rectangle(y_interval[0], y_interval[1], rectangle_minimum_z, rectangle_maximum_z)

    return maximize_inscribe_rectangle

def measure_polygon_area(poly):
    shapely_poly = shapely.geometry.Polygon(poly)
    return shapely_poly.area

def draw_polygons_wireframe(polygons):
    import matplotlib.pyplot as plt
    plt.figure()
    for id in range(0, len(polygons)):
        poly_coord = polygons[id]
        coord = poly_coord.copy()
        coord.append(coord[0])  # repeat the first point to create a 'closed loop'
        xs, ys = zip(*coord)  # create lists of x and y values
        plt.plot(xs, ys, color="black")
    plt.show()

def draw_polygons_with_strengths(polygons, strength, strength_min = 0, strength_max = 2):
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    import matplotlib.cm as cmx

    jet = cm = plt.get_cmap('jet')
    cNorm = colors.Normalize(vmin=strength_min, vmax=strength_max)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

    plt.figure()

    for id in range(0, len(polygons)):
        poly_coord = polygons[id]
        coord = poly_coord.copy()
        coord.append(coord[0])  # repeat the first point to create a 'closed loop'
        xs, ys = zip(*coord)  # create lists of x and y values
        plt.plot(xs, ys, color="black")

        colorVal = scalarMap.to_rgba(strength[id])
        plt.fill(xs, ys, color=colorVal)

    plt.colorbar(scalarMap, label="Strength", orientation="vertical")
    plt.show()

def slice_polygons_vertically_with_intervals(polygons,
                              polygons_strengths,
                              slice_y_intervals):

    polygons_yaxis_intervals = measure_polygons_width_along_yaxis(polygons)

    polygons_intersec_shapes = []
    polygons_intersec_strengths = []

    for slice_intv in slice_y_intervals:

        for id in range(0, len(polygons)):
            polygon = polygons[id]
            polygon_x_interval = polygons_yaxis_intervals[id]
            strength = polygons_strengths[id]

            if polygon_x_interval[1] >= slice_intv[1] and slice_intv[0] >= polygon_x_interval[0]:

                intersection = boolean_intersection_polygon_vertical_rectangle(polygon, slice_intv)

                polygons_intersec_shapes.append(intersection)
                polygons_intersec_strengths.append(strength)

    return [polygons_intersec_shapes, polygons_intersec_strengths]


def slice_polygons_vertically(polygons,
                              polygons_strengths,
                              resolution,
                              tolerance = 1E-4):
    """
    Slice given polygons into thin strips and projected into 2D
    """

    # the intervals of polygons projected into X axis
    x_intervals = measure_polygons_width_along_yaxis(polygons)

    # the x value of intervals (ascend)
    x_endpoints = [0]
    for intv in x_intervals:
        x_endpoints.append(intv[0])
        x_endpoints.append(intv[1])

    x_endpoints = list(set(x_endpoints))
    x_endpoints.sort()

    # compute all possible candidate intervals
    candidate_intervals = []
    for id in range(0, len(x_endpoints) - 1):

        interval_left_x =  x_endpoints[id]
        interval_right_x = x_endpoints[id + 1]

        # in some intervals, the polygons may have zero projection area
        # we ignore these intervals to accelerate our program
        is_interval_valid = False

        for intv in x_intervals:
            if interval_left_x > intv[1] - tolerance or interval_right_x < intv[0] + tolerance:
                is_interval_valid = False
            else:
                is_interval_valid = True
                break

        if is_interval_valid == False:
            continue

        interval_width = interval_right_x - interval_left_x
        # if the interval width is smaller than the fabrication tolerance, we ignore this interval
        if interval_width < tolerance:
            continue

        num_segments = math.ceil(interval_width / resolution)

        for kd in range(0, num_segments):
            segment_left_x = interval_left_x + interval_width / num_segments * kd
            segment_right_x = interval_left_x + interval_width / num_segments * (kd + 1)
            candidate_intervals.append([segment_left_x, segment_right_x])

    [polygons_intersec_shapes, polygons_intersec_strengths] = slice_polygons_vertically_with_intervals(polygons, polygons_strengths, candidate_intervals)

    return [polygons_intersec_shapes, polygons_intersec_strengths]

def squarize_rectangle(left_y, right_y, bottom_z, top_z, resolution, tolerance):
    height = top_z - bottom_z
    number_of_squares = math.floor(height / resolution)

    squares = []

    for kd in range(0, number_of_squares):
        square = create_rectangle(left_y, right_y, bottom_z + kd * resolution, bottom_z + (kd + 1) * resolution)
        squares.append(square)

        # leftover
        if top_z - (bottom_z + number_of_squares * resolution) > tolerance:
            square = create_rectangle(left_y, right_y, bottom_z + number_of_squares * resolution, top_z)
            squares.append(square)

    return squares

def squarize_polygons(polygons,
                      polygons_strengths,
                      resolution,
                      tolerance = 1E-4):

    [slice_polygons, slice_polygons_strengths] = slice_polygons_vertically(polygons, polygons_strengths, resolution, tolerance)

    squares_shapes = []
    squares_strength = []

    for id in range(0, len(slice_polygons)):
        polygon = slice_polygons[id]
        [left_y, right_y, bottom_z, top_z] = get_polygon_corner(polygon)

        squares = []
        if bottom_z <= 0 and top_z > 0:
            squares0 = squarize_rectangle(left_y, right_y, bottom_z, 0, resolution, tolerance)
            squares1 = squarize_rectangle(left_y, right_y, 0, top_z, resolution, tolerance)
            squares = [*squares0, *squares1]
        else:
            squares = squarize_rectangle(left_y, right_y, bottom_z, top_z, resolution, tolerance)

        for square in squares:
            squares_shapes.append(square)
            squares_strength.append(slice_polygons_strengths[id])


    return [squares_shapes, squares_strength]

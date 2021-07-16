from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import math
import shapely.geometry

def project_2Dregion_into_x_intervals(region_2Dpolygon_list):
    x_intervals = []
    for polygon in region_2Dpolygon_list:
        x_coordinates = []
        for pt in polygon:
            x_coordinates.append(pt[0])
        x_coordinates.sort()
        x_intervals.append([x_coordinates[0], x_coordinates[-1]])
    return x_intervals

def boolean_intersection_poly_and_interval(poly, interval, conservative = True):
    y_coordinates = []
    for pt in poly:
        y_coordinates.append(pt[1])
    y_coordinates.sort()

    interval_box = [[interval[0], y_coordinates[0]],
                    [interval[1], y_coordinates[0]],
                    [interval[1], y_coordinates[-1]],
                    [interval[0], y_coordinates[-1]]];

    shapely_interval_box = shapely.geometry.Polygon(interval_box)
    shapely_poly = shapely.geometry.Polygon(poly)
    shapely_intersec_poly =  shapely_poly.intersection(shapely_interval_box)

    intersec_poly = []
    for pt in shapely_intersec_poly.exterior.coords:
        intersec_poly.append([pt[0], pt[1]])

    if conservative:
        eps = 1E-4
        left_y = []
        right_y = []
        for pt in intersec_poly:
            if (abs(pt[0] - interval[0]) < eps):
                left_y.append(pt[1])
            if (abs(pt[0] - interval[1]) < eps):
                right_y.append(pt[1])

        poly_minimum_y = max(min(left_y), min(right_y))
        poly_maximum_y = min(max(left_y), max(right_y))

        intersec_poly = [
            [interval[0], poly_minimum_y],
            [interval[1], poly_minimum_y],
            [interval[1], poly_maximum_y],
            [interval[0], poly_maximum_y]
        ]

    return intersec_poly


def compute_poly_area(poly):
    shapely_poly = shapely.geometry.Polygon(poly)
    return shapely_poly.area

def boolean_intersection_2Dregion_with_x_intervals(region_2Dpolygon_list,
                                                   region_strength,
                                                   candidate_intervals):
    x_intervals = project_2Dregion_into_x_intervals(region_2Dpolygon_list)

    polygon_intersec_shapes = []
    polygon_intersec_heights = []
    polygon_intersec_strength = []

    for intv in candidate_intervals:
        intv_poly_intersection_shape = []
        intv_poly_strength = []
        inv_poly_intersection_height = []

        intv_width = intv[1] - intv[0]

        for id in range(0, len(region_2Dpolygon_list)):
            if x_intervals[id][1] >= intv[1] and intv[0] >= x_intervals[id][0]:

                poly = region_2Dpolygon_list[id]
                intersec_poly = boolean_intersection_poly_and_interval(poly, intv)
                intv_poly_intersection_shape.append(intersec_poly)

                intv_poly_strength.append(region_strength[id])

                poly_area = compute_poly_area(intersec_poly)
                inv_poly_intersection_height.append(poly_area / intv_width)

        polygon_intersec_shapes.append(intv_poly_intersection_shape)
        polygon_intersec_heights.append(inv_poly_intersection_height)
        polygon_intersec_strength.append(intv_poly_strength)

    return [polygon_intersec_shapes, polygon_intersec_strength, polygon_intersec_heights]

def draw_2Dregion_wireframe(polygons):
    import matplotlib.pyplot as plt
    plt.figure()

    for id in range(0, len(polygons)):
        poly_coord = polygons[id]
        coord = poly_coord.copy()
        coord.append(coord[0])  # repeat the first point to create a 'closed loop'
        xs, ys = zip(*coord)  # create lists of x and y values
        plt.plot(xs, ys, color="black")

    plt.show()  # if you need...
def draw_2Dregion(polygons, strength, strength_min = 0, strength_max = 2):
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
    plt.show()  # if you need...

def draw_2Dregion_from_slicing(slice_result, strength_min = 0, strength_max = 2):
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    import matplotlib.cm as cmx

    jet = cm = plt.get_cmap('jet')
    cNorm = colors.Normalize(vmin=strength_min, vmax=strength_max)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

    plt.figure()

    for id in range(0, len(slice_result["shapes"])):
        poly_interval = slice_result["shapes"][id]
        for jd in range(0, len(poly_interval)):
            poly_coord = poly_interval[jd]
            coord = poly_coord.copy()
            coord.append(coord[0])  # repeat the first point to create a 'closed loop'
            xs, ys = zip(*coord)  # create lists of x and y values
            plt.plot(xs, ys, color = "black")

            colorVal = scalarMap.to_rgba(slice_result["strength"][id][jd])
            plt.fill(xs, ys, color = colorVal)

    plt.colorbar(scalarMap, label="Strength", orientation="vertical")
    plt.show()  # if you need...

def slice_2Dregion_into_1Dsegment(region_2Dpolygon_list,
                                  region_strength,
                                  minimum_segment_width,
                                  tolerance = 1E-4):
    """
    Slice given polygons into thin strips and projected into 2D
    """

    # the intervals of polygons projected into X axis
    x_intervals = project_2Dregion_into_x_intervals(region_2Dpolygon_list)

    # the x value of intervals (ascend)
    #x_endpoints = [0]
    x_endpoints = []
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

        num_segments = math.ceil(interval_width / minimum_segment_width)

        for kd in range(0, num_segments):
            segment_left_x = interval_left_x + interval_width / num_segments * kd
            segment_right_x = interval_left_x + interval_width / num_segments * (kd + 1)
            candidate_intervals.append([segment_left_x, segment_right_x])

    [polygon_intersec_shapes, polygon_intersec_strength, polygon_intersec_heights] = boolean_intersection_2Dregion_with_x_intervals(region_2Dpolygon_list, region_strength, candidate_intervals)
    return {"intervals" : candidate_intervals,
            "shapes" : polygon_intersec_shapes,
            "strength" : polygon_intersec_strength,
            "heights" : polygon_intersec_heights}

def slice_2Dregion_into_squares(region_2Dpolygon_list,
                                region_strength,
                                resolution,
                                tolerance = 1E-4):

    result = slice_2Dregion_into_1Dsegment(region_2Dpolygon_list, region_strength, resolution, tolerance)

    squares_shapes = []
    squares_strength = []

    shapes = result["shapes"]
    strengths = result["strength"]
    for id in range(0, len(shapes)):
        for jd in range(0, len(shapes[id])):
            poly = shapes[id][jd]
            bottom_y = poly[0][1]
            top_y = poly[2][1]
            left_x = poly[0][0]
            right_x = poly[1][0]
            height = top_y - bottom_y
            num_square = math.floor(height / resolution)
            for kd in range(0, num_square):
                sub_poly = [[left_x, bottom_y + kd * resolution],
                        [right_x, bottom_y + kd * resolution],
                        [right_x, bottom_y + (kd + 1) * resolution],
                        [left_x, bottom_y + (kd + 1) * resolution]]
                sub_strength = strengths[id][jd]
                squares_shapes.append(sub_poly)
                squares_strength.append(sub_strength)

            # leftover
            if top_y - (bottom_y + num_square * resolution) > 1E-4:
                squares_shapes.append([[left_x, bottom_y + num_square * resolution],
                                   [right_x, bottom_y + num_square * resolution],
                                   [right_x, top_y],
                                   [left_x, top_y]])
                squares_strength.append(strengths[id][jd])

    return {"shapes" : squares_shapes,
            "strength" : squares_strength}

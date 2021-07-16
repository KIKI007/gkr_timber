import pytest
import compas
from gkr_timber.plasticity import discretize_region
from gkr_timber.plasticity import strength_evaluation_3D
from gkr_timber.plasticity import strength_evaluation_2D

#Case 1
# polygons_positive = [[[-0.15, 0], [1, 0], [1, 1], [-0.15, 1]],
#                         [[2, 0], [3, 0], [3, 2], [2, 2]],
#                         [[0, 1.5], [1.5, 1.5], [0, 2.5]]]
#
#     strength_positive = [1, 2, 1.5]
#
#     polygons_negative = [[[-2, 0], [1, 0], [1, 1], [-2, 1]]]
#     strength_negative = [1.3]

#Case 2
# polygons_positive = [[[-1.5, -1], [-1, -1], [-1, 1], [-1.5, 1]],
#                      [[-1, 0], [1, 0], [1, 1], [-1, 1]],
#                      [[1, -1], [2, -1], [2, 1], [1, 1]]]
#
# strength_positive = [1, 2, 1]
#
# polygons_negative = [[[-1.5, -1], [-1, -1], [-1, 1], [-1.5, 1]],
#                      [[-1, 0], [1, 0], [1, 1], [-1, 1]],
#                      [[1, -1], [2, -1], [2, 1], [1, 1]]]

#Case 3
# polygons_positive = [
#     [[-1, 0], [2, 0], [2, 1], [-1, 1]],
# ]
# strength_positive = [1]
#
# polygons_negative = [[[-2, 0], [1, 0], [1, 1], [-2, 1]]]
# strength_negative = [2]
#

def test_discretize_region3D():
    polygons_positive = [[[-1.5, -1], [-1, -1], [-1, 1], [-1.5, 1]],
                     [[-1, 0], [1, 0], [1, 1], [-1, 1]],
                     [[1, -1], [2, -1], [2, 1], [1, 1]]]

    strength_positive = [1, 2, 1]

    polygons_negative = [[[-1.5, -1], [-1, -1], [-1, 1], [-1.5, 1]],
                     [[-1, 0], [1, 0], [1, 1], [-1, 1]],
                     [[1, -1], [2, -1], [2, 1], [1, 1]]]

    strength_negative = [1, 2, 1]
    minimum_segment_width = 0.1

    #squares_region_positive = discretize_region.slice_2Dregion_into_squares(polygons_positive, strength_positive, minimum_segment_width, 1E-4)
    #discretize_region.draw_2Dregion(squares_region_positive["shapes"], squares_region_positive["strength"])

    #squares_region_negative = discretize_region.slice_2Dregion_into_squares(polygons_negative, strength_negative, minimum_segment_width, 1E-4)
    #discretize_region.draw_2Dregion(squares_region_negative["shapes"], squares_region_negative["strength"])

    #Evaluation
    result = strength_evaluation_3D.evaluate_joint_strength_3D(polygons_positive,
                                                   strength_positive,
                                                   polygons_negative,
                                                   strength_negative,
                                                   0,
                                                   0.0,
                                                   6.0,
                                                   minimum_segment_width)

    if result["stable"] == True:
        strength_evaluation_3D.draw_3D_partition_result(result)

def draw_3D_cell():
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    plt.figure()
    left_y = 0
    right_y = 1
    bottom_z = 0
    top_z = 1

    area_bending_y = 0.8
    area_bending_z = 0.1
    area_force_x = 0

    force_polygons = []
    colors = []

    # region bending y
    y_bending_z_height = area_bending_y / (right_y - left_y) / 2
    y_bending_z_range = [bottom_z + y_bending_z_height, top_z - y_bending_z_height]
    if y_bending_z_height > 1E-5:
        force_polygons.append([[left_y, bottom_z], [right_y, bottom_z], [right_y, y_bending_z_range[0]], [left_y, y_bending_z_range[0]]])
        force_polygons.append([[left_y, y_bending_z_range[1]], [right_y, y_bending_z_range[1]], [right_y, top_z], [left_y, top_z]])
        colors.append("yellow")
        colors.append("yellow")

    # region bending y
    z_bending_z_height = top_z - bottom_z - y_bending_z_height * 2
    if z_bending_z_height > 1E-5:
        z_bending_y_width = area_bending_z / (z_bending_z_height) / 2
        z_bending_y_range = [left_y + z_bending_y_width, right_y - z_bending_y_width]
        if z_bending_y_width > 1E-5:
            force_polygons.append([[left_y, y_bending_z_range[0]],
                                   [z_bending_y_range[0], y_bending_z_range[0]],
                                   [z_bending_y_range[0], y_bending_z_range[1]],
                                   [left_y, y_bending_z_range[1]]])
            force_polygons.append([[z_bending_y_range[1], y_bending_z_range[0]],
                                   [right_y, y_bending_z_range[0]],
                                   [right_y, y_bending_z_range[1]],
                                   [z_bending_y_range[1], y_bending_z_range[1]]])
            colors.append("red")
            colors.append("red")

    # region force x
    x_force_y_width = z_bending_y_range[1] - z_bending_y_range[0]
    if x_force_y_width > 1E-5:
        x_force_z_height = area_force_x / x_force_y_width
        if x_force_z_height > 1E-5:
            force_polygons.append([[z_bending_y_range[0], y_bending_z_range[0]],
                                   [z_bending_y_range[1], y_bending_z_range[0]],
                                   [z_bending_y_range[1], y_bending_z_range[0] + x_force_z_height],
                                   [z_bending_y_range[0], y_bending_z_range[0] + x_force_z_height]])
            colors.append("blue")

    color_index = 0
    for poly_coord in force_polygons:
        coord = poly_coord.copy()
        coord.append(coord[0])  # repeat the first point to create a 'closed loop'
        xs, ys = zip(*coord)  # create lists of x and y values
        plt.fill(xs, ys, color=colors[color_index])
        color_index += 1

    custom_lines = [Line2D([0], [0], color="blue", lw=4),
                    Line2D([0], [0], color="red", lw=4),
                    Line2D([0], [0], color="yellow", lw=4)]

    ax = plt.gca()
    ax.legend(custom_lines, ['X Force Region', 'Y Bending Region', 'Z Bending Region'])
    plt.show()

def test_discretize_region():


    polygons_positive = [[[-1.5, -1], [-1, -1], [-1, 1], [-1.5, 1]],
                     [[-1, 0], [1, 0], [1, 1], [-1, 1]],
                     [[1, -1], [2, -1], [2, 1], [1, 1]]]

    strength_positive = [1, 2, 1]

    polygons_negative = [[[-1.5, -1], [-1, -1], [-1, 1], [-1.5, 1]],
                     [[-1, 0], [1, 0], [1, 1], [-1, 1]],
                     [[1, -1], [2, -1], [2, 1], [1, 1]]]

    strength_negative = [1, 2, 1]
    minimum_segment_width = 0.1

    # # Visualize region
    discretize_region.draw_2Dregion_wireframe(polygons_positive)
    discretize_region.draw_2Dregion_wireframe(polygons_negative)
    discretize_region.draw_2Dregion(polygons_positive, strength_positive)
    discretize_region.draw_2Dregion(polygons_negative, strength_negative)
    #
    # # Visualize region slice
    slice_region_positive = discretize_region.slice_2Dregion_into_1Dsegment(polygons_positive, strength_positive, minimum_segment_width, 1E-4)
    slice_region_negative = discretize_region.slice_2Dregion_into_1Dsegment(polygons_negative, strength_negative, minimum_segment_width, 1E-4)

    discretize_region.draw_2Dregion_from_slicing(slice_region_positive)
    discretize_region.draw_2Dregion_from_slicing(slice_region_negative)


    # Evaluation
    # result = strength_evaluation.evaluate_joint_strength_2D(polygons_positive,
    #                                                strength_positive,
    #                                                polygons_negative,
    #                                                strength_negative,
    #                                                -2,
    #                                                1,
    #                                                minimum_segment_width)
    # result = strength_evaluation.measure_joint_maximum_force_strength(polygons_positive,
    #                                                strength_positive,
    #                                                polygons_negative,
    #                                                strength_negative,
    #                                                2,
    #                                                minimum_segment_width)
    # print(result["force_range"])
    # strength_evaluation.draw_partition_result([polygons_positive, polygons_negative],
    #                                           result["slice_region"],
    #                                            result["segment_data"],
    #                                            result["height_force"][0],
    #                                            result["height_bending"][0])
    #
    # strength_evaluation.draw_partition_result([polygons_positive, polygons_negative],
    #                                           result["slice_region"],
    #                                            result["segment_data"],
    #                                            result["height_force"][1],
    #                                            result["height_bending"][1])

    # strength_evaluation.draw_partition_result([polygons_positive, polygons_negative],
    #                                           result["slice_region"],
    #                                           result["segment_data"],
    #                                           result["height_force"],
    #                                           result["height_bending"])
if __name__ == '__main__':
    test_discretize_region3D()

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import cvxpy as cp
import numpy as np

from .discretize_region import slice_2Dregion_into_squares

def obtain_contact_decomposition_from_result(result):

    polygons_bending_y = [[], []]
    polygons_bending_z = [[], []]
    polygons_force_x = [[], []]

    var_index = 0
    for side_index in range(0, 2):
        polygons = result["regions"][side_index]["shapes"]
        for id in range(0, len(polygons)):
            poly_shape = polygons[id]

            left_y = poly_shape[0][0]
            right_y = poly_shape[1][0]
            bottom_z = poly_shape[0][1]
            top_z = poly_shape[2][1]

            area_bending_y = result["area_y_bending"][var_index]
            area_bending_z = result["area_z_bending"][var_index]
            area_force_x = result["area_x_force"][var_index]

            # region bending y
            y_bending_z_height = area_bending_y / (right_y - left_y) / 2
            y_bending_z_range = [bottom_z + y_bending_z_height, top_z - y_bending_z_height]
            if y_bending_z_height > 1E-5:
                polygons_bending_y[side_index].append([[left_y, bottom_z], [right_y, bottom_z], [right_y, y_bending_z_range[0]], [left_y, y_bending_z_range[0]]])
                polygons_bending_y[side_index].append([[left_y, y_bending_z_range[1]], [right_y, y_bending_z_range[1]], [right_y, top_z], [left_y, top_z]])

            # region bending z
            z_bending_z_height = top_z - bottom_z - y_bending_z_height * 2
            z_bending_y_range = [left_y, right_y]
            if z_bending_z_height > 1E-5:
                z_bending_y_width = area_bending_z / (z_bending_z_height) / 2
                z_bending_y_range = [left_y + z_bending_y_width, right_y - z_bending_y_width]
                if z_bending_y_width > 1E-5:
                    polygons_bending_z[side_index].append([[left_y, y_bending_z_range[0]],
                                           [z_bending_y_range[0], y_bending_z_range[0]],
                                           [z_bending_y_range[0], y_bending_z_range[1]],
                                           [left_y, y_bending_z_range[1]]])
                    polygons_bending_z[side_index].append([[z_bending_y_range[1], y_bending_z_range[0]],
                                           [right_y, y_bending_z_range[0]],
                                           [right_y, y_bending_z_range[1]],
                                           [z_bending_y_range[1], y_bending_z_range[1]]])

            # region force x
            x_force_y_width = z_bending_y_range[1] - z_bending_y_range[0]
            if x_force_y_width > 1E-5:
                x_force_z_height = area_force_x / x_force_y_width
                if x_force_z_height > 1E-5:
                    polygons_force_x[side_index].append([[z_bending_y_range[0], y_bending_z_range[0]],
                                           [z_bending_y_range[1], y_bending_z_range[0]],
                                           [z_bending_y_range[1], y_bending_z_range[0] + x_force_z_height],
                                           [z_bending_y_range[0], y_bending_z_range[0] + x_force_z_height]])

            var_index = var_index + 1
    return [polygons_force_x, polygons_bending_y, polygons_bending_z]

def draw_3D_partition_result(result):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    result_polygons = obtain_contact_decomposition_from_result(result)
    for side_index in range(0, 2):
        plt.figure()
        colors = ["blue", "yellow", "red"]
        color_index = 0
        for polygons in [result_polygons[0][side_index], result_polygons[1][side_index], result_polygons[2][side_index]]:
            for poly_coord in polygons:
                coord = poly_coord.copy()
                coord.append(coord[0])  # repeat the first point to create a 'closed loop'
                xs, ys = zip(*coord)  # create lists of x and y values
                plt.fill(xs, ys, color=colors[color_index])

            color_index += 1

        # wireframe
        for poly_coord in result["regions"][side_index]["shapes"]:
            coord = poly_coord.copy()
            coord.append(coord[0])  # repeat the first point to create a 'closed loop'
            xs, ys = zip(*coord)  # create lists of x and y values
            plt.plot(xs, ys, color="black")

        custom_lines = [Line2D([0], [0], color="blue", lw=4),
                        Line2D([0], [0], color="red", lw=4),
                        Line2D([0], [0], color="yellow", lw=4)]

        ax = plt.gca()
        plt.xlabel("Region partition at positive side"
                   if side_index == 0 else "Region partition at negative side", fontsize=10)
        ax.legend(custom_lines, ['X Force Region', 'Z Bending Region', 'Y Bending Region'])
        plt.show()

def obtain_data_for_optimization_3D(region_polygons_positive,
                                    region_strength_positive,
                                    region_polygons_negative,
                                    region_strength_negative,
                                    minimum_segment_width = 0.1,
                                    tolerance = 1E-4):

    result_region_positive = slice_2Dregion_into_squares(region_polygons_positive, region_strength_positive, minimum_segment_width, tolerance)
    result_region_negative = slice_2Dregion_into_squares(region_polygons_negative, region_strength_negative, minimum_segment_width, tolerance)

    regions = [result_region_positive, result_region_negative]

    strength_list = []
    arm_for_bending_y_list = []
    arm_for_benidng_z_list = []
    area_list = []
    positive_Mz_index = []
    positive_My_index = []

    index = 0
    for kd in range(0, 2):
        region = regions[kd]
        sign = 1 if kd == 0 else -1
        for id in range(0, len(region["shapes"])):
            poly = region["shapes"][id]
            height = poly[2][1] - poly[1][1]
            width = poly[1][0] - poly[0][0]
            area = height * width
            strength = region["strength"][id]
            arm_for_bending_y = (poly[2][1] + poly[0][1])/2
            arm_for_bending_z = -(poly[1][0] + poly[0][0])/2

            area_list.append(area)
            arm_for_bending_y_list.append(arm_for_bending_y)
            arm_for_benidng_z_list.append(arm_for_bending_z)
            strength_list.append(strength * sign)

            if sign * arm_for_bending_y >= 0:
                positive_My_index.append(index)

            if sign * arm_for_bending_z >= 0:
                positive_Mz_index.append(index)

            index = index + 1

    return [regions,
            strength_list,
            arm_for_bending_y_list,
            arm_for_benidng_z_list,
            area_list,
            positive_My_index,
            positive_Mz_index]


def evaluate_joint_strength_3D(region_polygons_positive,
                               region_strength_positive,
                               region_polygons_negative,
                               region_strength_negative,
                               force_x,
                               bending_y,
                               bending_z,
                               resolution = 0.1,
                               tolerance = 1E-4):
    [regions, strength_list, arm_for_bending_y_list, arm_for_bending_z_list, area_list, positive_My_index, positive_Mz_index] \
        = obtain_data_for_optimization_3D(region_polygons_positive,
                                       region_strength_positive,
                                       region_polygons_negative,
                                       region_strength_negative,
                                       resolution,
                                       tolerance)

    # assign cell to be zero
    if bending_y < 0:
        indices = positive_Mz_index.copy()
        positive_Mz_index = [1 - x for x in indices]
    if bending_z < 0:
        indices = positive_My_index.copy()
        positive_My_index = [1 - x for x in indices]

    # CVXPY
    n_var = len(strength_list)

    area_force_x_var = cp.Variable(n_var)
    area_bending_z_var = cp.Variable(n_var)
    area_bending_y_var = cp.Variable(n_var)

    area_array = np.array(area_list)
    strength_array = np.array(strength_list)
    arm_for_bending_z_array = np.array(arm_for_bending_z_list)
    arm_for_bending_y_array = np.array(arm_for_bending_y_list)

    objective = cp.Maximize(cp.sum(area_array - area_force_x_var - area_bending_z_var - area_bending_y_var))
    constraints = [
        area_force_x_var.T @ strength_array + force_x == 0,  # force balanced equations,
        arm_for_bending_z_array.T @ cp.multiply(area_bending_z_var, strength_array) + bending_z == 0,  # bending in z axis balanced equations,
        arm_for_bending_y_array.T @ cp.multiply(area_bending_y_var, strength_array) + bending_y == 0,   # bending in y axis balanced equations,
        area_bending_z_var.T @ strength_array == 0,  # contact bending don't create force
        area_bending_y_var.T @ strength_array == 0,  # contact bending don't create force
        area_bending_z_var + area_bending_y_var + area_force_x_var <= area_array,  # maximum usage of contact face area
        0 <= area_bending_y_var,  # non-negative bending area
        0 <= area_bending_z_var,  # non-negative bending area
        0 <= area_force_x_var,  # non-negative force area
        area_bending_y_var[positive_My_index] == 0,
        area_bending_z_var[positive_Mz_index] == 0
    ]

    prob = cp.Problem(objective, constraints)
    prob.solve()

    if prob.status not in ["infeasible", "unbounded"]:
        return {"stable": True,
                "regions": regions,
                "area_x_force": area_force_x_var.value,
                "area_y_bending": area_bending_y_var.value,
                "area_z_bending": area_bending_z_var.value,
                }
    else:
        return {"stable" : False}

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import cvxpy as cp
import numpy as np

from gkr_timber.plasticity.discretize_polygons import squarize_polygons
from gkr_timber.plasticity.discretize_polygons import get_polygon_corner
from gkr_timber.plasticity.discretize_polygons import create_rectangle

def extract_geometry_from_evlaution_3D_result(result, tolerance = 1E-4):

    polygons_bending_y = [[], []]
    polygons_bending_z = [[], []]
    polygons_force_x = [[], []]

    var_index = 0
    for side_index in range(0, 2):
        polygons = result["squares_shapes"][side_index]
        for id in range(0, len(polygons)):
            poly_shape = polygons[id]
            [left_y, right_y, bottom_z, top_z] = get_polygon_corner(poly_shape)

            area_bending_y = result["area_y_bending"][var_index]
            area_bending_z = result["area_z_bending"][var_index]
            area_force_x = result["area_x_force"][var_index]

            # region bending y
            y_bending_z_height = area_bending_y / (right_y - left_y) / 2
            y_bending_z_range = [bottom_z + y_bending_z_height, top_z - y_bending_z_height]
            if y_bending_z_height > tolerance:
                polygons_bending_y[side_index].append(create_rectangle(left_y, right_y, bottom_z, y_bending_z_range[0]))
                polygons_bending_y[side_index].append(create_rectangle(left_y, right_y, y_bending_z_range[1], top_z))

            # region bending z
            z_bending_z_height = top_z - bottom_z - y_bending_z_height * 2
            z_bending_y_range = [left_y, right_y]
            if z_bending_z_height > tolerance:
                z_bending_y_width = area_bending_z / (z_bending_z_height) / 2
                z_bending_y_range = [left_y + z_bending_y_width, right_y - z_bending_y_width]
                if z_bending_y_width > tolerance:
                    polygons_bending_z[side_index].append(create_rectangle(left_y, z_bending_y_range[0], y_bending_z_range[0], y_bending_z_range[1]))
                    polygons_bending_z[side_index].append(create_rectangle(z_bending_y_range[1], right_y, y_bending_z_range[0], y_bending_z_range[1]))

            # region force x
            x_force_y_width = z_bending_y_range[1] - z_bending_y_range[0]
            if x_force_y_width > tolerance:
                x_force_z_height = area_force_x / x_force_y_width
                if x_force_z_height > tolerance:
                    polygons_force_x[side_index].append(create_rectangle(z_bending_y_range[0],
                                                                         z_bending_y_range[1],
                                                                         y_bending_z_range[0],
                                                                         y_bending_z_range[0] + x_force_z_height))

            var_index = var_index + 1
    return [polygons_force_x, polygons_bending_y, polygons_bending_z]

def draw_3D_partition_result(result):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    if result["stable"] == True:
        result_polygons = extract_geometry_from_evlaution_3D_result(result)
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
            for poly_coord in result["squares_shapes"][side_index]:
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

def prepare_data_for_optimization_3D(contacts_shapes,
                                     contacts_strengths,
                                     bending_y,
                                     bending_z,
                                     resolution = 0.1,
                                     tolerance = 1E-4):
    [contact_positive_shapes, contact_negative_shapes] = contacts_shapes
    [contact_positive_strengths, contact_negative_strengths] = contacts_strengths

    [squares_contacts_positive, squares_contacts_positive_strength] = squarize_polygons(contact_positive_shapes, contact_positive_strengths, resolution, tolerance)
    [squares_contacts_negative, squares_contacts_negative_strength] = squarize_polygons(contact_negative_shapes, contact_negative_strengths, resolution, tolerance)

    squares_shapes = [squares_contacts_positive, squares_contacts_negative]
    squares_contacts_strength = [squares_contacts_positive_strength, squares_contacts_negative_strength]

    strength_list = []
    arm_for_bending_y_list = []
    arm_for_benidng_z_list = []
    area_list = []
    bending_z_zero_index = []
    bending_y_zero_index = []

    index = 0
    for kd in range(0, 2):
        squares = squares_shapes[kd]
        sign = 1 if kd == 0 else -1
        for id in range(0, len(squares)):
            poly = squares[id]
            [left_y, right_y, bottom_z, top_z] = get_polygon_corner(poly)
            height = top_z - bottom_z
            width = right_y - left_y
            area = height * width
            strength = squares_contacts_strength[kd][id]
            arm_for_bending_y = (bottom_z + top_z)/2
            arm_for_bending_z = -(left_y + right_y)/2

            area_list.append(area)
            arm_for_bending_y_list.append(arm_for_bending_y)
            arm_for_benidng_z_list.append(arm_for_bending_z)
            strength_list.append(strength * sign)

            if sign * arm_for_bending_y * bending_y >= 0:
                bending_y_zero_index.append(index)

            if sign * arm_for_bending_z * bending_z >= 0:
                bending_z_zero_index.append(index)

            index = index + 1

    return [squares_shapes,
            strength_list,
            arm_for_bending_y_list,
            arm_for_benidng_z_list,
            area_list,
            bending_y_zero_index,
            bending_z_zero_index]


def evaluate_joint_strength_3D(contacts_shapes,
                               contacts_strengths,
                               force_x,
                               bending_y,
                               bending_z,
                               resolution = 0.1,
                               tolerance = 1E-4):

    [squares_shapes, strength_list, arm_for_bending_y_list, arm_for_bending_z_list, area_list, bending_y_zero_index, bending_z_zero_index] \
        = prepare_data_for_optimization_3D(contacts_shapes,
                                           contacts_strengths,
                                           bending_y,
                                           bending_z,
                                           resolution,
                                           tolerance)

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
        area_bending_y_var[bending_y_zero_index] == 0,
        area_bending_z_var[bending_z_zero_index] == 0
    ]

    prob = cp.Problem(objective, constraints)
    prob.solve()

    if prob.status not in ["infeasible", "unbounded"]:
        return {"stable": True,
                "squares_shapes": squares_shapes,
                "area_x_force": area_force_x_var.value,
                "area_y_bending": area_bending_y_var.value,
                "area_z_bending": area_bending_z_var.value,
                }
    else:
        return {"stable" : False}

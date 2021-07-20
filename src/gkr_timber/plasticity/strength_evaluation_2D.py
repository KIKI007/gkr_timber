from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import cvxpy as cp
import numpy as np

from gkr_timber.plasticity.discretize_polygons import create_rectangle
from gkr_timber.plasticity.discretize_polygons import get_polygon_corner
from gkr_timber.plasticity.discretize_polygons import slice_polygons_vertically

def extract_geometry_from_evlaution_2D_result(result, tolerance = 1E-4):
    if result["stable"] == False:
        return [[], []]

    rectangles_shapes = result["rectangles_shapes"]
    contact_force_height = result["contacts_forces_height"]
    contacts_bending_z_height = result["contacts_bending_z_height"]

    polygons_forces = [[], []]
    polygons_bendings = [[], []]
    index = 0
    for side_index in range(0, 2):
        # draw original contact polygons
        for poly_coord in rectangles_shapes[side_index]:

            height_force = contact_force_height[index]
            height_bend = contacts_bending_z_height[index]
            [left_y, right_y, bottom_z, top_z] = get_polygon_corner(poly_coord)

            if height_force > tolerance:
                poly_force = create_rectangle(left_y, right_y, bottom_z, bottom_z + height_force)
                polygons_forces[side_index].append(poly_force)
            if height_bend > tolerance:
                poly_bending = create_rectangle(left_y, right_y, bottom_z + height_force, bottom_z + height_force + height_bend)
                polygons_bendings[side_index].append(poly_bending)

            index = index + 1

    return [polygons_forces, polygons_bendings]

def draw_strength_evaluation_2D_result(result):
    import matplotlib.pyplot as plt
    import shapely.geometry
    from matplotlib.lines import Line2D

    if result["stable"] == False:
        return

    rectangles_shapes = result["rectangles_shapes"]
    contact_force_height = result["contacts_forces_height"]
    contacts_bending_z_height = result["contacts_bending_z_height"]

    index = 0
    for side_index in range(0, 2):
        plt.figure()

        # draw original contact polygons
        for poly_coord in rectangles_shapes[side_index]:
            coord = poly_coord.copy()
            coord.append(coord[0])  # repeat the first point to create a 'closed loop'
            xs, ys = zip(*coord)  # create lists of x and y values
            plt.plot(xs, ys, color="black")

            height_force = contact_force_height[index]
            height_bend = contacts_bending_z_height[index]
            [left_y, right_y, bottom_z, top_z] = get_polygon_corner(poly_coord)

            poly_force = create_rectangle(left_y, right_y, bottom_z, bottom_z + height_force)
            poly_bending = create_rectangle(left_y, right_y, bottom_z + height_force, bottom_z + height_force + height_bend)

            colors = ["blue", "red"]
            color_index = 0
            for poly_coord in [poly_force, poly_bending]:
                coord = poly_coord.copy()
                coord.append(coord[0])  # repeat the first point to create a 'closed loop'
                xs, ys = zip(*coord)  # create lists of x and y values
                plt.fill(xs, ys, color=colors[color_index])
                color_index += 1

            index = index + 1

        custom_lines = [Line2D([0], [0], color="blue", lw=4),
                        Line2D([0], [0], color="red", lw=4)]

        ax = plt.gca()
        plt.xlabel("Region partition at positive side"
                   if side_index == 0 else "Region partition at negative side", fontsize=10)
        ax.legend(custom_lines, ['Force Region', 'Bending Region'])
        plt.show()


def prepare_data_for_optimization_2D(contacts_shapes,
                                     contacts_strengths,
                                     bending_z,
                                     resolution,
                                     tolerance = 1E-4):
    [contact_positive_shapes, contact_negative_shapes] = contacts_shapes
    [contact_positive_strengths, contact_negative_strengths] = contacts_strengths

    vertical_slice_contact_positive = slice_polygons_vertically(contact_positive_shapes, contact_positive_strengths, resolution, tolerance)
    vertical_slice_contact_negative = slice_polygons_vertically(contact_negative_shapes, contact_negative_strengths, resolution, tolerance)

    vertical_slices = [vertical_slice_contact_positive, vertical_slice_contact_negative]

    rectangles_shapes = [[], []]
    rectangle_widths_y = []
    rectangles_strengths = []
    rectangles_heights = []
    rectangles_torque_arm_y = []
    bending_zero_indices = []

    index = 0
    for kd in range(0, 2):
        [slice_polygons, slice_strength] = vertical_slices[kd]
        sign = 1 if kd == 0 else -1

        for id in range(0, len(slice_polygons)):
            polygon = slice_polygons[id]
            strength = slice_strength[id]
            [left_y, right_y, bottom_z, top_z] = get_polygon_corner(polygon)
            torque_arm_y = -(left_y + right_y) / 2
            width_y = (right_y - left_y)

            rectangles_shapes[kd].append(polygon)
            rectangles_strengths.append(strength * sign * width_y)
            rectangles_heights.append(top_z - bottom_z)
            rectangles_torque_arm_y.append(torque_arm_y)
            rectangle_widths_y.append(width_y)

            if (torque_arm_y * sign * bending_z > 0):
                bending_zero_indices.append(index)

            index = index + 1

    return [rectangles_shapes, rectangles_strengths, rectangles_heights, rectangle_widths_y, rectangles_torque_arm_y, bending_zero_indices]

def measure_joint_maximum_force_strength(contacts_shapes,
                                         contacts_strengths,
                                         external_bending_force_z,
                                         resolution,
                                         tolerance = 1E-4):

    # Prepare Data for Optimization
    [rectangles_shapes, rectangles_strengths, rectangles_heights, rectangle_widths_y, rectangles_torque_arm_y, bending_zero_indices] \
        = prepare_data_for_optimization_2D(contacts_shapes,
                                           contacts_strengths,
                                           external_bending_force_z,
                                           resolution,
                                           tolerance)

    # CVXPY
    n_var = len(rectangles_heights)

    external_axial_force = cp.Variable(1)
    contact_force_height_var = cp.Variable(n_var)
    contact_bending_z_height_var = cp.Variable(n_var)

    height_array = np.array(rectangles_heights)
    strength_array = np.array(rectangles_strengths)
    arm_array = np.array(rectangles_torque_arm_y)

    constraints = [
        contact_force_height_var.T @ strength_array + external_axial_force == 0,  # force balanced equations,
        arm_array.T @ cp.multiply(contact_bending_z_height_var, strength_array) + external_bending_force_z == 0,  # bending balanced equations,
        contact_bending_z_height_var.T @ strength_array == 0,  # contact bending don't create force
        contact_force_height_var + contact_bending_z_height_var <= height_array,  # maximum usage of contact face area
        0 <= contact_force_height_var,  # non-negative bending area
        0 <= contact_bending_z_height_var,  # non-negative force area
        contact_bending_z_height_var[bending_zero_indices] == 0.0,  # zero bending
    ]

    prob1 = cp.Problem(cp.Maximize(external_axial_force), constraints)
    prob1.solve()
    max_external_axial_force = external_axial_force.value[0]
    max_force_height_force_var = contact_force_height_var.value
    max_force_height_bend_var = contact_bending_z_height_var.value

    prob2 = cp.Problem(cp.Minimize(external_axial_force), constraints)
    prob2.solve()
    min_external_axial_force = external_axial_force.value[0]
    min_force_height_force_var = contact_force_height_var.value
    min_force_height_bend_var = contact_bending_z_height_var.value

    if prob1.status not in ["infeasible", "unbounded"] and prob2.status not in ["infeasible", "unbounded"]:
        return {"stable": True,
                "external_axial_force_ranges": [min_external_axial_force, max_external_axial_force],
                "retangles_shapes": rectangles_shapes,
                "contacts_forces_height": [min_force_height_force_var, max_force_height_force_var],
                "contacts_bending_z_height": [min_force_height_bend_var, max_force_height_bend_var]}
    else:
        return {"stable": False}

def evaluate_joint_strength_2D(contacts_shapes,
                               contacts_strengths,
                               external_axial_force,
                               external_bending_force_z,
                               resolution,
                               tolerance = 1E-4):

    # Prepare Data for Optimization
    [rectangles_shapes, rectangles_strengths, rectangles_heights, rectangle_widths_y, rectangles_torque_arm_y, bending_zero_indices] \
        = prepare_data_for_optimization_2D(contacts_shapes,
                                           contacts_strengths,
                                           external_bending_force_z,
                                           resolution,
                                           tolerance)

    # CVXPY
    n_var = len(rectangles_heights)

    contact_force_height_var = cp.Variable(n_var)
    contact_bending_z_height_var = cp.Variable(n_var)

    height_array = np.array(rectangles_heights)
    strength_array = np.array(rectangles_strengths)
    arm_array = np.array(rectangles_torque_arm_y)
    width_array = np.array(rectangle_widths_y)

    constraints = [
        contact_force_height_var.T @ strength_array + external_axial_force == 0,  # force balanced equations,
        arm_array.T @ cp.multiply(contact_bending_z_height_var, strength_array) + external_bending_force_z == 0,  # bending balanced equations,
        contact_bending_z_height_var.T @ strength_array == 0,  # contact bending don't create force
        contact_force_height_var + contact_bending_z_height_var <= height_array,  # maximum usage of contact face area
        0 <= contact_force_height_var,  # non-negative bending area
        0 <= contact_bending_z_height_var,  # non-negative force area
    ]

    if bending_zero_indices != []:
        constraints.append(contact_bending_z_height_var[bending_zero_indices] == 0.0)  # zero bending


    objective = cp.Maximize(width_array.T@(height_array - contact_force_height_var - contact_bending_z_height_var))
    prob = cp.Problem(objective, constraints)
    result = prob.solve()

    if prob.status not in ["infeasible", "unbounded"]:
        return {"stable": True,
                "rectangles_shapes": rectangles_shapes,
                "contacts_forces_height": contact_force_height_var.value,
                "contacts_bending_z_height": contact_bending_z_height_var.value}
    else:
        return {"stable" : False}

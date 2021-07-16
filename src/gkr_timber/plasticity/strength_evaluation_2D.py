from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import cvxpy as cp
import numpy as np

from .discretize_region import slice_2Dregion_into_1Dsegment

def get_partition_result(polygons,
                          region_slice,
                          segment_data,
                          height_force,
                          height_bending):
    import shapely.geometry
    polys_force = [[], []]
    polys_bending = [[], []]
    for side_index in range(0, 2):

        # draw partitioned contact regions
        for id in range(0, len(segment_data)):

            slice_index = segment_data[id][0]
            interval_index = segment_data[id][1]
            poly_index = segment_data[id][2]

            if slice_index != side_index:
                continue

            poly = region_slice[slice_index]["shapes"][interval_index][poly_index]
            poly_shapely = shapely.geometry.Polygon(poly)

            interval = region_slice[slice_index]["intervals"][interval_index]

            cy = poly_shapely.centroid.y
            tot_height = region_slice[slice_index]["heights"][interval_index][poly_index]
            bottom_y = cy - tot_height / 2
            force_y = bottom_y + height_force[id]
            bending_y = force_y + height_bending[id]

            poly_force = [[interval[0], bottom_y],
                          [interval[1], bottom_y],
                          [interval[1], force_y],
                          [interval[0], force_y]]

            poly_bending = [[interval[0], force_y],
                            [interval[1], force_y],
                            [interval[1], bending_y],
                            [interval[0], bending_y]]

            if height_force[id] > 1e-4:
                polys_force[side_index].append(poly_force)
            if height_bending[id] > 1e-4:
                polys_bending[side_index].append(poly_bending)


    return {"polys_force": polys_force, "polys_bending" : polys_bending}

def draw_partition_result(polygons,
                          region_slice,
                          segment_data,
                          height_force,
                          height_bending):
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    import matplotlib.cm as cmx
    import shapely.geometry
    from matplotlib.lines import Line2D


    for side_index in range(0, 2):
        plt.figure()

        # draw original contact polygons
        for poly_coord in polygons[side_index]:
            coord = poly_coord.copy()
            coord.append(coord[0])  # repeat the first point to create a 'closed loop'
            xs, ys = zip(*coord)  # create lists of x and y values
            plt.plot(xs, ys, color="black")

        # draw partitioned contact regions
        for id in range(0, len(segment_data)):
            slice_index = segment_data[id][0]
            interval_index = segment_data[id][1]
            poly_index = segment_data[id][2]

            if slice_index != side_index:
                continue

            poly = region_slice[slice_index]["shapes"][interval_index][poly_index]
            poly_shapely = shapely.geometry.Polygon(poly)

            interval = region_slice[slice_index]["intervals"][interval_index]

            cy = poly_shapely.centroid.y
            tot_height = region_slice[slice_index]["heights"][interval_index][poly_index]
            bottom_y = cy - tot_height / 2
            force_y = bottom_y + height_force[id]
            bending_y = force_y + height_bending[id]

            poly_force = [[interval[0], bottom_y],
                          [interval[1], bottom_y],
                          [interval[1], force_y],
                          [interval[0], force_y]]

            poly_bending = [[interval[0], force_y],
                            [interval[1], force_y],
                            [interval[1], bending_y],
                            [interval[0], bending_y]]

            colors = ["blue", "red"]
            color_index = 0
            for poly_coord in [poly_force, poly_bending]:
                coord = poly_coord.copy()
                coord.append(coord[0])  # repeat the first point to create a 'closed loop'
                xs, ys = zip(*coord)  # create lists of x and y values
                plt.fill(xs, ys, color=colors[color_index])
                color_index += 1

        custom_lines = [Line2D([0], [0], color="blue", lw=4),
                        Line2D([0], [0], color="red", lw=4)]

        ax = plt.gca()
        plt.xlabel("Region partition at positive side"
                   if side_index == 0 else "Region partition at negative side", fontsize=10)
        ax.legend(custom_lines, ['Force Region', 'Bending Region'])
        plt.show()


def obtain_data_for_optimization_2D(region_polygons_positive,
                                    region_strength_positive,
                                    region_polygons_negative,
                                    region_strength_negative,
                                    minimum_segment_width = 0.1,
                                    tolerance = 1E-4):

    slice_region_positive = slice_2Dregion_into_1Dsegment(region_polygons_positive, region_strength_positive, minimum_segment_width, tolerance)
    slice_region_negative = slice_2Dregion_into_1Dsegment(region_polygons_negative, region_strength_negative, minimum_segment_width, tolerance)

    slice_region = [slice_region_positive, slice_region_negative]

    strength_list = []
    height_list = []
    width_list = []
    arm_length_list = []
    segment_data = []
    force_bending_zero_index = []

    for kd in range(0, 2):
        slice = slice_region[kd]
        sign = 1 if kd == 0 else -1
        for id in range(0, len(slice["shapes"])):
            interval_sta = slice["intervals"][id][0]
            interval_end = slice["intervals"][id][1]
            width_interval = interval_end - interval_sta
            arm_length = (interval_sta + interval_end) / 2

            poly_interval = slice["shapes"][id]
            for jd in range(0, len(poly_interval)):
                strength_poly = slice["strength"][id][jd]
                height_poly = slice["heights"][id][jd]
                width_list.append(width_interval)
                strength_list.append(strength_poly * sign * width_interval)
                height_list.append(height_poly)
                arm_length_list.append(arm_length)
                segment_data.append([kd, id, jd])

                if (arm_length * sign < 0):
                    force_bending_zero_index.append(len(segment_data) - 1)

    return [slice_region,
            strength_list,
            height_list,
            width_list,
            arm_length_list,
            segment_data,
            force_bending_zero_index]

def measure_joint_maximum_force_strength(region_polygons_positive,
                                           region_strength_positive,
                                           region_polygons_negative,
                                           region_strength_negative,
                                           bending_z,
                                           minimum_segment_width = 0.1,
                                           tolerance = 1E-4):
    #Obtain Data for Optimization
    [slice_region, strength_list, height_list, width_list, arm_length_list, segment_data, force_bending_zero_index] \
        = obtain_data_for_optimization_2D(region_polygons_positive,
                                       region_strength_positive,
                                       region_polygons_negative,
                                       region_strength_negative,
                                       minimum_segment_width,
                                       tolerance)
    # CVXPY
    n_var = len(height_list)

    force_x = cp.Variable(1)
    height_force_var = cp.Variable(n_var)
    height_bending_var = cp.Variable(n_var)

    height_array = np.array(height_list)
    strength_array = np.array(strength_list)
    arm_array = np.array(arm_length_list)

    constraints = [
        height_force_var.T @ strength_array + force_x == 0,  # force balanced equations,
        arm_array.T @ cp.multiply(height_bending_var, strength_array) + bending_z == 0,  # bending balanced equations,
        height_bending_var.T @ strength_array == 0,  # contact bending don't create force
        height_bending_var + height_force_var <= height_array,  # maximum usage of contact face area
        0 <= height_bending_var,  # non-negative bending area
        0 <= height_force_var,  # non-negative force area
        #height_bending_var[force_bending_zero_index] == 0.0,  # zero bending
    ]

    prob1 = cp.Problem(cp.Maximize(force_x), constraints)
    prob1.solve()
    max_force_value = force_x.value[0]
    max_force_height_force_var = height_force_var.value
    max_force_height_bend_var = height_bending_var.value

    prob2 = cp.Problem(cp.Minimize(force_x), constraints)
    prob2.solve()
    min_force_value = force_x.value[0]
    min_force_height_force_var = height_force_var.value
    min_force_height_bend_var = height_bending_var.value

    if prob1.status not in ["infeasible", "unbounded"] and prob2.status not in ["infeasible", "unbounded"]:
        return {"success": True,
                "force_range": [min_force_value, max_force_value],
                "slice_region": slice_region,
                "segment_data": segment_data,
                "height_force": [min_force_height_force_var, max_force_height_force_var],
                "height_bending": [min_force_height_bend_var, max_force_height_bend_var]}
    else:
        return {"success": False}


def measure_joint_maximum_bending_strength(region_polygons_positive,
                                           region_strength_positive,
                                           region_polygons_negative,
                                           region_strength_negative,
                                           force_x,
                                           minimum_segment_width = 0.1,
                                           tolerance = 1E-4):

    [slice_region, strength_list, height_list, width_list, arm_length_list, segment_data, force_bending_zero_index] \
        = obtain_data_for_optimization_2D(region_polygons_positive,
                                       region_strength_positive,
                                       region_polygons_negative,
                                       region_strength_negative,
                                       minimum_segment_width,
                                       tolerance)
    # CVXPY
    n_var = len(height_list)

    bending_z = cp.Variable(1)
    height_force_var = cp.Variable(n_var)
    height_bending_var = cp.Variable(n_var)

    height_array = np.array(height_list)
    strength_array = np.array(strength_list)
    arm_array = np.array(arm_length_list)

    constraints = [
        height_force_var.T @ strength_array + force_x == 0,  # force balanced equations,
        arm_array.T @ cp.multiply(height_bending_var, strength_array) + bending_z == 0,  # bending balanced equations,
        height_bending_var.T @ strength_array == 0,  # contact bending don't create force
        height_bending_var + height_force_var <= height_array,  # maximum usage of contact face area
        0 <= height_bending_var,  # non-negative bending area
        0 <= height_force_var,  # non-negative force area
        #height_bending_var[force_bending_zero_index] == 0.0,  # zero bending
    ]

    prob1 = cp.Problem(cp.Maximize(bending_z), constraints)
    prob1.solve()
    max_bending_value = bending_z.value[0]
    max_bending_force_var = height_force_var.value
    max_bending_bend_var = height_bending_var.value

    prob2 = cp.Problem(cp.Minimize(bending_z), constraints)
    prob2.solve()
    min_bending_value = bending_z.value[0]
    min_bending_force_var = height_force_var.value
    min_bending_bend_var = height_bending_var.value

    if prob1.status not in ["infeasible", "unbounded"] and prob2.status not in ["infeasible", "unbounded"]:
        return {"success": True,
                "bending_range" : [min_bending_value, max_bending_value],
                "slice_region": slice_region,
                "segment_data": segment_data,
                "height_force": [min_bending_force_var, max_bending_force_var],
                "height_bending": [min_bending_bend_var, max_bending_bend_var]}
    else:
        return {"success" : False}


def evaluate_joint_strength_2D(region_polygons_positive,
                               region_strength_positive,
                               region_polygons_negative,
                               region_strength_negative,
                               force_x,
                               bending_z,
                               minimum_segment_width = 0.1,
                               tolerance = 1E-4):

    [slice_region, strength_list, height_list, width_list, arm_length_list, segment_data, force_bending_zero_index] \
        = obtain_data_for_optimization_2D(region_polygons_positive,
                                       region_strength_positive,
                                       region_polygons_negative,
                                       region_strength_negative,
                                       minimum_segment_width,
                                       tolerance)

    #CVXPY
    n_var = len(height_list)

    height_force_var = cp.Variable(n_var)
    height_bending_var = cp.Variable(n_var)

    height_array = np.array(height_list)
    strength_array = np.array(strength_list)
    arm_array = np.array(arm_length_list)
    width_array = np.array(width_list)

    objective = cp.Maximize(width_array.T@(height_array - height_force_var - height_bending_var))
    constraints = [
        height_force_var.T@strength_array + force_x == 0, # force balanced equations,
        arm_array.T@cp.multiply(height_bending_var, strength_array) + bending_z == 0, #bending balanced equations,
        height_bending_var.T@strength_array == 0, # contact bending don't create force
        height_bending_var + height_force_var <= height_array, # maximum usage of contact face area
        0 <= height_bending_var, # non-negative bending area
        0 <= height_force_var, # non-negative force area
        #height_bending_var[force_bending_zero_index] == 0.0, # zero bending
        ]

    prob = cp.Problem(objective, constraints)
    result = prob.solve()

    if prob.status not in ["infeasible", "unbounded"]:
        return {"stable": True,
                "slice_region": slice_region,
                "segment_data": segment_data,
                "height_force": height_force_var.value,
                "height_bending": height_bending_var.value}
    else:
        return {"stable" : False}

import pytest
import compas
from gkr_timber.plasticity import discretize_region
from gkr_timber.plasticity import strength_evaluation

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

def test_discretize_region():
    polygons_positive = [
        [[-1, 0], [2, 0], [2, 1], [-1, 1]],
    ]
    strength_positive = [1]

    polygons_negative = [[[-2, 0], [1, 0], [1, 1], [-2, 1]]]
    strength_negative = [2]

    minimum_segment_width = 0.1

    # # Visualize region
    # discretize_region.draw_2Dregion(polygons_positive, strength_positive)
    # discretize_region.draw_2Dregion(polygons_negative, strength_negative)
    #
    # # Visualize region slice
    # slice_region_positive = discretize_region.slice_2Dregion_into_1Dsegment(polygons_positive, strength_positive, minimum_segment_width, 1E-4)
    # slice_region_negative = discretize_region.slice_2Dregion_into_1Dsegment(polygons_negative, strength_negative, minimum_segment_width, 1E-4)
    # discretize_region.draw_2Dregion_from_slicing(slice_region_positive)
    # discretize_region.draw_2Dregion_from_slicing(slice_region_negative)

    # Evaluation
    # result = strength_evaluation.evaluate_joint_strength_2D(polygons_positive,
    #                                                strength_positive,
    #                                                polygons_negative,
    #                                                strength_negative,
    #                                                -2,
    #                                                1,
    #                                                minimum_segment_width)
    result = strength_evaluation.measure_joint_maximum_force_strength(polygons_positive,
                                                   strength_positive,
                                                   polygons_negative,
                                                   strength_negative,
                                                   2,
                                                   minimum_segment_width)
    print(result["force_range"])
    strength_evaluation.draw_partition_result([polygons_positive, polygons_negative],
                                              result["slice_region"],
                                               result["segment_data"],
                                               result["height_force"][0],
                                               result["height_bending"][0])

    strength_evaluation.draw_partition_result([polygons_positive, polygons_negative],
                                              result["slice_region"],
                                               result["segment_data"],
                                               result["height_force"][1],
                                               result["height_bending"][1])

    # strength_evaluation.draw_partition_result([polygons_positive, polygons_negative],
    #                                           result["slice_region"],
    #                                           result["segment_data"],
    #                                           result["height_force"],
    #                                           result["height_bending"])
if __name__ == '__main__':
    test_discretize_region()

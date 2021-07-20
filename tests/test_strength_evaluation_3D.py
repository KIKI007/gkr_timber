import gkr_timber.plasticity.strength_evaluation_3D as strength_evaluation_3D
import pytest

class TestStrengthEvaluation3D:
    def test_evaluate_joint_strength_3D(self):
        polygons_positive = [[[-1, -1], [1, -1], [1, 1], [-1, 1]]]
        strength_positive = [0.5]

        polygons_negative = [[[-1, -1], [1, -1], [1, 1], [-1, 1]]]
        strength_negative = [0.5]

        result = strength_evaluation_3D.evaluate_joint_strength_3D([polygons_positive, polygons_negative],
                                                                   [strength_positive, strength_negative],
                                                                   1.0, # force
                                                                   0.1, # bending y
                                                                   0.8, # bending z
                                                                   0.1)
        strength_evaluation_3D.draw_3D_partition_result(result)

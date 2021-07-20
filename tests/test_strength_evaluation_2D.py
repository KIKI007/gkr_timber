import gkr_timber.plasticity.strength_evaluation_2D as strength_evaluation_2D
import pytest

class TestStrengthEvaluation2D:
    def test_evaluate_joint_strength_2D(self):
        polygons_positive = [[[-1, 0], [1, 0], [1, 1], [-1, 1]]]
        strength_positive = [1]

        polygons_negative = [[[-1, 0], [1, 0], [1, 1], [-1, 1]]]
        strength_negative = [1]

        result = strength_evaluation_2D.evaluate_joint_strength_2D([polygons_positive, polygons_negative], [strength_positive, strength_negative], 0.1, 0.8, 0.1)
        assert result["stable"] == True
        [polygons_forces, polygons_bendings] = strength_evaluation_2D.extract_geometry_from_evlaution_2D_result(result)
        assert len(polygons_forces[0]) == 0
        assert len(polygons_forces[1]) != 0

        result = strength_evaluation_2D.evaluate_joint_strength_2D([polygons_positive, polygons_negative], [strength_positive, strength_negative], 0, 1.01, 0.1)
        strength_evaluation_2D.draw_strength_evaluation_2D_result(result)
        assert result["stable"] == False

    def test_measure_joint_maximum_force_strength(self):
        polygons_positive = [[[-1, 0], [1, 0], [1, 1], [-1, 1]]]
        strength_positive = [1]

        polygons_negative = [[[-1, 0], [1, 0], [1, 1], [-1, 1]]]
        strength_negative = [1]

        result = strength_evaluation_2D.measure_joint_maximum_force_strength([polygons_positive, polygons_negative], [strength_positive, strength_negative], 1.0, 0.1)
        assert result["external_axial_force_ranges"] == [pytest.approx(-1.0), pytest.approx(1.0)]

    def test_draw_strength_evaluation_2D_result(self):
        polygons_positive = [[[-1, 0], [1, 0], [1, 1], [-1, 1]]]
        strength_positive = [1]

        polygons_negative = [[[-1, 0], [1, 0], [1, 1], [-1, 1]]]
        strength_negative = [1]
        result = strength_evaluation_2D.evaluate_joint_strength_2D([polygons_positive, polygons_negative], [strength_positive, strength_negative], 0.1, 0.8, 0.1)
        strength_evaluation_2D.draw_strength_evaluation_2D_result(result)

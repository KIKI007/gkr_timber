import gkr_timber.plasticity.discretize_polygons as discretize_polygons
import pytest

class TestDiscretizeRegion:
    def test_get_polygon_corner(self):
        polygon = [[0, -1],
                   [2, -1],
                   [2, 1],
                   [0, 1]]
        [left_y, right_y, bottom_z, top_z] = discretize_polygons.get_polygon_corner(polygon)
        assert left_y == 0
        assert right_y == 2
        assert bottom_z == -1
        assert top_z == 1

    def test_create_rectangle(self):
        polygon = discretize_polygons.create_rectangle(0, 2, -1, 1)
        assert polygon == [[0, -1],
                   [2, -1],
                   [2, 1],
                   [0, 1]]

    def test_measure_polygons_width_along_yaxis(self):
        polygons = [[[-2, -3], [-1, -3], [-1, 0]],
                    [[0, -1], [2, -1], [3, 1], [0, 1]]]
        assert [[-2, -1], [0, 3]] == discretize_polygons.measure_polygons_width_along_yaxis(polygons)

    def test_boolean_intersection_polygon_vertical_rectangle(self):
        polygon = [[0, 0],
                    [1, 0],
                    [1, 1]]
        intersection = discretize_polygons.boolean_intersection_polygon_vertical_rectangle(polygon, [0.1, 0.2], 1E-4)
        [left_y, right_y, bottom_z, top_z] = discretize_polygons.get_polygon_corner(intersection)

        assert left_y == pytest.approx(0.1)
        assert right_y == pytest.approx(0.2)
        assert bottom_z == pytest.approx(0)
        assert top_z == pytest.approx(0.1)

    def test_measure_polygon_area(self):
        polygon = [[0, 0],
                   [1, 0],
                   [1, 1]]
        area = discretize_polygons.measure_polygon_area(polygon)
        assert area == pytest.approx(0.5)

    def test_drawing(self):
        polygon = [[0, 0],
                   [1, 0],
                   [1, 1]]

        discretize_polygons.draw_polygons_wireframe([polygon])
        discretize_polygons.draw_polygons_with_strengths([polygon], [1])

    def test_slice_polygons_vertically_with_intervals(self):
        polygons = [[[0, 0],
                   [1, 0],
                   [1, 1]]]
        strengths = [1]
        slice_y_intervals = [[0.1, 0.2], [0.2, 0.3], [0.5, 0.6]]
        [polygons_intersec_shapes, polygons_intersec_strengths] =  discretize_polygons.slice_polygons_vertically_with_intervals(polygons, strengths, slice_y_intervals)

        discretize_polygons.draw_polygons_with_strengths(polygons_intersec_shapes, polygons_intersec_strengths)

    def test_slice_polygons_vertically(self):
        polygons = [[[0, 0],
                     [1, 0],
                     [1, 1]]]
        strengths = [1]
        [slice_polygons, slice_polygons_strengths] = discretize_polygons.slice_polygons_vertically(polygons, strengths, 0.1)
        discretize_polygons.draw_polygons_with_strengths(slice_polygons, slice_polygons_strengths)

    def test_squarize_polygons(self):
        polygons = [[[0, 0],
                     [1, 0],
                     [1, 1]]]
        strengths = [1]
        [squares_shapes, squares_strength] = discretize_polygons.squarize_polygons(polygons, strengths, 0.1)
        discretize_polygons.draw_polygons_with_strengths(squares_shapes, squares_strength)


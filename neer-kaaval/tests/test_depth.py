import pytest
from neer_kaaval.depth import MarkerNotFound, estimate_depth
from neer_kaaval.synthetic import make_marker_image


@pytest.mark.parametrize("d", [0, 10, 25, 40, 60, 85])
def test_depth_within_5cm(d):
    r = estimate_depth(make_marker_image(d, seed=d))
    assert abs(r.depth_cm - d) <= 5
    assert r.confidence > 0.5


def test_fully_submerged_or_missing_marker():
    with pytest.raises(MarkerNotFound):
        estimate_depth(make_marker_image(100))

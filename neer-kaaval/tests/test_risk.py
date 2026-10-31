from neer_kaaval.risk import consensus_depth, risk_score


def test_consensus_drops_outlier_and_low_confidence():
    d, n = consensus_depth([(30, 0.9), (32, 0.8), (31, 0.7), (90, 0.9), (5, 0.2)])
    assert n == 3 and 30 <= d <= 32


def test_no_readings_falls_back_to_forecast():
    d, n = consensus_depth([])
    assert d is None and n == 0
    score, level = risk_score(None, 0, 50)
    assert level == "LOW"


def test_measured_depth_overrides_forecast():
    assert risk_score(55, 0, 0)[1] == "HIGH"
    assert risk_score(32, 0, 0)[1] == "MEDIUM"

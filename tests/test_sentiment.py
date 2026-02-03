from ims.services.sentiment import score_headline


def test_score_headline_empty():
    s = score_headline("")
    assert s.score == 0.0
    assert s.confidence == 0.0


def test_score_headline_basic_positive():
    s = score_headline("Company wins big order, shares rally")
    assert -1.0 <= s.score <= 1.0
    assert s.confidence >= 0.2


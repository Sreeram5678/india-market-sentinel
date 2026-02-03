from ims.services.summarize import summarize_filing


def test_summarize_dividend_with_amount():
    r = summarize_filing("Declaration of dividend", "Board approved dividend of ₹5 per share")
    assert r.category == "DIVIDEND"
    assert "₹5" in r.summary
    assert r.confidence >= 0.6


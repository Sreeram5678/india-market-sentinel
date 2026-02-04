from ims.providers.bse import BseAnnouncementsProvider


def test_normalize_pdf_url_filename_only():
    got = BseAnnouncementsProvider._normalize_pdf_url("a876faac-3eb3-4f61-8778-7a6154e94df8.pdf")
    assert got == "https://www.bseindia.com/xml-data/corpfiling/AttachLive/a876faac-3eb3-4f61-8778-7a6154e94df8.pdf"


def test_normalize_pdf_url_absolute():
    url = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/x.pdf"
    assert BseAnnouncementsProvider._normalize_pdf_url(url) == url


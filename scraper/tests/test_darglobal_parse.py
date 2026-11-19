"""DarGlobal page -> chunks, verified at the data-contract edge (what records come out)."""
from dar.domain.models import Chunk
from scraper.darglobal.parse import parse_page

URL = "https://darglobal.co.uk/neptune"
NOW = "2026-11-19T10:00:00Z"

PAGE = """
<html><head><title>Neptune | Branded Villas Riyadh</title><script>var secret=1</script></head>
<body>
<header><a href="/">Home</a> Menu Login</header>
<h1>Neptune, Interiors by Mouawad</h1>
<p>Limited edition villas in Riyadh.</p>
<h2>Amenities</h2>
<p>Private pool and a cinema room.</p>
<h2>Why INVEST</h2>
<h3>01 Full freehold ownership</h3><h3>02 Residency eligibility via SAR 4M+</h3>
<h2>Register Your Interest</h2>
<form><input name="email"><p>Send us your details</p></form>
<h2>We value our privacy</h2><p>We use cookies</p>
<h2>Frequently Asked Questions</h2>
<h3>Where is Neptune located?</h3><p>Neptune is in Riyadh.</p>
<p>Contact sales@darglobal.co.uk or +971 4 123 4567.</p>
<footer>Copyright footer text</footer>
</body></html>
"""


def chunks(html=PAGE):
    return parse_page(html, URL, NOW)


def test_one_chunk_per_section_and_an_overview_before_the_first_heading():
    sections = [c.section for c in chunks()]
    assert sections == ["Overview", "Amenities", "Why INVEST", "Frequently Asked Questions"]


def test_every_chunk_starts_with_source_title_section_header():
    for c in chunks():
        assert c.text.startswith(f"DarGlobal | Neptune, Interiors by Mouawad | {c.section}")


def test_boilerplate_forms_cookie_banners_navigation_and_scripts_are_dropped():
    body = " ".join(c.text for c in chunks())
    for junk in ("Send us your details", "cookies", "Menu Login", "Copyright footer", "secret"):
        assert junk not in body


def test_site_chrome_sections_are_dropped_but_descriptive_ones_kept():
    html = ("<h1>P</h1><h2>find your next investment</h2><p>Type All Types Location All Locations</p>"
            "<h2>related projects</h2><p>Dubai | UAE The Pagani Penthouse</p>"
            "<h2>Articles And News</h2><p>Mar 17, 2022</p>"
            "<h2>Photo Gallery</h2><p>Managed residences with exceptional service.</p>")
    assert [c.section for c in parse_page(html, URL, NOW)] == ["Photo Gallery"]


def test_heading_items_are_kept_with_their_section():
    why = next(c for c in chunks() if c.section == "Why INVEST")
    assert "01 Full freehold ownership" in why.text and "02 Residency eligibility" in why.text


def test_contact_details_in_text_are_redacted():
    body = " ".join(c.text for c in chunks())
    assert "sales@darglobal.co.uk" not in body and "123 4567" not in body


def test_records_satisfy_the_data_contract_and_carry_url_and_date():
    for c in chunks():
        assert isinstance(c, Chunk)
        assert c.url == URL and c.source == "darglobal" and c.scraped_at == NOW
    assert len({c.id for c in chunks()}) == len(chunks())  # unique, stable ids
    assert [c.id for c in chunks()] == [c.id for c in chunks()]


def test_ids_stay_unique_when_a_page_repeats_a_heading():
    html = ("<h1>P</h1><p>Intro text.</p><h2>Overview</h2><p>Second overview.</p>"
            "<h2>FAQ</h2><p>First faq.</p><h2>FAQ</h2><p>Second faq.</p>")
    result = parse_page(html, URL, NOW)
    assert len(result) == 4
    assert len({c.id for c in result}) == 4
    assert [c.id for c in result] == [c.id for c in parse_page(html, URL, NOW)]  # and stable


def test_long_sections_are_split_without_losing_text_or_cutting_sentences():
    sentences = [f"Sentence number {i} about the villa." for i in range(120)]
    html = f"<h1>Big</h1><h2>Details</h2><p>{' '.join(sentences)}</p>"
    result = parse_page(html, URL, NOW)
    assert len(result) > 1
    assert all(len(c.text) <= 1900 for c in result)
    assert all(c.text.rstrip().endswith(".") for c in result)
    joined = " ".join(c.text for c in result)
    assert all(s in joined for s in sentences)


def test_the_pages_preview_image_is_attached_to_every_chunk_and_junk_values_are_ignored():
    og = '<head><title>N | x</title><meta property="og:image" content="https://cdn.example.test/neptune.jpg"></head>'
    page_with_image = PAGE.replace("<head><title>Neptune | Branded Villas Riyadh</title>", og.replace("</head>", "")).replace("</head>", "</head>", 1)
    result = chunks(page_with_image)
    assert result and all(c.image_url == "https://cdn.example.test/neptune.jpg" for c in result)
    for junk in ("null", "", "undefined", "/relative.jpg"):
        bad = PAGE.replace("<title>Neptune", f'<meta property="og:image" content="{junk}"><title>Neptune')
        assert all(c.image_url is None for c in chunks(bad)), junk


def test_a_large_realistic_page_is_parsed_quickly():
    import time

    cards = "".join(f"<div><div><div><span>Card {i}</span><p>Detail text number {i}.</p></div></div></div>" for i in range(1500))
    html = f"<html><body><h1>Big</h1>{''.join(f'<h2>Section {s}</h2>{cards[:4000]}' for s in range(30))}</body></html>"
    started = time.perf_counter()
    parse_page(html, URL, NOW)
    assert time.perf_counter() - started < 5


def test_page_without_headings_still_yields_a_chunk_from_its_text():
    result = parse_page("<html><title>Plain</title><body><p>Just some text here.</p></body></html>", URL, NOW)
    assert len(result) == 1 and "Just some text here." in result[0].text

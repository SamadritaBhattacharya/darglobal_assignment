"""The Wasalt homepage's own description becomes an 'About Wasalt' record (so 'what is Wasalt?' has an answer)."""
from dar.domain.models import Chunk
from scraper.wasalt.home import parse_home

NOW = "2026-11-19T10:00:00Z"
DESC = "Find properties For Sale and Rent in Saudi Arabia, Wasalt the Saudi&#39;s largest selection of properties.Installment Payment Plans available | Wasalt"


def home(canonical="https://wasalt.sa/en", description=DESC, image="https://cdn.wasalt.sa/images/wasalt-logo.svg", extra=""):
    meta = f'<meta name="description" content="{description}"/>' if description is not None else ""
    og = f'<meta property="og:image" content="{image}"/>' if image else ""
    return (f'<html><head><title>Properties For Sale and Rent in Saudi Arabia | Wasalt</title>{meta}{og}'
            f'<link rel="canonical" href="{canonical}"/></head><body>'
            f'<script id="__NEXT_DATA__" type="application/json">{{"props":{{"pageProps":{{"cmsData":{{}}{extra}}}}}}}</script></body></html>')


def test_the_homepage_becomes_an_about_wasalt_record():
    c = parse_home(home(), NOW)
    assert isinstance(c, Chunk)
    assert (c.id, c.source, c.url, c.title, c.section) == ("wasalt:about", "wasalt", "https://wasalt.sa/en", "About Wasalt", "Overview")
    assert c.image_url == "https://cdn.wasalt.sa/images/wasalt-logo.svg" and c.scraped_at == NOW


def test_the_description_is_cleaned_for_reading():
    text = parse_home(home(), NOW).text
    assert text.startswith("Wasalt | About Wasalt | Overview")
    assert "largest selection of properties. Installment Payment Plans available" in text   # missing space fixed
    assert "Saudi's" in text and "&#39;" not in text                                         # HTML entity decoded
    assert "| Wasalt" not in text.split("\n", 1)[1]                                          # site-name suffix removed
    assert text.rstrip().endswith("Source: Wasalt.sa")


def test_only_the_real_homepage_counts_not_search_results_or_listings():
    jeddah = home(canonical="https://wasalt.sa/en/properties-for-sale-in-jeddah")   # internal search results: policy says do not use
    listing = home(canonical="https://wasalt.sa/en/property/sale/x-1", extra=',"propertyDetailsV3":{}')
    assert parse_home(jeddah, NOW) is None
    assert parse_home(listing, NOW) is None


def test_a_page_without_a_description_or_with_junk_is_skipped():
    assert parse_home(home(description=None), NOW) is None
    assert parse_home(home(description=""), NOW) is None
    assert parse_home("", NOW) is None
    assert parse_home("<html><body>nothing</body></html>", NOW) is None

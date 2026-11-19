"""Wasalt saved page -> one listing record. Verified at the data-contract edge (what record comes out)."""
import json

from dar.domain.models import Chunk
from scraper.wasalt.parse import parse_listing

NOW = "2026-11-19T10:00:00Z"
SECRET_PHONE, SECRET_NAME = "0562259309", "Ahmed Alqahtani"


def page(info=None, attributes=None, kind="sale", top=None):
    """A made-up page shaped like Wasalt's real one, with fake agent details that must never come out."""
    info = {
        "title": "Apartment 152.78 SQM with 5 Bedrooms", "propertyFor": "sale", "salePrice": 570000, "expectedRent": "",
        "currencyType": "SAR", "city": "Jeddah", "zone": "Al Faysaleyyah", "district": "Al Faysaleyyah",
        "territory": "North Jeddah", "propertySubType": "Apartment", "slug": "apartment-15278-sqm-with-5-bedrooms-5924016",
        "description": f"<p>Call the agent {SECRET_NAME} on {SECRET_PHONE} or +966 50 123 4567</p>", **(info or {}),
    }
    details = {
        "id": 5924016, "propertyInfo": info,
        "attributes": attributes if attributes is not None else [
            {"key": "noOfBedrooms", "value": 5}, {"key": "builtUpArea", "value": "152.78"}],
        "propertyOwner": {"name": SECRET_NAME, "mobile": SECRET_PHONE},
        "leadContactInfo": {"phone": SECRET_PHONE, "agent": SECRET_NAME},
        "regaMojDesc": "REGA-LICENCE-123456",
        **(top or {}),
    }
    data = {"props": {"pageProps": {"propertyDetailsV3": details}}}
    return f'<html><head><title>x</title></head><body><script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script></body></html>'


def test_a_sale_listing_becomes_one_valid_record_with_the_structured_facts():
    c = parse_listing(page(), NOW)
    assert isinstance(c, Chunk)
    assert (c.source, c.listing_kind, c.city, c.district, c.property_type) == ("wasalt", "sale", "Jeddah", "Al Faysaleyyah", "apartment")
    assert (c.price, c.currency, c.area_sqm, c.bedrooms) == (570000, "SAR", 152.78, 5)
    assert c.url == "https://wasalt.sa/en/property/sale/apartment-15278-sqm-with-5-bedrooms-5924016"
    assert c.id == "wasalt:5924016" and c.scraped_at == NOW


def test_a_rental_uses_the_rent_price_and_says_per_year():
    c = parse_listing(page({"propertyFor": "rent", "salePrice": "", "expectedRent": 60000, "expectedRentType": "/Year",
                            "slug": "floor-315-sqm-with-4-bedrooms-5900066", "propertySubType": "Floor"},
                           attributes=[{"key": "noOfBedrooms", "value": 4}, {"key": "builtUpArea", "value": "315"}]), NOW)
    assert (c.listing_kind, c.price, c.property_type, c.area_sqm, c.bedrooms) == ("rent", 60000, "floor", 315, 4)
    assert "60,000 SAR per year" in c.text
    assert c.price_period == "per year"
    assert c.url.startswith("https://wasalt.sa/en/property/rent/")


def test_a_sale_has_no_price_period():
    assert parse_listing(page(), NOW).price_period is None


def test_agent_owner_phone_and_licence_details_never_appear_anywhere_in_the_record():
    c = parse_listing(page(), NOW)
    everything = c.model_dump_json()
    for secret in (SECRET_PHONE, SECRET_NAME, "123 4567", "REGA-LICENCE", "Call the agent"):
        assert secret not in everything


IMG = "https://imagedelivery.net/abc/production/properties/5924016/images/photo.jpg/quality=60,format=auto"


def with_og_image(html: str, content: str) -> str:
    return html.replace("<head>", f'<head><meta property="og:image" content="{content}"/>')


def test_the_listing_photo_from_the_page_preview_is_kept():
    assert parse_listing(with_og_image(page(), IMG), NOW).image_url == IMG


def test_a_missing_or_unusable_image_is_simply_none():
    assert parse_listing(page(), NOW).image_url is None
    for bad in ("null", "", "/relative.jpg", "http://insecure.example/x.jpg", "javascript:alert(1)"):
        assert parse_listing(with_og_image(page(), bad), NOW).image_url is None, bad


def test_the_text_is_built_from_facts_with_a_header_and_attribution():
    c = parse_listing(page(), NOW)
    assert c.text.startswith("Wasalt | Apartment 152.78 SQM with 5 Bedrooms | Listing")
    assert "Apartment for sale in Al Faysaleyyah, Jeddah" in c.text
    assert "5 bedrooms" in c.text and "152.78 sqm" in c.text and "570,000 SAR" in c.text
    assert c.text.rstrip().endswith("Source: Wasalt.sa")


def test_missing_optional_facts_do_not_break_the_record():
    c = parse_listing(page({"title": "Apartment with no stated facts"}, attributes=[]), NOW)
    assert c.area_sqm is None and c.bedrooms is None and "sqm" not in c.text


def test_when_the_size_field_is_absent_the_size_in_the_title_is_used():
    # real case: rest houses keep their size elsewhere, but the title always says "869.16 SQM"
    c = parse_listing(page({"title": "Rest House 869.16 SQM with 2 Bedrooms"}, attributes=[{"key": "noOfBedrooms", "value": 2}]), NOW)
    assert c.area_sqm == 869.16 and "869.16 sqm" in c.text


def test_the_size_field_wins_over_the_title_when_both_exist():
    c = parse_listing(page({"title": "Apartment 999 SQM with 5 Bedrooms"}), NOW)  # attributes say builtUpArea 152.78
    assert c.area_sqm == 152.78


def test_pages_that_are_not_listings_are_skipped():
    home = '<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"cmsData":{}}}}</script>'
    assert parse_listing(home, NOW) is None
    assert parse_listing("<html><body>nothing here</body></html>", NOW) is None
    assert parse_listing("", NOW) is None


def test_a_listing_with_no_usable_price_is_skipped_not_guessed():
    assert parse_listing(page({"salePrice": "", "expectedRent": ""}), NOW) is None

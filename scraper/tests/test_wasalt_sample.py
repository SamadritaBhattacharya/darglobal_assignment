"""Choosing which Wasalt listings to save by hand: a varied, deterministic sample."""
from scraper.wasalt.sample import stratified_sample

BASE = "https://wasalt.sa/en/property"


def make(kind: str, ptype: str, beds: int, n: int) -> list[str]:
    return [f"{BASE}/{kind}/{ptype}-{100 + i}-sqm-with-{beds}-bedrooms-{abs(hash((kind, ptype, beds, i))) % 10**7}" for i in range(n)]


CATALOG = (make("sale", "apartment", 3, 50) + make("sale", "villa", 5, 40) + make("rent", "apartment", 2, 40)
           + make("rent", "floor", 3, 30) + make("sale", "land", 0, 20))


def test_returns_at_most_n_unique_urls_from_the_input():
    picked = stratified_sample(CATALOG, n=12, seed=1)
    assert len(picked) == 12 and len(set(picked)) == 12 and set(picked) <= set(CATALOG)


def test_covers_sale_and_rent_and_every_property_type():
    picked = stratified_sample(CATALOG, n=15, seed=1)
    assert any("/sale/" in u for u in picked) and any("/rent/" in u for u in picked)
    for ptype in ("apartment", "villa", "floor", "land"):
        assert any(f"/{ptype}-" in u for u in picked), ptype


def test_is_deterministic_for_a_seed_and_differs_between_seeds():
    assert stratified_sample(CATALOG, 10, seed=7) == stratified_sample(CATALOG, 10, seed=7)
    assert stratified_sample(CATALOG, 10, seed=7) != stratified_sample(CATALOG, 10, seed=8)


def test_skips_malformed_urls_and_handles_small_inputs():
    assert stratified_sample(["https://wasalt.sa/en/blog/x", "garbage"], 5, seed=1) == []
    assert len(stratified_sample(CATALOG[:3], 10, seed=1)) == 3

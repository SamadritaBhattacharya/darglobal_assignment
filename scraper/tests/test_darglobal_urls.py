"""DarGlobal URL selection, verified by outcome: given a sitemap, which pages get scraped."""
from scraper.darglobal.urls import select_urls

BASE = "https://darglobal.co.uk"


def sitemap(*paths: str) -> str:
    return "<urlset>" + "".join(f"<url><loc>{BASE}/{p}</loc></url>" for p in paths) + "</urlset>"


def chosen(*paths: str) -> list[str]:
    return [u.removeprefix(BASE + "/") for u in select_urls(sitemap(*paths))]


def test_keeps_project_partner_and_property_pages():
    assert chosen("projects/properties-in-uae/villas", "partners/lamborghini", "one-of-one/project-pagani",
                  "rayana/trump-mansions", "amaya/amaya-plots", "trump-plaza/park-residences", "neptune", "marea") == [
        "projects/properties-in-uae/villas", "partners/lamborghini", "one-of-one/project-pagani",
        "rayana/trump-mansions", "amaya/amaya-plots", "trump-plaza/park-residences", "neptune", "marea"]


def test_keeps_info_pages():
    assert chosen("about", "faq", "why-invest") == ["about", "faq", "why-invest"]


def test_drops_blog_utility_and_non_content_pages():
    assert chosen("blog/some-post", "blog", "pay-online/status", "pay-online", "careers", "thank-you",
                  "become-an-agent", "internships", "landingpage/newStaticLandingPageHtml", "bookYourUnit",
                  "privacy-policy", "new-home-page", "marea") == ["marea"]


def test_dedupes_case_variants_html_entities_and_trailing_slashes():
    urls = chosen("La-Collina", "la-collina/", "the-mulliner", "the-mulliner")
    assert [u.lower().strip("/") for u in urls] == ["la-collina", "the-mulliner"]


def test_samples_only_a_few_press_and_insight_items_in_sitemap_order():
    press = [f"press/item-{i}" for i in range(30)]
    insights = [f"insights/post-{i}" for i in range(20)]
    result = chosen(*press, *insights)
    assert [p for p in result if p.startswith("press/")] == press[:8]
    assert [p for p in result if p.startswith("insights/")] == insights[:5]


def test_ignores_urls_from_other_domains():
    text = "<urlset><url><loc>https://evil.example/neptune</loc></url></urlset>"
    assert select_urls(text) == []

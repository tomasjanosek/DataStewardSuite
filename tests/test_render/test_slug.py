from src.render.slug import slugify


def test_slugify_strips_czech_diacritics_and_spaces():
    assert slugify("Měření místa") == "mereni-mista"


def test_slugify_collapses_punctuation():
    assert slugify("Odečty  (SCADA/AVE)") == "odecty-scada-ave"

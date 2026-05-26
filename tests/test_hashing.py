from src.utils.hashing import canonicalize, url_hash


def test_canonicalize_strips_tracking_and_normalizes():
    a = canonicalize("https://www.Example.com/post/?utm_source=x&id=1")
    b = canonicalize("http://example.com/post?id=1")
    assert a == b


def test_url_hash_stable():
    assert url_hash("https://example.com/x") == url_hash("https://example.com/x/")

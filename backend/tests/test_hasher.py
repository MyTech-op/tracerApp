from app.crawler.hasher import generate_content_hash


def test_content_hash_consistency():
    hash1 = generate_content_hash("Title", "Meta", "H1", "Body", "Article")
    hash2 = generate_content_hash("Title", "Meta", "H1", "Body", "Article")
    assert hash1 == hash2


def test_content_hash_sensitivity():
    hash1 = generate_content_hash("Title", "Meta", "H1", "Body", "Article")
    hash2 = generate_content_hash("Updated Title", "Meta", "H1", "Body", "Article")
    assert hash1 != hash2

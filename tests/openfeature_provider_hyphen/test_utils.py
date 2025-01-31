import base64
from openfeature_provider_hyphen.utils import get_org_id_from_public_key, build_default_horizon_url, build_url

def test_get_org_id_from_public_key():
    # Test valid public key
    # Create a base64 string that when decoded would be "test:key"
    test_key = base64.b64encode(b"test:key").decode('utf-8')
    public_key = "public_" + test_key
    org_id = get_org_id_from_public_key(public_key)
    assert org_id == "test"

    # Test invalid public key
    org_id = get_org_id_from_public_key("invalid_key")
    assert org_id == ""

def test_build_default_horizon_url():
    # Test with org ID
    test_key = base64.b64encode(b"test:key").decode('utf-8')
    public_key = "public_" + test_key
    url = build_default_horizon_url(public_key)
    assert url == "https://test.toggle.hyphen.cloud"

    # Test without org ID
    url = build_default_horizon_url("invalid_key")
    assert url == "https://toggle.hyphen.cloud"

def test_build_url():
    # Test with base path
    url = build_url("https://example.com/base", "/path")
    assert url == "https://example.com/base/path"

    # Test without base path
    url = build_url("https://example.com", "/path")
    assert url == "https://example.com/path"

    # Test with trailing slash
    url = build_url("https://example.com/base/", "/path")
    assert url == "https://example.com/base/path"

    # Test with leading slash in path
    url = build_url("https://example.com/base", "path")
    assert url == "https://example.com/base/path"

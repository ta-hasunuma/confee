import pytest

import confee_agent.tools.search_connpass as search_connpass_module


@pytest.fixture(autouse=True)
def _reset_api_key_cache():
    """各テスト前に API キーキャッシュをリセットする。"""
    search_connpass_module._cached_api_key = None
    yield
    search_connpass_module._cached_api_key = None

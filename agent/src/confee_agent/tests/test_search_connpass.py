import httpx
import respx

from confee_agent.models import ConnpassEvent, ConnpassSearchResult
from confee_agent.tools.search_connpass import (
    CONNPASS_API_URL,
    _search_connpass_api,
    search_connpass,
)


SAMPLE_EVENT = {
    "id": 12345,
    "title": "TypeScript meetup #1",
    "catch": "TypeScript初心者向け勉強会",
    "description": "<p>TypeScriptの基礎を学びます</p>",
    "url": "https://connpass.com/event/12345/",
    "image_url": None,
    "hash_tag": "ts_meetup",
    "started_at": "2026-03-15T13:00:00+09:00",
    "ended_at": "2026-03-15T17:00:00+09:00",
    "limit": 50,
    "event_type": "participation",
    "open_status": "open",
    "group": {
        "id": 100,
        "subdomain": "ts-meetup",
        "title": "TypeScript Meetup Group",
        "url": "https://ts-meetup.connpass.com/",
    },
    "address": "東京都渋谷区",
    "place": "渋谷カンファレンスセンター",
    "lat": "35.6812",
    "lon": "139.7671",
    "owner_id": 456,
    "owner_nickname": "organizer",
    "owner_display_name": "主催者",
    "accepted": 30,
    "waiting": 5,
    "updated_at": "2026-02-01T10:00:00+09:00",
}

SAMPLE_RESPONSE = {
    "results_returned": 1,
    "results_available": 1,
    "results_start": 1,
    "events": [SAMPLE_EVENT],
}


class TestSearchConnpassApiKeyword:
    """正常系: キーワード検索テスト"""

    @respx.mock
    def test_keyword_search_returns_events(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, ConnpassSearchResult)
        assert result.results_returned == 1
        assert result.results_available == 1
        assert result.results_start == 1
        assert len(result.events) == 1
        event = result.events[0]
        assert isinstance(event, ConnpassEvent)
        assert event.id == 12345
        assert event.title == "TypeScript meetup #1"
        assert event.catch == "TypeScript初心者向け勉強会"
        assert event.description == "<p>TypeScriptの基礎を学びます</p>"
        assert event.url == "https://connpass.com/event/12345/"
        assert event.started_at == "2026-03-15T13:00:00+09:00"
        assert event.ended_at == "2026-03-15T17:00:00+09:00"
        assert event.place == "渋谷カンファレンスセンター"
        assert event.address == "東京都渋谷区"
        assert event.accepted == 30
        assert event.waiting == 5
        assert event.limit == 50
        assert event.event_type == "participation"
        assert event.open_status == "open"

    @respx.mock
    def test_keyword_search_sends_correct_params(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(keyword="TypeScript", count=5, order=2)

        request = route.calls[0].request
        assert request.url.params["keyword"] == "TypeScript"
        assert request.url.params["count"] == "5"
        assert request.url.params["order"] == "2"
        assert request.url.params["start"] == "1"

    @respx.mock
    def test_default_order_is_1(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(keyword="TypeScript")

        request = route.calls[0].request
        assert request.url.params["order"] == "1"

    @respx.mock
    def test_keyword_search_sends_api_key_header(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(keyword="TypeScript")

        request = route.calls[0].request
        assert request.headers["X-API-Key"] == "test-api-key"
        assert "User-Agent" in request.headers

    @respx.mock
    def test_keyword_or_search(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(keyword_or="TypeScript,Python")

        request = route.calls[0].request
        assert request.url.params["keyword_or"] == "TypeScript,Python"

    @respx.mock
    def test_empty_params_omitted(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(keyword="test")

        request = route.calls[0].request
        assert "keyword_or" not in request.url.params
        assert "ym" not in request.url.params
        assert "ymd" not in request.url.params
        assert "prefecture" not in request.url.params


class TestSearchConnpassApiZeroResults:
    """正常系: 0件結果テスト"""

    @respx.mock
    def test_zero_results(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        empty_response = {
            "results_returned": 0,
            "results_available": 0,
            "results_start": 1,
            "events": [],
        }
        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=empty_response)
        )

        result = _search_connpass_api(keyword="存在しないカンファレンス")

        assert isinstance(result, ConnpassSearchResult)
        assert result.results_returned == 0
        assert result.results_available == 0
        assert result.results_start == 1
        assert result.events == []


class TestSearchConnpassApiErrors:
    """異常系: エラーレスポンス・タイムアウトテスト"""

    @respx.mock
    def test_api_error_response(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, dict)
        assert result["error"] is True
        assert result["status_code"] == 500

    @respx.mock
    def test_api_unauthorized(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "invalid-key")

        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, dict)
        assert result["error"] is True
        assert result["status_code"] == 401

    @respx.mock
    def test_api_rate_limited(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(429, text="Too Many Requests")
        )

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, dict)
        assert result["error"] is True
        assert result["status_code"] == 429

    @respx.mock
    def test_api_timeout(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        respx.get(CONNPASS_API_URL).mock(side_effect=httpx.ReadTimeout("timeout"))

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, dict)
        assert result["error"] is True
        assert "timeout" in result["message"].lower()

    def test_missing_api_key_returns_error(self, monkeypatch):
        monkeypatch.delenv("CONNPASS_API_KEY", raising=False)

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, dict)
        assert result["error"] is True
        assert "CONNPASS_API_KEY" in result["message"]


class TestSearchConnpassToolWrapper:
    """search_connpass @tool ラッパー関数テスト"""

    @respx.mock
    def test_tool_returns_dict_on_success(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        result = search_connpass._tool_func(keyword="TypeScript")

        assert isinstance(result, dict)
        assert result["results_returned"] == 1
        assert result["results_available"] == 1
        assert result["results_start"] == 1
        assert len(result["events"]) == 1
        event = result["events"][0]
        assert event["id"] == 12345
        assert event["title"] == "TypeScript meetup #1"
        assert event["description"] == "<p>TypeScriptの基礎を学びます</p>"
        assert event["event_type"] == "participation"

    @respx.mock
    def test_tool_returns_error_dict_on_failure(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        result = search_connpass._tool_func(keyword="TypeScript")

        assert isinstance(result, dict)
        assert result["error"] is True


class TestSearchConnpassApiPrefectureAndDate:
    """正常系: 都道府県・日付パラメータテスト"""

    @respx.mock
    def test_prefecture_param(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(keyword="Python", prefecture="tokyo")

        request = route.calls[0].request
        assert request.url.params["prefecture"] == "tokyo"

    @respx.mock
    def test_ym_param(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(ym="202603")

        request = route.calls[0].request
        assert request.url.params["ym"] == "202603"

    @respx.mock
    def test_ymd_param(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(ymd="20260315")

        request = route.calls[0].request
        assert request.url.params["ymd"] == "20260315"


class TestExpiredEventFiltering:
    """申し込み期限切れイベントのフィルタリングテスト"""

    @respx.mock
    def test_filters_out_closed_events(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        closed_event = {**SAMPLE_EVENT, "id": 99999, "title": "Closed Event", "open_status": "close"}
        response_data = {
            "results_returned": 2,
            "results_available": 2,
            "results_start": 1,
            "events": [SAMPLE_EVENT, closed_event],
        }
        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=response_data)
        )

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, ConnpassSearchResult)
        assert result.results_returned == 1
        assert all(e.open_status != "close" for e in result.events)

    @respx.mock
    def test_filters_out_cancelled_events(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        cancelled_event = {**SAMPLE_EVENT, "id": 99998, "title": "Cancelled Event", "open_status": "cancelled"}
        response_data = {
            "results_returned": 2,
            "results_available": 2,
            "results_start": 1,
            "events": [SAMPLE_EVENT, cancelled_event],
        }
        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=response_data)
        )

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, ConnpassSearchResult)
        assert result.results_returned == 1
        assert all(e.open_status != "cancelled" for e in result.events)

    @respx.mock
    def test_keeps_open_and_preopen_events(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        preopen_event = {**SAMPLE_EVENT, "id": 99997, "title": "Preopen Event", "open_status": "preopen"}
        response_data = {
            "results_returned": 2,
            "results_available": 2,
            "results_start": 1,
            "events": [SAMPLE_EVENT, preopen_event],
        }
        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=response_data)
        )

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, ConnpassSearchResult)
        assert result.results_returned == 2
        statuses = {e.open_status for e in result.events}
        assert statuses == {"open", "preopen"}

    @respx.mock
    def test_all_expired_returns_zero_results(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        closed_event = {**SAMPLE_EVENT, "id": 99996, "open_status": "close"}
        cancelled_event = {**SAMPLE_EVENT, "id": 99995, "open_status": "cancelled"}
        response_data = {
            "results_returned": 2,
            "results_available": 2,
            "results_start": 1,
            "events": [closed_event, cancelled_event],
        }
        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=response_data)
        )

        result = _search_connpass_api(keyword="TypeScript")

        assert isinstance(result, ConnpassSearchResult)
        assert result.results_returned == 0
        assert result.events == []


class TestSearchConnpassApiPagination:
    """正常系: ページネーションテスト"""

    @respx.mock
    def test_start_param(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        route = respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )

        _search_connpass_api(keyword="Python", start=11, count=10)

        request = route.calls[0].request
        assert request.url.params["start"] == "11"
        assert request.url.params["count"] == "10"

    @respx.mock
    def test_results_start_in_response(self, monkeypatch):
        monkeypatch.setenv("CONNPASS_API_KEY", "test-api-key")

        paginated_response = {
            "results_returned": 10,
            "results_available": 50,
            "results_start": 11,
            "events": [SAMPLE_EVENT],
        }
        respx.get(CONNPASS_API_URL).mock(
            return_value=httpx.Response(200, json=paginated_response)
        )

        result = _search_connpass_api(keyword="Python", start=11)

        assert isinstance(result, ConnpassSearchResult)
        assert result.results_start == 11
        assert result.results_available == 50

import logging
import os

import httpx
from strands import tool

from confee_agent.mock_events import MOCK_EVENTS
from confee_agent.models import ConnpassEvent, ConnpassSearchResult

logger = logging.getLogger(__name__)

CONNPASS_API_URL = "https://connpass.com/api/v2/events/"
CONNPASS_SECRET_NAME = "confee/connpass-api-key"
USER_AGENT = "confee/1.0"
TIMEOUT_SECONDS = 5

_cached_api_key: str | None = None


def _get_api_key() -> str:
    """Secrets Manager → 環境変数の優先順で API キーを取得する。"""
    global _cached_api_key
    if _cached_api_key is not None:
        return _cached_api_key

    # 1. Secrets Manager から取得を試みる
    try:
        import boto3

        client = boto3.client("secretsmanager")
        resp = client.get_secret_value(SecretId=CONNPASS_SECRET_NAME)
        secret = resp.get("SecretString", "")
        if secret:
            logger.info("connpass API key loaded from Secrets Manager")
            _cached_api_key = secret
            return _cached_api_key
    except Exception as e:
        logger.debug("Secrets Manager unavailable, falling back to env var: %s", e)

    # 2. 環境変数から取得
    _cached_api_key = os.environ.get("CONNPASS_API_KEY", "")
    if _cached_api_key:
        logger.info("connpass API key loaded from environment variable")
    return _cached_api_key


def _parse_event(event_data: dict) -> ConnpassEvent:
    return ConnpassEvent(
        id=event_data["id"],
        title=event_data["title"],
        catch=event_data.get("catch"),
        description=event_data.get("description"),
        url=event_data["url"],
        started_at=event_data.get("started_at"),
        ended_at=event_data.get("ended_at"),
        place=event_data.get("place"),
        address=event_data.get("address"),
        accepted=event_data.get("accepted", 0),
        waiting=event_data.get("waiting", 0),
        limit=event_data.get("limit"),
        event_type=event_data.get("event_type", ""),
        open_status=event_data.get("open_status", ""),
    )


def _filter_mock_events(
    keyword: str = "",
    keyword_or: str = "",
    count: int = 10,
    start: int = 1,
) -> ConnpassSearchResult:
    filtered = MOCK_EVENTS

    if keyword:
        keywords = [k.strip().lower() for k in keyword.split(",")]
        filtered = [
            e for e in filtered
            if all(
                k in e["title"].lower()
                or k in (e.get("catch") or "").lower()
                or k in (e.get("description") or "").lower()
                or k in (e.get("address") or "").lower()
                or k in (e.get("place") or "").lower()
                for k in keywords
            )
        ]

    if keyword_or:
        keywords = [k.strip().lower() for k in keyword_or.split(",")]
        filtered = [
            e for e in filtered
            if any(
                k in e["title"].lower()
                or k in (e.get("catch") or "").lower()
                or k in (e.get("description") or "").lower()
                or k in (e.get("address") or "").lower()
                or k in (e.get("place") or "").lower()
                for k in keywords
            )
        ]

    total = len(filtered)
    start_idx = max(0, start - 1)
    paginated = filtered[start_idx : start_idx + count]
    events = [_parse_event(e) for e in paginated]

    return ConnpassSearchResult(
        results_returned=len(events),
        results_available=total,
        results_start=start,
        events=events,
    )


def _search_connpass_api(
    keyword: str = "",
    keyword_or: str = "",
    ym: str = "",
    ymd: str = "",
    prefecture: str = "",
    order: int = 1,
    start: int = 1,
    count: int = 10,
) -> ConnpassSearchResult | dict:
    api_key = _get_api_key()
    if not api_key:
        return _filter_mock_events(
            keyword=keyword,
            keyword_or=keyword_or,
            count=count,
            start=start,
        )

    headers = {
        "X-API-Key": api_key,
        "User-Agent": USER_AGENT,
    }

    params: dict = {"order": order, "start": start, "count": count}
    if keyword:
        params["keyword"] = keyword
    if keyword_or:
        params["keyword_or"] = keyword_or
    if ym:
        params["ym"] = ym
    if ymd:
        params["ymd"] = ymd
    if prefecture:
        params["prefecture"] = prefecture

    try:
        response = httpx.get(
            CONNPASS_API_URL,
            headers=headers,
            params=params,
            timeout=TIMEOUT_SECONDS,
        )

        if response.status_code != 200:
            return {
                "error": True,
                "status_code": response.status_code,
                "message": f"connpass API returned status {response.status_code}",
            }

        data = response.json()
        events = [_parse_event(e) for e in data.get("events", [])]

        return ConnpassSearchResult(
            results_returned=data.get("results_returned", 0),
            results_available=data.get("results_available", 0),
            results_start=data.get("results_start", 1),
            events=events,
        )

    except httpx.TimeoutException:
        return {
            "error": True,
            "message": "Timeout: connpass API did not respond within the time limit.",
        }
    except httpx.HTTPError as e:
        return {
            "error": True,
            "message": f"HTTP error occurred: {e}",
        }


@tool
def search_connpass(
    keyword: str = "",
    keyword_or: str = "",
    ym: str = "",
    ymd: str = "",
    prefecture: str = "",
    order: int = 1,
    start: int = 1,
    count: int = 10,
) -> dict:
    """connpass API v2からイベントを検索する。

    技術カンファレンス、勉強会、LT会などのイベント情報を検索する。

    Args:
        keyword: AND条件検索キーワード。タイトル、キャッチ、概要、住所を対象に検索。複数指定時はカンマ区切り
        keyword_or: OR条件検索キーワード。タイトル、キャッチ、概要、住所を対象に検索。複数指定時はカンマ区切り
        ym: 開催年月（yyyymm形式）。例: "202603"
        ymd: 開催日（yyyymmdd形式）。例: "20260315"
        prefecture: 都道府県コード。例: "tokyo", "online", "osaka"。複数指定時はカンマ区切り
        order: ソート順。1=更新日時降順, 2=開催日時降順, 3=新着順
        start: 検索結果の開始位置（最小値: 1）
        count: 取得件数（1〜100）
    """
    result = _search_connpass_api(
        keyword=keyword,
        keyword_or=keyword_or,
        ym=ym,
        ymd=ymd,
        prefecture=prefecture,
        order=order,
        start=start,
        count=count,
    )

    if isinstance(result, dict):
        return result

    return {
        "results_returned": result.results_returned,
        "results_available": result.results_available,
        "results_start": result.results_start,
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "catch": e.catch,
                "description": e.description,
                "url": e.url,
                "started_at": e.started_at,
                "ended_at": e.ended_at,
                "place": e.place,
                "address": e.address,
                "accepted": e.accepted,
                "waiting": e.waiting,
                "limit": e.limit,
                "event_type": e.event_type,
                "open_status": e.open_status,
            }
            for e in result.events
        ],
    }

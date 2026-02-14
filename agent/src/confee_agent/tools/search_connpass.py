import logging
import os

import httpx
from strands import tool

from confee_agent.models import ConnpassEvent, ConnpassSearchResult

logger = logging.getLogger(__name__)

CONNPASS_API_URL = "https://connpass.com/api/v2/events/"
CONNPASS_SECRET_NAME = "confee/connpass-api-key"
USER_AGENT = "confee/1.0"
TIMEOUT_SECONDS = 5

_cached_api_key: str | None = None


def _get_api_key() -> str:
    """環境変数 → Secrets Manager の優先順で API キーを取得する。"""
    global _cached_api_key
    if _cached_api_key is not None:
        return _cached_api_key

    logger.info("API key retrieval started")

    # 1. 環境変数から取得（優先）
    api_key = os.environ.get("CONNPASS_API_KEY", "")
    if api_key:
        masked = api_key[:4] + "***" + api_key[-4:]
        logger.info("connpass API key loaded from environment variable: %s", masked)
        _cached_api_key = api_key
        return _cached_api_key
    else:
        logger.info("CONNPASS_API_KEY env var not set")

    # 2. Secrets Manager から取得（フォールバック）
    try:
        import boto3

        region = os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1")
        logger.info(
            "Attempting Secrets Manager: secret=%s, region=%s",
            CONNPASS_SECRET_NAME,
            region,
        )
        client = boto3.client("secretsmanager", region_name=region)
        resp = client.get_secret_value(SecretId=CONNPASS_SECRET_NAME)
        secret = resp.get("SecretString", "")
        if secret:
            masked = secret[:4] + "***" + secret[-4:]
            logger.info("connpass API key loaded from Secrets Manager: %s", masked)
            _cached_api_key = secret
            return _cached_api_key
        else:
            logger.warning("Secrets Manager returned empty SecretString")
    except Exception as e:
        logger.warning("Secrets Manager unavailable: %s", e)

    # API キーが見つからない場合はキャッシュしない（次回リトライ可能に）
    logger.warning("No API key found")
    return ""


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


# 申し込み可能なステータス（これ以外は期限切れ・キャンセル等として除外）
_ACTIVE_OPEN_STATUSES = {"open", "preopen"}


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
        return {
            "error": True,
            "message": "connpass APIキーが設定されていません。環境変数 CONNPASS_API_KEY を設定してください。",
        }

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
        all_events = [_parse_event(e) for e in data.get("events", [])]

        # 申し込み期限切れ・キャンセル済みイベントを除外
        events = [e for e in all_events if e.open_status in _ACTIVE_OPEN_STATUSES]
        filtered_count = len(all_events) - len(events)
        if filtered_count > 0:
            logger.info("Filtered out %d expired/cancelled events", filtered_count)

        return ConnpassSearchResult(
            results_returned=len(events),
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

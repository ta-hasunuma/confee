import json
import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("AGENT_RUNTIME_ARN", "arn:aws:bedrock:ap-northeast-1:123456789012:agent-runtime/test-id")


@pytest.fixture
def mock_agentcore_client():
    with patch("handler.boto3.client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        yield mock_client


def _make_apigw_event(body: dict) -> dict:
    return {
        "body": json.dumps(body),
        "httpMethod": "POST",
        "path": "/chat",
    }


def _make_runtime_response(response_text: str, session_id: str = "") -> dict:
    response_bytes = json.dumps({"response": response_text}).encode()
    return {
        "response": BytesIO(response_bytes),
        "runtimeSessionId": session_id,
    }


class TestHandlerParseRequest:
    """リクエストのパースをテストする"""

    def test_parses_message_from_body(self, mock_agentcore_client):
        """bodyからmessageを取得してAgentCoreに渡す"""
        from handler import handler

        mock_agentcore_client.invoke_agent_runtime.return_value = (
            _make_runtime_response("テスト応答")
        )

        event = _make_apigw_event(
            {"message": "TypeScriptのカンファレンス", "session_id": "test-session-123456789012345678901"}
        )
        handler(event, None)

        call_args = mock_agentcore_client.invoke_agent_runtime.call_args
        payload = json.loads(call_args[1]["payload"])
        assert payload["prompt"] == "TypeScriptのカンファレンス"

    def test_parses_session_id_from_body(self, mock_agentcore_client):
        """bodyからsession_idを取得してAgentCoreに渡す"""
        from handler import handler

        mock_agentcore_client.invoke_agent_runtime.return_value = (
            _make_runtime_response("テスト応答")
        )

        event = _make_apigw_event(
            {"message": "テスト", "session_id": "my-session-id-that-is-at-least-33-chars"}
        )
        handler(event, None)

        call_args = mock_agentcore_client.invoke_agent_runtime.call_args
        assert call_args[1]["runtimeSessionId"] == "my-session-id-that-is-at-least-33-chars"

    def test_returns_400_when_message_missing(self, mock_agentcore_client):
        """messageが未指定の場合400を返す"""
        from handler import handler

        event = _make_apigw_event({"session_id": "some-session"})
        response = handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "message" in body["error"]

    def test_returns_400_when_message_empty(self, mock_agentcore_client):
        """messageが空文字の場合400を返す"""
        from handler import handler

        event = _make_apigw_event({"message": "", "session_id": "some-session"})
        response = handler(event, None)

        assert response["statusCode"] == 400

    def test_generates_session_id_when_missing(self, mock_agentcore_client):
        """session_idが未指定の場合UUIDを生成する"""
        from handler import handler

        mock_agentcore_client.invoke_agent_runtime.return_value = (
            _make_runtime_response("テスト応答")
        )

        event = _make_apigw_event({"message": "テスト"})
        response = handler(event, None)

        body = json.loads(response["body"])
        assert len(body["session_id"]) >= 33

    def test_handles_missing_body(self, mock_agentcore_client):
        """bodyが存在しない場合400を返す"""
        from handler import handler

        event = {"httpMethod": "POST", "path": "/chat"}
        response = handler(event, None)

        assert response["statusCode"] == 400


class TestHandlerInvokeAgentRuntime:
    """AgentCore Runtime呼び出しをテストする"""

    def test_calls_invoke_agent_runtime_with_correct_params(
        self, mock_agentcore_client
    ):
        """invoke_agent_runtimeを正しいパラメータで呼び出す"""
        from handler import handler

        mock_agentcore_client.invoke_agent_runtime.return_value = (
            _make_runtime_response("応答テスト")
        )

        event = _make_apigw_event(
            {"message": "Pythonの勉強会", "session_id": "session-123456789012345678901234"}
        )
        handler(event, None)

        mock_agentcore_client.invoke_agent_runtime.assert_called_once()
        call_kwargs = mock_agentcore_client.invoke_agent_runtime.call_args[1]
        assert call_kwargs["agentRuntimeArn"] == "arn:aws:bedrock:ap-northeast-1:123456789012:agent-runtime/test-id"
        assert call_kwargs["runtimeSessionId"] == "session-123456789012345678901234"
        payload = json.loads(call_kwargs["payload"])
        assert payload["prompt"] == "Pythonの勉強会"

    def test_creates_boto3_client_for_bedrock_agentcore(
        self, mock_agentcore_client
    ):
        """bedrock-agentcoreクライアントを作成する"""
        with patch("handler.boto3.client") as mock_factory:
            mock_client = MagicMock()
            mock_factory.return_value = mock_client
            mock_client.invoke_agent_runtime.return_value = (
                _make_runtime_response("ok")
            )

            from handler import handler

            event = _make_apigw_event(
                {"message": "テスト", "session_id": "a" * 33}
            )
            handler(event, None)

            mock_factory.assert_called_with("bedrock-agentcore")

    def test_returns_response_and_session_id(self, mock_agentcore_client):
        """応答テキストとsession_idを返す"""
        from handler import handler

        mock_agentcore_client.invoke_agent_runtime.return_value = (
            _make_runtime_response("カンファレンスが見つかりました", "session-xyz-12345678901234567890")
        )

        event = _make_apigw_event(
            {"message": "テスト", "session_id": "session-xyz-12345678901234567890"}
        )
        response = handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["response"] == "カンファレンスが見つかりました"
        assert body["session_id"] == "session-xyz-12345678901234567890"


class TestHandlerErrorHandling:
    """エラーハンドリングをテストする"""

    def test_runtime_error_returns_503(self, mock_agentcore_client):
        """AgentCore Runtimeエラー時に503を返す"""
        from handler import handler

        mock_agentcore_client.invoke_agent_runtime.side_effect = Exception(
            "Runtime unavailable"
        )

        event = _make_apigw_event(
            {"message": "テスト", "session_id": "a" * 33}
        )
        response = handler(event, None)

        assert response["statusCode"] == 503
        body = json.loads(response["body"])
        assert "error" in body

    def test_timeout_returns_503(self, mock_agentcore_client):
        """タイムアウト時に503を返す"""
        from handler import handler
        from botocore.exceptions import ReadTimeoutError

        mock_agentcore_client.invoke_agent_runtime.side_effect = (
            ReadTimeoutError(endpoint_url="https://example.com")
        )

        event = _make_apigw_event(
            {"message": "テスト", "session_id": "a" * 33}
        )
        response = handler(event, None)

        assert response["statusCode"] == 503

    def test_invalid_json_body_returns_400(self, mock_agentcore_client):
        """不正なJSONボディの場合400を返す"""
        from handler import handler

        event = {
            "body": "not-json",
            "httpMethod": "POST",
            "path": "/chat",
        }
        response = handler(event, None)

        assert response["statusCode"] == 400


class TestHandlerCorsHeaders:
    """CORSヘッダーをテストする"""

    def test_success_response_includes_cors_headers(
        self, mock_agentcore_client
    ):
        """成功レスポンスにCORSヘッダーが含まれる"""
        from handler import handler

        mock_agentcore_client.invoke_agent_runtime.return_value = (
            _make_runtime_response("ok")
        )

        event = _make_apigw_event(
            {"message": "テスト", "session_id": "a" * 33}
        )
        response = handler(event, None)

        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "Content-Type" in response["headers"]

    def test_error_response_includes_cors_headers(
        self, mock_agentcore_client
    ):
        """エラーレスポンスにCORSヘッダーが含まれる"""
        from handler import handler

        event = _make_apigw_event({})
        response = handler(event, None)

        assert response["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_503_response_includes_cors_headers(self, mock_agentcore_client):
        """503レスポンスにCORSヘッダーが含まれる"""
        from handler import handler

        mock_agentcore_client.invoke_agent_runtime.side_effect = Exception(
            "error"
        )

        event = _make_apigw_event(
            {"message": "テスト", "session_id": "a" * 33}
        )
        response = handler(event, None)

        assert response["headers"]["Access-Control-Allow-Origin"] == "*"

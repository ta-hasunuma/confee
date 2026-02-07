from unittest.mock import MagicMock, patch

from confee_agent.agent import ConfeeAgent, SYSTEM_PROMPT


class TestConfeeAgentSystemPrompt:
    """システムプロンプトの内容テスト"""

    def test_system_prompt_requires_japanese_response(self):
        assert "日本語" in SYSTEM_PROMPT

    def test_system_prompt_mentions_conference_name(self):
        assert "カンファレンス名" in SYSTEM_PROMPT or "イベント名" in SYSTEM_PROMPT

    def test_system_prompt_mentions_date(self):
        assert "日時" in SYSTEM_PROMPT or "開催日" in SYSTEM_PROMPT

    def test_system_prompt_mentions_location(self):
        assert "場所" in SYSTEM_PROMPT or "開催場所" in SYSTEM_PROMPT

    def test_system_prompt_mentions_recommendation_score(self):
        assert "おすすめ度" in SYSTEM_PROMPT

    def test_system_prompt_mentions_deadline(self):
        assert "期限" in SYSTEM_PROMPT or "締切" in SYSTEM_PROMPT or "申込" in SYSTEM_PROMPT

    def test_system_prompt_mentions_url(self):
        assert "URL" in SYSTEM_PROMPT or "リンク" in SYSTEM_PROMPT

    def test_system_prompt_mentions_recommendation_reason(self):
        assert "理由" in SYSTEM_PROMPT or "根拠" in SYSTEM_PROMPT

    def test_system_prompt_mentions_expired_handling(self):
        assert "期限切れ" in SYSTEM_PROMPT or "過ぎ" in SYSTEM_PROMPT


class TestConfeeAgentCreation:
    """ConfeeAgent生成テスト"""

    @patch("confee_agent.agent.Agent")
    def test_create_agent_passes_system_prompt(self, mock_agent_cls):
        confee = ConfeeAgent()
        confee.create_agent()

        mock_agent_cls.assert_called_once()
        call_kwargs = mock_agent_cls.call_args
        assert call_kwargs.kwargs.get("system_prompt") == SYSTEM_PROMPT

    @patch("confee_agent.agent.Agent")
    def test_create_agent_registers_search_connpass_tool(self, mock_agent_cls):
        confee = ConfeeAgent()
        confee.create_agent()

        call_kwargs = mock_agent_cls.call_args
        tools = call_kwargs.kwargs.get("tools", [])
        assert len(tools) >= 1

    @patch("confee_agent.agent.Agent")
    def test_create_agent_uses_bedrock_model(self, mock_agent_cls):
        confee = ConfeeAgent()
        confee.create_agent()

        call_kwargs = mock_agent_cls.call_args
        model = call_kwargs.kwargs.get("model")
        assert model is not None

    @patch("confee_agent.agent.Agent")
    def test_create_agent_returns_agent_instance(self, mock_agent_cls):
        mock_agent_cls.return_value = MagicMock()
        confee = ConfeeAgent()
        agent = confee.create_agent()

        assert agent is mock_agent_cls.return_value


class TestConfeeAgentInvoke:
    """ConfeeAgent.invokeテスト"""

    @patch("confee_agent.agent.Agent")
    def test_invoke_calls_agent_with_prompt(self, mock_agent_cls):
        mock_agent = MagicMock()
        mock_agent.return_value.message = "テスト応答"
        mock_agent_cls.return_value = mock_agent

        confee = ConfeeAgent()
        confee.create_agent()
        result = confee.invoke("TypeScriptのカンファレンスある？")

        mock_agent.assert_called_once_with("TypeScriptのカンファレンスある？")

    @patch("confee_agent.agent.Agent")
    def test_invoke_returns_response_dict(self, mock_agent_cls):
        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.message = "おすすめのカンファレンスがあります"
        mock_agent.return_value = mock_result
        mock_agent_cls.return_value = mock_agent

        confee = ConfeeAgent()
        confee.create_agent()
        result = confee.invoke("面白そうなカンファレンス見つけてきて")

        assert isinstance(result, dict)
        assert "response" in result
        assert result["response"] == "おすすめのカンファレンスがあります"

    def test_invoke_without_create_raises_error(self):
        confee = ConfeeAgent()

        try:
            confee.invoke("テスト")
            assert False, "Should have raised an error"
        except RuntimeError:
            pass

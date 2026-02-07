from unittest.mock import MagicMock, patch

import confee_agent.main as main_module


class TestMainEntrypoint:
    """main.py BedrockAgentCoreApp エントリポイントテスト"""

    def setup_method(self):
        main_module._confee = None

    def teardown_method(self):
        main_module._confee = None

    @patch("confee_agent.main.ConfeeAgent")
    def test_invoke_extracts_prompt_from_payload(self, mock_confee_cls):
        mock_confee = MagicMock()
        mock_confee.invoke.return_value = {"response": "テスト応答"}
        mock_confee_cls.return_value = mock_confee

        result = main_module.invoke({"prompt": "TypeScriptのカンファレンスある？"})

        mock_confee.invoke.assert_called_once_with("TypeScriptのカンファレンスある？")

    @patch("confee_agent.main.ConfeeAgent")
    def test_invoke_returns_agent_response(self, mock_confee_cls):
        mock_confee = MagicMock()
        mock_confee.invoke.return_value = {"response": "おすすめのカンファレンスです"}
        mock_confee_cls.return_value = mock_confee

        result = main_module.invoke({"prompt": "面白いカンファレンス"})

        assert result == {"response": "おすすめのカンファレンスです"}

    @patch("confee_agent.main.ConfeeAgent")
    def test_invoke_uses_default_prompt_when_missing(self, mock_confee_cls):
        mock_confee = MagicMock()
        mock_confee.invoke.return_value = {"response": "こんにちは"}
        mock_confee_cls.return_value = mock_confee

        result = main_module.invoke({})

        mock_confee.invoke.assert_called_once_with("こんにちは！何かお手伝いできますか？")

    @patch("confee_agent.main.ConfeeAgent")
    def test_lazy_initialization_creates_agent_once(self, mock_confee_cls):
        mock_confee = MagicMock()
        mock_confee.invoke.return_value = {"response": "応答1"}
        mock_confee_cls.return_value = mock_confee

        main_module.invoke({"prompt": "質問1"})
        main_module.invoke({"prompt": "質問2"})

        mock_confee_cls.assert_called_once()
        mock_confee.create_agent.assert_called_once()

import logging
import traceback

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from confee_agent.agent import ConfeeAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

_confee = None


def _get_confee() -> ConfeeAgent:
    global _confee
    if _confee is None:
        logger.info("Initializing ConfeeAgent...")
        _confee = ConfeeAgent()
        _confee.create_agent()
        logger.info("ConfeeAgent initialized successfully")
    return _confee


@app.entrypoint
def invoke(payload):
    try:
        prompt = payload.get("prompt", "こんにちは！何かお手伝いできますか？")
        logger.info("Received prompt: %s", prompt[:100])
        result = _get_confee().invoke(prompt)
        logger.info("Agent invocation completed successfully")
        return result
    except Exception as e:
        logger.error("Agent invocation failed: %s\n%s", e, traceback.format_exc())
        return {"response": f"エラーが発生しました: {e}"}


if __name__ == "__main__":
    app.run()

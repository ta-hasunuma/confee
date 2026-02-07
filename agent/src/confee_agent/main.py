from bedrock_agentcore.runtime import BedrockAgentCoreApp

from confee_agent.agent import ConfeeAgent

app = BedrockAgentCoreApp()

_confee = None


def _get_confee() -> ConfeeAgent:
    global _confee
    if _confee is None:
        _confee = ConfeeAgent()
        _confee.create_agent()
    return _confee


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt", "こんにちは！何かお手伝いできますか？")
    return _get_confee().invoke(prompt)


if __name__ == "__main__":
    app.run()

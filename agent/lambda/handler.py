import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def handler(event, context):
    try:
        body_str = event.get("body") or "{}"
        body = json.loads(body_str)
    except (json.JSONDecodeError, TypeError):
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Invalid JSON body"}),
        }

    message = body.get("message", "")
    if not message:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "message is required"}),
        }

    session_id = body.get("session_id", "")
    if not session_id:
        session_id = f"{uuid.uuid4()}-{uuid.uuid4().hex[:8]}"

    try:
        client = boto3.client("bedrock-agentcore")
        response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            payload=json.dumps({"prompt": message}).encode("utf-8"),
            runtimeSessionId=session_id,
        )

        response_body = json.loads(response["response"].read())

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {
                    "response": response_body.get("response", ""),
                    "session_id": response.get(
                        "runtimeSessionId"
                    )
                    or session_id,
                }
            ),
        }
    except Exception as e:
        logger.error("AgentCore invocation failed: %s", e, exc_info=True)
        return {
            "statusCode": 503,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {"error": "Service temporarily unavailable"}
            ),
        }

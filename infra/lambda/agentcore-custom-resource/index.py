import json
import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _get_client():
    return boto3.client("bedrock-agentcore-control")


def on_event(event, context):
    """CloudFormation Custom Resource の onCreate/onUpdate/onDelete ハンドラー"""
    request_type = event["RequestType"]
    props = event["ResourceProperties"]

    logger.info("Received %s request", request_type)

    if request_type == "Create":
        return _on_create(props)
    elif request_type == "Update":
        return _on_update(event, props)
    elif request_type == "Delete":
        return _on_delete(event)
    else:
        raise ValueError(f"Unknown RequestType: {request_type}")


def _on_create(props):
    client = _get_client()

    params = {
        "agentRuntimeName": props["agentRuntimeName"],
        "agentRuntimeArtifact": json.loads(props["agentRuntimeArtifact"]),
        "networkConfiguration": json.loads(props["networkConfiguration"]),
        "roleArn": props["roleArn"],
    }

    if props.get("description"):
        params["description"] = props["description"]

    if props.get("environmentVariables"):
        params["environmentVariables"] = json.loads(
            props["environmentVariables"]
        )

    response = client.create_agent_runtime(**params)

    logger.info(
        "Created agent runtime: %s (ARN: %s)",
        response["agentRuntimeId"],
        response["agentRuntimeArn"],
    )

    return {
        "PhysicalResourceId": response["agentRuntimeId"],
        "Data": {
            "AgentRuntimeId": response["agentRuntimeId"],
            "AgentRuntimeArn": response["agentRuntimeArn"],
        },
    }


def _on_update(event, props):
    physical_id = event["PhysicalResourceId"]
    client = _get_client()

    params = {
        "agentRuntimeId": physical_id,
        "agentRuntimeArtifact": json.loads(props["agentRuntimeArtifact"]),
        "networkConfiguration": json.loads(props["networkConfiguration"]),
        "roleArn": props["roleArn"],
    }

    if props.get("description"):
        params["description"] = props["description"]

    if props.get("environmentVariables"):
        params["environmentVariables"] = json.loads(
            props["environmentVariables"]
        )

    response = client.update_agent_runtime(**params)

    logger.info(
        "Updating agent runtime: %s (ARN: %s)",
        response["agentRuntimeId"],
        response["agentRuntimeArn"],
    )

    return {
        "PhysicalResourceId": response["agentRuntimeId"],
        "Data": {
            "AgentRuntimeId": response["agentRuntimeId"],
            "AgentRuntimeArn": response["agentRuntimeArn"],
        },
    }


def _on_delete(event):
    physical_id = event["PhysicalResourceId"]
    client = _get_client()

    try:
        client.delete_agent_runtime(agentRuntimeId=physical_id)
        logger.info("Deleting agent runtime: %s", physical_id)
    except client.exceptions.ResourceNotFoundException:
        logger.info("Agent runtime already deleted: %s", physical_id)

    return {"PhysicalResourceId": physical_id}


def is_complete(event, context):
    """非同期完了チェック: Runtime が READY/DELETING完了 になるまでポーリング"""
    request_type = event["RequestType"]
    physical_id = event["PhysicalResourceId"]

    client = _get_client()

    if request_type == "Delete":
        try:
            response = client.get_agent_runtime(agentRuntimeId=physical_id)
            status = response["status"]
            logger.info("Delete polling - status: %s", status)
            return {"IsComplete": False}
        except client.exceptions.ResourceNotFoundException:
            logger.info("Agent runtime deleted successfully")
            return {"IsComplete": True}

    # Create / Update
    try:
        response = client.get_agent_runtime(agentRuntimeId=physical_id)
        status = response["status"]
        logger.info("Create/Update polling - status: %s", status)

        if status == "READY":
            return {
                "IsComplete": True,
                "Data": {
                    "AgentRuntimeId": response["agentRuntimeId"],
                    "AgentRuntimeArn": response["agentRuntimeArn"],
                },
            }
        elif status in ("CREATE_FAILED", "UPDATE_FAILED"):
            raise RuntimeError(
                f"Agent runtime failed with status: {status}"
            )

        return {"IsComplete": False}
    except client.exceptions.ResourceNotFoundException:
        raise RuntimeError(
            f"Agent runtime {physical_id} not found during polling"
        )

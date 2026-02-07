#!/usr/bin/env node
import * as cdk from "aws-cdk-lib/core";
import { ConfeeAgentCoreStack } from "../lib/agentcore-stack";
import { ConfeeApiStack } from "../lib/api-stack";
import { ConfeeFrontendStack } from "../lib/frontend-stack";

const app = new cdk.App();

const agentCoreStack = new ConfeeAgentCoreStack(app, "ConfeeAgentCoreStack");

new ConfeeApiStack(app, "ConfeeApiStack", {
  agentRuntimeArn: agentCoreStack.agentRuntimeArn,
});

new ConfeeFrontendStack(app, "ConfeeFrontendStack");

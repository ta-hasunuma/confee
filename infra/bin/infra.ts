#!/usr/bin/env node
import * as cdk from "aws-cdk-lib/core";
import { ConfeeApiStack } from "../lib/api-stack";
import { ConfeeFrontendStack } from "../lib/frontend-stack";

const app = new cdk.App();
new ConfeeApiStack(app, "ConfeeApiStack");
new ConfeeFrontendStack(app, "ConfeeFrontendStack");

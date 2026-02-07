import * as cdk from "aws-cdk-lib/core";
import { Template, Match } from "aws-cdk-lib/assertions";
import { ConfeeAgentCoreStack } from "../lib/agentcore-stack";

describe("ConfeeAgentCoreStack", () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new ConfeeAgentCoreStack(app, "TestAgentCoreStack");
    template = Template.fromStack(stack);
  });

  test("AgentCore Runtime用のIAMロールが作成される", () => {
    template.hasResourceProperties("AWS::IAM::Role", {
      AssumeRolePolicyDocument: Match.objectLike({
        Statement: Match.arrayWith([
          Match.objectLike({
            Action: "sts:AssumeRole",
            Effect: "Allow",
          }),
        ]),
      }),
    });
  });

  test("on_event Lambda関数が作成される", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Handler: "index.on_event",
      Runtime: "python3.13",
      Timeout: 300,
    });
  });

  test("is_complete Lambda関数が作成される", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Handler: "index.is_complete",
      Runtime: "python3.13",
      Timeout: 300,
    });
  });

  test("Custom Resourceが作成される", () => {
    template.hasResourceProperties("AWS::CloudFormation::CustomResource", {
      agentRuntimeName: "confee_agent",
    });
  });

  test("AgentRuntimeIdの出力が定義される", () => {
    template.hasOutput("AgentRuntimeId", {});
  });

  test("AgentRuntimeArnの出力が定義される", () => {
    template.hasOutput("AgentRuntimeArn", {});
  });

  test("AgentRuntimeRoleArnの出力が定義される", () => {
    template.hasOutput("AgentRuntimeRoleArn", {});
  });
});

import * as cdk from "aws-cdk-lib/core";
import { Template } from "aws-cdk-lib/assertions";
import { ConfeeApiStack } from "../lib/api-stack";

describe("ConfeeApiStack", () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new ConfeeApiStack(app, "TestApiStack");
    template = Template.fromStack(stack);
  });

  test("Lambda関数が作成される", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Runtime: "python3.13",
      Handler: "index.handler",
    });
  });

  test("API Gateway REST APIが作成される", () => {
    template.hasResourceProperties("AWS::ApiGateway::RestApi", {
      Name: "confee-api",
    });
  });

  test("/health GETメソッドが作成される", () => {
    template.hasResourceProperties("AWS::ApiGateway::Method", {
      HttpMethod: "GET",
    });
  });
});

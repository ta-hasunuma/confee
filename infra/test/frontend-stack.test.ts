import * as cdk from "aws-cdk-lib/core";
import { Template } from "aws-cdk-lib/assertions";
import { ConfeeFrontendStack } from "../lib/frontend-stack";

describe("ConfeeFrontendStack", () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new ConfeeFrontendStack(app, "TestFrontendStack");
    template = Template.fromStack(stack);
  });

  test("S3バケットが作成される", () => {
    template.hasResourceProperties("AWS::S3::Bucket", {
      WebsiteConfiguration: {
        IndexDocument: "index.html",
      },
    });
  });

  test("CloudFrontディストリビューションが作成される", () => {
    template.resourceCountIs("AWS::CloudFront::Distribution", 1);
  });
});

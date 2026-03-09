import * as cdk from "aws-cdk-lib/core";
import { Template, Match } from "aws-cdk-lib/assertions";
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

  test("CloudFront Functionが作成される", () => {
    template.resourceCountIs("AWS::CloudFront::Function", 1);
  });

  test("CloudFront FunctionがDistributionにviewer-requestとして関連付けられる", () => {
    template.hasResourceProperties("AWS::CloudFront::Distribution", {
      DistributionConfig: {
        DefaultCacheBehavior: Match.objectLike({
          FunctionAssociations: Match.arrayWith([
            Match.objectLike({
              EventType: "viewer-request",
            }),
          ]),
        }),
      },
    });
  });

  test("distributionDomainNameプロパティが公開されている", () => {
    const app = new cdk.App();
    const stack = new ConfeeFrontendStack(app, "TestDomainStack");
    expect(stack.distributionDomainName).toBeDefined();
  });
});

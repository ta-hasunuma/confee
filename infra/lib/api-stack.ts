import * as cdk from "aws-cdk-lib/core";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as iam from "aws-cdk-lib/aws-iam";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as wafv2 from "aws-cdk-lib/aws-wafv2";
import { Construct } from "constructs";
import * as path from "path";
import { ALLOWED_IP_CIDRS } from "./config/allowed-ips";

export interface ConfeeApiStackProps extends cdk.StackProps {
  agentRuntimeArn: string;
}

export class ConfeeApiStack extends cdk.Stack {
  public readonly api: apigateway.RestApi;

  constructor(scope: Construct, id: string, props: ConfeeApiStackProps) {
    super(scope, id, props);

    // connpass APIキー用のSecrets Manager シークレット
    const connpassApiKeySecret = new secretsmanager.Secret(
      this,
      "ConnpassApiKeySecret",
      {
        secretName: "confee/connpass-api-key",
        description: "connpass API key for confee agent",
      }
    );

    // Health Check Lambda
    const healthFunction = new lambda.Function(this, "HealthFunction", {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "index.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "../lambda/health")),
      timeout: cdk.Duration.seconds(10),
    });

    // Chat Lambda Proxy
    const chatLambdaPath = path.join(__dirname, "../../agent/lambda");
    const chatFunction = new lambda.Function(this, "ChatFunction", {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "handler.handler",
      code: lambda.Code.fromAsset(chatLambdaPath, {
        exclude: ["tests", "tests/**", "__pycache__"],
        bundling: {
          image: lambda.Runtime.PYTHON_3_13.bundlingImage,
          command: [
            "bash",
            "-c",
            "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
          ],
        },
      }),
      timeout: cdk.Duration.seconds(60),
      environment: {
        AGENT_RUNTIME_ARN: props.agentRuntimeArn,
      },
    });

    // Lambda に AgentCore Runtime 呼び出し権限を付与
    chatFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["bedrock-agentcore:InvokeAgentRuntime"],
        resources: ["*"],
      })
    );

    // Lambda に Secrets Manager 読み取り権限を付与
    connpassApiKeySecret.grantRead(chatFunction);

    // API Gateway
    this.api = new apigateway.RestApi(this, "ConfeeApi", {
      restApiName: "confee-api",
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ["Content-Type"],
      },
    });

    // GET /health
    const health = this.api.root.addResource("health");
    health.addMethod("GET", new apigateway.LambdaIntegration(healthFunction));

    // POST /chat
    const chat = this.api.root.addResource("chat");
    chat.addMethod("POST", new apigateway.LambdaIntegration(chatFunction));

    // API Gateway 自身のエラーレスポンスにも CORS ヘッダーを付与
    this.api.addGatewayResponse("Default4xx", {
      type: apigateway.ResponseType.DEFAULT_4XX,
      responseHeaders: {
        "Access-Control-Allow-Origin": "'*'",
        "Access-Control-Allow-Headers": "'Content-Type'",
      },
    });
    this.api.addGatewayResponse("Default5xx", {
      type: apigateway.ResponseType.DEFAULT_5XX,
      responseHeaders: {
        "Access-Control-Allow-Origin": "'*'",
        "Access-Control-Allow-Headers": "'Content-Type'",
      },
    });

    new cdk.CfnOutput(this, "ApiUrl", {
      value: this.api.url,
      description: "API Gateway URL",
    });

    // WAF IPSet
    const ipSet = new wafv2.CfnIPSet(this, "AllowedIpSet", {
      name: "confee-allowed-ips",
      scope: "REGIONAL",
      ipAddressVersion: "IPV4",
      addresses: ALLOWED_IP_CIDRS,
    });

    // WAF WebACL
    const webAcl = new wafv2.CfnWebACL(this, "ApiWebAcl", {
      name: "confee-api-waf",
      scope: "REGIONAL",
      defaultAction: { block: {} },
      visibilityConfig: {
        cloudWatchMetricsEnabled: true,
        metricName: "confee-api-waf",
        sampledRequestsEnabled: true,
      },
      rules: [
        {
          name: "AllowWhitelistedIPs",
          priority: 1,
          action: { allow: {} },
          statement: {
            ipSetReferenceStatement: {
              arn: ipSet.attrArn,
            },
          },
          visibilityConfig: {
            cloudWatchMetricsEnabled: true,
            metricName: "confee-allowed-ips",
            sampledRequestsEnabled: true,
          },
        },
      ],
    });

    // WAF WebACL → API Gateway ステージ関連付け
    new wafv2.CfnWebACLAssociation(this, "ApiWafAssociation", {
      resourceArn: `arn:aws:apigateway:${this.region}::/restapis/${this.api.restApiId}/stages/${this.api.deploymentStage.stageName}`,
      webAclArn: webAcl.attrArn,
    });
  }
}

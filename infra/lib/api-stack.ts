import * as cdk from "aws-cdk-lib/core";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as iam from "aws-cdk-lib/aws-iam";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";
import * as path from "path";

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

    new cdk.CfnOutput(this, "ApiUrl", {
      value: this.api.url,
      description: "API Gateway URL",
    });
  }
}

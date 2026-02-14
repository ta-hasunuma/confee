import * as cdk from "aws-cdk-lib/core";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as ecr_assets from "aws-cdk-lib/aws-ecr-assets";
import * as cr from "aws-cdk-lib/custom-resources";
import { Construct } from "constructs";
import * as path from "path";

export class ConfeeAgentCoreStack extends cdk.Stack {
  public readonly agentRuntimeArn: string;
  public readonly agentRuntimeRoleArn: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // エージェントコンテナイメージのビルド＆ECRプッシュ
    const agentImage = new ecr_assets.DockerImageAsset(this, "AgentImage", {
      directory: path.join(__dirname, "../../agent"),
      platform: ecr_assets.Platform.LINUX_ARM64,
    });

    // AgentCore Runtime用のIAMロール
    const agentRuntimeRole = new iam.Role(this, "AgentRuntimeRole", {
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
      description: "IAM role for confee AgentCore Runtime",
    });

    // Bedrock モデル呼び出し権限
    agentRuntimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // CloudWatch Logs 書き込み権限
    agentRuntimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        resources: ["*"],
      })
    );

    // ECR イメージ取得権限
    agentImage.repository.grantPull(agentRuntimeRole);

    // Secrets Manager 読み取り権限 (connpass API キー)
    agentRuntimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["secretsmanager:GetSecretValue"],
        resources: [
          `arn:aws:secretsmanager:*:${this.account}:secret:confee/connpass-api-key-*`,
        ],
      })
    );

    // Custom Resource Lambda: AgentCore Runtime 作成/削除
    const onEventHandler = new lambda.Function(
      this,
      "AgentRuntimeOnEventHandler",
      {
        runtime: lambda.Runtime.PYTHON_3_13,
        handler: "index.on_event",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../lambda/agentcore-custom-resource")
        ),
        timeout: cdk.Duration.minutes(5),
        initialPolicy: [
          new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
              "bedrock-agentcore:*",
              "iam:PassRole",
              "iam:CreateServiceLinkedRole",
            ],
            resources: ["*"],
          }),
        ],
      }
    );

    const isCompleteHandler = new lambda.Function(
      this,
      "AgentRuntimeIsCompleteHandler",
      {
        runtime: lambda.Runtime.PYTHON_3_13,
        handler: "index.is_complete",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../lambda/agentcore-custom-resource")
        ),
        timeout: cdk.Duration.minutes(5),
        initialPolicy: [
          new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: ["bedrock-agentcore:*"],
            resources: ["*"],
          }),
        ],
      }
    );

    const provider = new cr.Provider(this, "AgentRuntimeProvider", {
      onEventHandler,
      isCompleteHandler,
      totalTimeout: cdk.Duration.minutes(30),
      queryInterval: cdk.Duration.seconds(30),
    });

    const agentRuntime = new cdk.CustomResource(this, "AgentRuntime", {
      serviceToken: provider.serviceToken,
      properties: {
        agentRuntimeName: "confee_agent",
        description:
          "Conference recommendation agent powered by connpass API",
        agentRuntimeArtifact: JSON.stringify({
          containerConfiguration: {
            containerUri: agentImage.imageUri,
          },
        }),
        networkConfiguration: JSON.stringify({
          networkMode: "PUBLIC",
        }),
        roleArn: agentRuntimeRole.roleArn,
        environmentVariables: JSON.stringify({
          AWS_DEFAULT_REGION: "ap-northeast-1",
        }),
      },
    });

    this.agentRuntimeArn = agentRuntime.getAttString("AgentRuntimeArn");
    this.agentRuntimeRoleArn = agentRuntimeRole.roleArn;

    new cdk.CfnOutput(this, "AgentRuntimeId", {
      value: agentRuntime.getAttString("AgentRuntimeId"),
      description: "AgentCore Runtime ID",
    });

    new cdk.CfnOutput(this, "AgentRuntimeArn", {
      value: this.agentRuntimeArn,
      description: "AgentCore Runtime ARN",
    });

    new cdk.CfnOutput(this, "AgentRuntimeRoleArn", {
      value: this.agentRuntimeRoleArn,
      description: "AgentCore Runtime IAM Role ARN",
    });

    new cdk.CfnOutput(this, "AgentImageUri", {
      value: agentImage.imageUri,
      description: "Agent container image URI",
    });
  }
}

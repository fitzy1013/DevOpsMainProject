from aws_cdk import Stack, Duration
from constructs import Construct
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as actions
import aws_cdk.aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions

evaluation_periods = 1
namespace = 'devops'
metric_name = 'devops'
sites = ['https://fbref.com/en/', 'https://github.com']
metric_type = ['status', 'latency']
alarm_names = ["MyAlarm1", "MyAlarm2", "MyAlarm3", "MyAlarm4"]
thresholds = [1, 0.05]
comparison = [cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD, cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD]


class MyProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the Lambda function
        function = _lambda.Function(self, "lambda_function",
                                    runtime=_lambda.Runtime.PYTHON_3_10,
                                    handler="index.index_handler",
                                    code=_lambda.Code.from_asset("handler")
                                    )

        invoked_function = _lambda.Function(self, "lambda_function_invoked",
                                            runtime=_lambda.Runtime.PYTHON_3_10,
                                            handler="invoked.index_handler",
                                            code=_lambda.Code.from_asset("handler")
                                            )

        # Create the CloudWatchFullAccess policy
        cloudwatch_full_access_policy = iam.ManagedPolicy(self, "CloudWatchFullAccessPolicy",
                                                          managed_policy_name="CloudWatchFullAccess",
                                                          statements=[
                                                              iam.PolicyStatement(
                                                                  actions=["cloudwatch:*"],
                                                                  resources=["*"]
                                                              )
                                                          ]
                                                          )

        dynamodb_full_access_policy = iam.ManagedPolicy(self, "DynamoDBFullAccessPolicy",
                                                        managed_policy_name="DynamoDBFullAccess",
                                                        statements=[
                                                            iam.PolicyStatement(
                                                                actions=["dynamodb:*"],
                                                                resources=["*"]
                                                            )
                                                        ]
                                                        )

        # Attach the CloudWatchFullAccess policy to the Lambda function's role
        function.role.add_managed_policy(cloudwatch_full_access_policy)
        invoked_function.role.add_managed_policy(dynamodb_full_access_policy)

        # Create a CloudWatch Events rule and associate it with the Lambda function
        rule = events.Rule(self, "schedule_rule",
                           schedule=events.Schedule.rate(Duration.minutes(1)),
                           targets=[targets.LambdaFunction(function)]
                           )

        topic = sns.Topic(self, "MyTopic")

        # sns.Subscription(self, "EmailSubscription",
        #                  topic=topic,
        #                  endpoint="liamfitzmaurice@hotmail.com",
        #                  protocol=sns.SubscriptionProtocol.EMAIL
        #                  )

        topic.add_subscription(subscriptions.LambdaSubscription(invoked_function))
        topic.add_subscription(subscriptions.EmailSubscription("liamfitzmaurice@hotmail.com"))

        for x in range(4):
            my_metric = cloudwatch.Metric(
                namespace=namespace,
                metric_name=metric_name,
                dimensions_map={sites[x % 2]: metric_type[0 if (x < 2) else 1]}
            )

            alarm = cloudwatch.Alarm(self, alarm_names[x],
                                     evaluation_periods=evaluation_periods,
                                     threshold=thresholds[0 if (x < 2) else 1],
                                     comparison_operator=comparison[0 if (x < 2) else 1],
                                     metric=my_metric,
                                     actions_enabled=True
                                     )

            alarm.add_alarm_action(actions.SnsAction(topic))

        # my_metric1 = cloudwatch.Metric(
        #     namespace='devops',
        #     metric_name='devops',
        #     dimensions_map={'https://fbref.com/en/': 'status'}
        # )
        #
        # my_metric2 = cloudwatch.Metric(
        #     namespace='devops',
        #     metric_name='devops',
        #     dimensions_map={'https://github.com': 'status'}
        # )
        #
        # alarm1 = cloudwatch.Alarm(self, "MyAlarm1",
        #                           evaluation_periods=evaluation_periods,
        #                           threshold=1,
        #                           comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
        #                           metric=my_metric1,
        #                           actions_enabled=True
        #                           )
        #
        # alarm2 = cloudwatch.Alarm(self, "MyAlarm2",
        #                           evaluation_periods=3,
        #                           threshold=1,
        #                           comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
        #                           metric=my_metric2,
        #                           actions_enabled=True
        #                           )
        #
        # alarm1.add_alarm_action(actions.SnsAction(topic))
        # alarm2.add_alarm_action(actions.SnsAction(topic))

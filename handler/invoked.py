import time

import boto3
import json

dynamoDB = boto3.client('dynamodb')

table_name = 'AlarmTable'
key_schema = [
    {
        'AttributeName': 'alarm_arn',
        'KeyType': 'HASH'
    },
    {
        'AttributeName': 'timestamp',
        'KeyType': 'RANGE'
    }
]

attribute_definitions = [
    {
        'AttributeName': 'alarm_arn',
        'AttributeType': 'S'
    },
    {
        'AttributeName': 'timestamp',
        'AttributeType': 'S'
    }
    # {
    #     'AttributeName': 'metric_namespace',
    #     'AttributeType': 'S'
    # },
    # {
    #     'AttributeName': 'metric_dimensions',
    #     'AttributeType': 'S'
    # },
    # {
    #     'AttributeName': 'alarm_reason',
    #     'AttributeType': 'S'
    # }
]

provisioned_throughput = {
    'ReadCapacityUnits': 5,
    'WriteCapacityUnits': 5
}


def wait_for_table_activation():
    while True:
        response = dynamoDB.describe_table(TableName=table_name)
        if response['Table']['TableStatus'] == 'ACTIVE':
            print(f"Table '{table_name}' is now active.")
            break
        else:
            print(f"Table status: {response['Table']['TableStatus']}. Waiting for table to become active...")
            time.sleep(5)  # Sleep for a few seconds before checking again


def index_handler(event, context):
    print("Received event for CloudWatch Alarm:")
    timestamp = event['Records'][0]['Sns']['Timestamp']
    sns_message = event['Records'][0]['Sns']['Message']
    sns_message_dict = json.loads(sns_message)

    alarm_arn = sns_message_dict.get("AlarmArn")
    alarm_new_value = sns_message_dict.get("NewStateValue")

    if alarm_new_value != "ALARM":
        pass
    else:
        try:
            response = dynamoDB.describe_table(TableName=table_name)
            print(f"Table '{table_name}' already exists.")
        except dynamoDB.exceptions.ResourceNotFoundException:
            print(f"Table '{table_name}' does not exist. Creating...")

            dynamoDB.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                ProvisionedThroughput=provisioned_throughput
            )

            wait_for_table_activation()

        item = {
            'alarm_arn': {'S': alarm_arn},
            'timestamp': {'S': timestamp}
        }

        response = dynamoDB.put_item(
            TableName=table_name,
            Item=item
        )

        print(response)

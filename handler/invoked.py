import time

import boto3
import json

dynamoDB = boto3.client('dynamodb')

table_name = 'AlarmTable'
key_schema = [
    {
        'AttributeName': 'alarm_arn',  # alarm ARN used as the primary hash
        'KeyType': 'HASH'
    },
    {
        'AttributeName': 'timestamp',  # timestamp used as a secondary sort
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

provisioned_throughput = {  # setting the read and write capacity
    'ReadCapacityUnits': 5,
    'WriteCapacityUnits': 5
}


def wait_for_table_activation():
    while True:
        response = dynamoDB.describe_table(TableName=table_name)  # checks to see if described table is active
        if response['Table']['TableStatus'] == 'ACTIVE':
            print(f"Table '{table_name}' is now active.")
            break
        else:
            print(f"Table status: {response['Table']['TableStatus']}. Waiting for table to become active...")
            time.sleep(5)  # Sleep for a few seconds before checking again


def index_handler(event, context):
    print("Received event for CloudWatch Alarm:")
    timestamp = event['Records'][0]['Sns']['Timestamp']  # gets the timestamp form the event
    sns_message = event['Records'][0]['Sns']['Message']  # gets the message which has all information about the alarm
    sns_message_dict = json.loads(sns_message) # this section is formatted in json so needs to be parsed

    alarm_arn = sns_message_dict.get("AlarmArn")  # getting the alarm ARN
    alarm_new_value = sns_message_dict.get("NewStateValue")  # getting the new state of the alarm determine whether
    # to add to the database

    if alarm_new_value != "ALARM":  # checks that the alert is an alarm and not just any other change of state
        pass
    else:
        try:
            response = dynamoDB.describe_table(TableName=table_name)  # checks to see if table exists
            print(f"Table '{table_name}' already exists.")
        except dynamoDB.exceptions.ResourceNotFoundException:
            print(f"Table '{table_name}' does not exist. Creating...")

            dynamoDB.create_table(  # if table doesn't exists create new table
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                ProvisionedThroughput=provisioned_throughput
            )

            wait_for_table_activation()  # helper function to ensure table is created before attempting to add data

        item = {
            'alarm_arn': {'S': alarm_arn},
            'timestamp': {'S': timestamp}
        }

        response = dynamoDB.put_item(  # adds the new record to the database
            TableName=table_name,
            Item=item
        )

        print(response)

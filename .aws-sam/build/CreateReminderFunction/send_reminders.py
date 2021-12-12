import dateutil.parser
import time
import boto3
import json
#from boto3.dynamodb.conditions import Key, Attr
import os
import ulid

lam = boto3.client('lambda')
dynamodb_client = boto3.client('dynamodb')
table_name = os.environ['REMINDERS_DDB_TABLE']
#email_reminder_function = os.environ['EMAIL_REMINDER_FUNCTION']
#text_reminder_function = os.environ['TEXT_REMINDER_FUNCTION']
#dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
#table = dynamodb.Table('reminders')

def alert_is_due(item_ulid):
    curr_unix_time = int(str(time.time()).split(".")[0])
    print(f'{curr_unix_time=}')
    print(f'{item_ulid=}')
    curr_unix_ulid = ulid.from_timestamp(curr_unix_time)
    print(f'{curr_unix_ulid=}')
    is_elapsed = item_ulid < curr_unix_ulid
    print(f'{is_elapsed=}')
    return is_elapsed

def lambda_handler(event, context):
    response = dynamodb_client.query(
        TableName = table_name,
        Limit=100,
        ScanIndexForward=True,
        KeyConditionExpression='#pk1 = :pk1',
        ExpressionAttributeNames={
            '#pk1': 'PK1'
        },
        ExpressionAttributeValues={
            ':pk1': {'S': 'REMINDER'}
        }
    )
    items = response['Items']
    print(items)
    response_items = []
    for item in items:
        item_ulid = ulid.from_str(item['SK1']['S'])
        if not alert_is_due(item_ulid):
            break
        print('reminder!')
        response_items.append(item)
        continue
        reminder = item['reminder']
        payload = {}
        payload['subject'] = reminder
        payload['body'] = "Friendly reminder of the following: " + reminder
        try:
            lam.invoke(FunctionName='emailReminder',
                       InvocationType='Event',
                       Payload=json.dumps(payload))
            payload = {
                "number": "+12403937527",
                "body": reminder
            }
            lam.invoke(FunctionName='textReminder',
                       InvocationType='Event',
                       Payload=json.dumps(payload))
        except Exception as e:
            print(e)
            raise e
        table.delete_item(Key = {'unixtimestamp': item['unixtimestamp']})
    return response_items
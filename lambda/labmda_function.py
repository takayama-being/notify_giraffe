import boto3
import slackweb
import os
import json

webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
s3_region = os.environ.get("REGION")
slack = slackweb.Slack(url=webhook_url)

s3_client = boto3.client('s3', region_name=s3_region)

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # パブリックにアクセスさせないようにしているので、署名付きURLを発行する。
    # いつでもアクセスできるようにしたければs3のポリシーを修正し以下をコメントイン。
    # image_object_url = f"https://s3-{s3_region}.amazonaws.com/{bucket}/{key}"
    image_object_url = s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': bucket, 'Key': key},
    ExpiresIn=3600
    )
    
    json_key = f'{os.path.splitext(key)[0]}.json'
    response = s3_client.get_object(Bucket=bucket, Key=json_key)
    data = json.loads(response['Body'].read())
    
    output_string = ''
    for key, value in data['classifications'].items():
        output_string += f"{key}: {value['category']} {value['score']}\n"


    attachments = [{"text":  f'しまうま発見！\n {output_string}', "image_url": image_object_url}]
    slack.notify(attachments=attachments)
        
    return {
        'statusCode': 200,
        'body': 'OK'
    }

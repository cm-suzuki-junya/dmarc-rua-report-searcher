import email, io, json
import boto3
import xmltodict

from dmarc_reports.classes import AggregateReport
from dmarc_reports.exceptions import BadAggregateReport

s3 = boto3.client('s3')

def lambda_handler(event, context):
    print(event)
    output_prefix = "output"

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    resp = s3.get_object(Bucket=bucket, Key=key)
    eml_file = resp['Body']
    mail = email.message_from_bytes(eml_file.read())

    # AggregateReportの機能ではなくinitによるバリデーションを期待している
    # TODO: 良き感じに例外処理を入れる
    try:
        AggregateReport(io.StringIO(mail.get_payload()))
    except BadAggregateReport as error:
        print("This report is invalid format")
        return {
            "StatsuCode": 200,
            "Body": ""
        }
    
    json_mailbody = xmltodict.parse(mail.get_payload())

    print(type(json_mailbody['feedback']['record']))
    # Convert 'Record' to list if dict
    if type(json_mailbody['feedback']['record']) is not list:
        json_mailbody['feedback']['record'] = [json_mailbody['feedback']['record']]

    # Parse filename
    # source key example: srouce/mailuser/mail-id.eml
    # output_key example: destination/mailuser/mail-id.eml.json
    output_key = "{}.json".format('/'.join([output_prefix] + key.split('/')[1:]))

    s3.put_object(Bucket=bucket, Key=output_key,Body=json.dumps(json_mailbody, separators=(',', ':')))
    
    return {
        "statusCode": 200,
        "body": "",
    }

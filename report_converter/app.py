import email, io, json, base64, zipfile
import boto3
import xmltodict

from dmarc_reports.classes import AggregateReport
from dmarc_reports.exceptions import BadAggregateReport

s3 = boto3.client('s3')

def lambda_handler(event, context):
    output_prefix = "output"

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    resp = s3.get_object(Bucket=bucket, Key=key)

    eml_file = resp['Body']
    mail = email.message_from_bytes(eml_file.read())
    
    report = get_report(mail)

    # AggregateReportの機能ではなくinitによるバリデーションを期待している
    # TODO: 良き感じに例外処理を入れる
    try:
        AggregateReport(io.StringIO(report))
    except BadAggregateReport as error:
        print("This report is invalid format")
        return {
            "StatsuCode": 200,
            "Body": "Invalid format report"
        }
    
    json_mailbody = xmltodict.parse(report)
    shaped_dmarc_json(json_mailbody)

    # Parse filename
    # source key example: srouce/mailuser/mail-id.eml
    # output_key example: destination/mailuser/mail-id.eml.json
    output_key = "{}.json".format('/'.join([output_prefix] + key.split('/')[1:]))

    s3.put_object(Bucket=bucket, Key=output_key,Body=json.dumps(json_mailbody, separators=(',', ':')))
    
    return {
        "statusCode": 200,
        "body": "",
    }

def get_report(mail):
    
    '''
        Emailオブジェクトからレポートを抽出する
    '''
    raw_payload = mail.get_payload()
    if mail.get('Content-Transfer-Encoding') == 'base64':
        payload = base64.b64decode(raw_payload)

    match mail.get_content_type():
        case 'application/zip':
            z = zipfile.ZipFile(io.BytesIO(payload))
            return z.read(z.namelist()[0]).decode('utf-8')
        case 'application/gzip':
            pass
        case _:
            return raw_payload

def shaped_dmarc_json(data):
    '''
        受け取ったJSON形式のDMARCレポートを整形する
    '''
    # Convert 'Record' to list if dict
    if type(data['feedback']['record']) is not list:
        data['feedback']['record'] = [data['feedback']['record']]

    # Convert 'dkim' to list if dict
    for i,d in enumerate(data['feedback']['record']):
        if 'auth_results' in d:
            if 'dkim' in d['auth_results'] and type(d['auth_results']['dkim']) is not list:
                data['feedback']['record'][i]['auth_results']['dkim'] = [data['feedback']['record'][i]['auth_results']['dkim']]
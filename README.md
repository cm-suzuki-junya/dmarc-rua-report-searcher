## 概要

DMARCをAmazon SESで受信しJSONに変換したものを同バケットに格納し、Athenaで検索するサンプル

## 詳細

以下のリソースを生成します。

- Amazon SESの受信ルール設定
- 上記メールを受信するS3バケット
  - `source/{{MailUser}}/`配下に受診したメール格納
- 上記バケットに受信したメールをもとに集計レポートをJSONに変換し再格納する
  - `source/{{MailUser}}/`配下に変換後JSONを格納

CloudFormationでルールの割り当ての方が対応していないため手動で設定が必要です。  
拡張としてAthenaのテーブルを作成することで分析可能ですがGlue::TableではなくAthena上でテーブルを作成する方式を選択したため別途対応が必要です。

テーブルの作成は`example-create-table.sql`で行えますが、実際のデータを元に生成しているためキーが不足している可能性がございます。

以下のページをご参照ください。

https://dev.classmethod.jp/articles/received-and-search-dmarc-report-used-ses-and-athena/

## デプロイ

`.env.example`を参考に事前に`.env`を作成します。  

```bash
sam build
sam deploy --parameter-overrides file://.env
```

## ローカルでの動作確認

テストコードは用意していませんが直接S3にメールファイルを格納し、`events/s3-put-sample.json`を元に良い感じに設定をすると変換部分の動作確認が可能です。

`s3.bucket.name`に実際の格納先のバケット名、`s3.object.key`に格納したファイルのキーを指定しイベントファイルとして利用することでローカルで受信後〜変換までのテストが可能です。

```bash
sam build
sam local invoke -e events/s3-put-sample.json
```

## Athenaによる検索例

SPFおよびDKIMいずれにも合致しないメールの送信もとIP毎の総和を算出する

```sql
WITH records AS (
    SELECT feedback.record as record
    FROM dmarc_report
)
SELECT
    rec.row.source_ip,
    SUM(CAST(rec.row.count AS Integer)) AS cnt
FROM records, UNNEST(record) AS t(rec)
WHERE rec.row.policy_evaluated.spf != 'pass' AND rec.row.policy_evaluated.dkim != 'pass'
GROUP BY rec.row.source_ip
ORDER BY cnt desc;
```
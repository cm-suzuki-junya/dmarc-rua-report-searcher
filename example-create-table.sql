CREATE EXTERNAL TABLE IF NOT EXISTS dmarc_report (
  feedback struct<
    report_metadata: struct<
      org_name: string,
      email: string,
      extra_contact_info: string,
      report_id: string,
      date_range: struct<
        begin: string,
        `end`: string
      >
    >,
    policy_published: struct<
      domain: string,
      adkim: string,
      aspf: string,
      p: string,
      sp: string,
      pct: string,
      np: string
    >,
    record: array<struct<
      `row`: struct<
        source_ip: string,
        `count`: string,
        policy_evaluated: struct<
          disposition: string,
          dkim: string,
          spf: string
        >
      >,
      identifiers: struct<
        header_from: string
      >,
      auth_results: struct<
        spf: struct<
          domain: string,
          result: string
        >,
        dkim: array<
          struct<
            domain: string,
            result: string,
            selector: string
          >
        >
      >>
    >
  >
 )
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
WITH SERDEPROPERTIES ('paths'='feedback')
LOCATION 's3://rua.example.com-mail-stocker/output/catcher';
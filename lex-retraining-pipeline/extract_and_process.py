import boto3
import pandas as pd
import argparse
import os

def extract_data(table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.scan()
    data = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response.get('Items', []))
    return data

def transform_for_lex(data):
    records = []
    for item in data:
        if item.get('isFallback'):
            records.append({
                'text': item['userInput'],
                'intent': 'FallbackIntent'
            })
    if not records:
        return None
    return pd.DataFrame(records)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table-name", type=str, required=True)
    parser.add_argument("--bucket-name", type=str, required=True)
    parser.add_argument("--output-key", type=str, required=True)
    args = parser.parse_args()

    print(f"Extracting data from DynamoDB: {args.table_name}")
    raw_data = extract_data(args.table_name)

    if not raw_data:
        print("No data found. Exiting.")
        # Create an empty file to satisfy SageMaker Processing Step output
        with open("/opt/ml/processing/output/utterances.csv", 'w') as f:
            pass
        return

    lex_df = transform_for_lex(raw_data)

    if lex_df is None or lex_df.empty:
        print("No fallback utterances to process. Exiting.")
        # Create an empty file to satisfy SageMaker Processing Step output
        with open("/opt/ml/processing/output/utterances.csv", 'w') as f:
            pass
        return

    output_path = "/opt/ml/processing/output/utterances.csv"
    # The header is required for the Lex import format
    lex_df.to_csv(output_path, index=False, header=["text", "intent"])

    # This part is for local verification, but in SageMaker the output is handled by ProcessingOutput
    # s3_client = boto3.client('s3')
    # s3_client.upload_file(output_path, args.bucket_name, args.output_key)
    print(f"Processed data written to {output_path}")

if __name__ == "__main__":
    main()
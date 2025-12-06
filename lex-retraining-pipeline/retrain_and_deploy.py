import boto3
import time
import argparse
import uuid
import os
import zipfile
import json

def create_lex_zip_archive(input_csv_path, output_zip_path, locale_id):
    """Creates a zip archive in the format required by the Lex V2 StartImport API."""

    # A minimal BotLocale.json is required at the root of the zip archive.
    # This manifest tells Lex how to interpret the contents.
    bot_locale_content = {
        "metadata": {
            "schemaVersion": "1.0",
            "importType": "LOCALE",
            "importStatus": "IN_PROGRESS"
        }
    }

    print(f"Creating ZIP archive at {output_zip_path}")
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. Write the BotLocale.json file to the root of the zip.
        zf.writestr('BotLocale.json', json.dumps(bot_locale_content, indent=4))

        # 2. Add the utterances CSV to the correct intent folder structure.
        # The required path inside the zip is IntentName/Utterances_LocaleID.csv
        archive_path = f'FallbackIntent/Utterances_{locale_id}.csv'
        zf.write(input_csv_path, archive_path)

    print(f"Successfully created Lex archive: {output_zip_path}")


def upload_to_s3(file_path, bucket, key):
    """Uploads a local file to S3."""
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_path, bucket, key)
    print(f"Successfully uploaded {file_path} to s3://{bucket}/{key}")
    return f"s3://{bucket}/{key}"

def start_lex_import(bot_id, bot_version, locale_id, s3_uri):
    """Starts a Lex bot locale import job."""
    lex_client = boto3.client('lexv2-models')
    import_id = str(uuid.uuid4())

    response = lex_client.start_import(
        importId=import_id,
        resourceSpecification={'botLocaleImportSpecification': {
            'botId': bot_id, 'botVersion': bot_version, 'localeId': locale_id
        }},
        mergeStrategy='Append',
        fileSource={'s3FileSource': {
            's3BucketName': s3_uri.split('/')[2],
            's3Key': '/'.join(s3_uri.split('/')[3:])
        }}
    )
    return response['importId']

def wait_for_import(import_id):
    """Waits for a Lex import job to complete."""
    lex_client = boto3.client('lexv2-models')
    while True:
        response = lex_client.describe_import(importId=import_id)
        status = response['importStatus']
        print(f"Import status: {status}")
        if status in ['Completed', 'Failed']:
            if status == 'Failed':
                failure_reasons = response.get('failureReasons', ['No reason provided.'])
                raise Exception(f"Lex import failed: {failure_reasons}")
            break
        time.sleep(30)

def build_bot_locale(bot_id, bot_version, locale_id):
    """Starts a build for the specified bot locale and waits for it to complete."""
    lex_client = boto3.client('lexv2-models')
    print("Starting bot build...")
    lex_client.build_bot_locale(botId=bot_id, botVersion=bot_version, localeId=locale_id)
    while True:
        response = lex_client.describe_bot_locale(
            botId=bot_id, botVersion=bot_version, localeId=locale_id
        )
        status = response['botLocaleStatus']
        print(f"Build status: {status}")
        if status in ['Built', 'ReadyExpressTesting', 'Failed']:
            if status == 'Failed':
                failure_reasons = response.get('failureReasons', ['No reason provided.'])
                raise Exception(f"Bot build failed with status: {status}. Reasons: {failure_reasons}")
            break
        time.sleep(30)
    print("Bot build completed successfully.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket-name", type=str, required=True)
    parser.add_argument("--bot-id", type=str, required=True)
    parser.add_argument("--bot-version", type=str, default="DRAFT")
    parser.add_argument("--locale-id", type=str, default="es_ES")
    args = parser.parse_args()

    input_csv_file = "/opt/ml/processing/input/utterances.csv"
    if not os.path.exists(input_csv_file) or os.path.getsize(input_csv_file) == 0:
        print("Input file is empty or does not exist. No new utterances to train. Skipping.")
        return

    # Create the zip archive in a local temporary directory
    zip_file_path = "/tmp/retraining_package.zip"
    create_lex_zip_archive(input_csv_file, zip_file_path, args.locale_id)

    # Upload the final zip archive to S3
    s3_key = f"conversation-logs/retraining-input-{uuid.uuid4()}.zip"
    s3_uri = upload_to_s3(zip_file_path, args.bucket_name, s3_key)

    print(f"Starting Lex import from {s3_uri}...")
    import_id = start_lex_import(args.bot_id, args.bot_version, args.locale_id, s3_uri)

    print(f"Waiting for import job {import_id} to complete...")
    wait_for_import(import_id)

    print("Import completed. Proceeding to build bot locale.")
    build_bot_locale(args.bot_id, args.bot_version, args.locale_id)

if __name__ == "__main__":
    main()

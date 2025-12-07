# src/backend/lex-retraining-pipeline/import.py

import argparse
import os
import boto3
import logging
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def start_lex_import(bot_id, bot_locale_id, aws_region, s3_uri):
    """
    Inicia un trabajo de importación en Amazon Lex V2 y espera su finalización.

    Args:
        bot_id (str): ID del bot de Amazon Lex.
        bot_locale_id (str): ID del locale del bot.
        aws_region (str): Región de AWS.
        s3_uri (str): URI de S3 del archivo ZIP a importar.
    """
    lex_client = boto3.client('lexv2-models', region_name=aws_region)

    s3_bucket, s3_key = s3_uri.replace('s3://', '').split('/', 1)

    try:
        logging.info(f"Iniciando importación para el bot {bot_id} ({bot_locale_id}) desde {s3_uri}")

        response = lex_client.start_import(
            payloadS3Location={
                's3BucketName': s3_bucket,
                's3ObjectKey': s3_key
            },
            resourceSpecification={
                'botLocaleSpecification': {
                    'botId': bot_id,
                    'botVersion': 'DRAFT', # Siempre importamos a la versión borrador
                    'localeId': bot_locale_id
                }
            },
            mergeStrategy='Append' # 'Append' añade las nuevas utterances sin sobreescribir las existentes
        )

        import_id = response['importId']
        logging.info(f"Importación iniciada con ID: {import_id}")

        # Esperar a que la importación se complete
        while True:
            import_status = lex_client.describe_import(importId=import_id)
            status = import_status['importStatus']
            logging.info(f"Estado actual de la importación: {status}")

            if status == 'Completed':
                logging.info("Importación completada exitosamente.")
                break
            elif status == 'Failed':
                logging.error(f"La importación falló. Razones: {import_status.get('failureReasons', 'No se proporcionaron razones.')}")
                raise Exception("Fallo en la importación de Lex.")

            time.sleep(15) # Esperar 15 segundos antes de volver a consultar

    except Exception as e:
        logging.error(f"Ocurrió un error durante la importación a Lex: {e}")
        raise

def main():
    """
    Función principal para ejecutar el script de importación.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--bot-id', type=str, required=True, help='ID del bot de Amazon Lex.')
    parser.add_argument('--bot-locale-id', type=str, required=True, help='ID del locale del bot.')
    parser.add_argument('--aws-region', type=str, required=True, help='Región de AWS.')
    parser.add_argument('--input-path', type=str, required=True, help='Ruta al directorio de entrada que contiene el ZIP.')
    args = parser.parse_args()

    # El URI de S3 se pasa implícitamente a través del entorno de SageMaker.
    # El archivo lex-import.zip está en el directorio de entrada.
    zip_s3_uri = os.path.join(args.input_path, 'lex-import.zip')

    start_lex_import(args.bot_id, args.bot_locale_id, args.aws_region, zip_s3_uri)

if __name__ == '__main__':
    main()

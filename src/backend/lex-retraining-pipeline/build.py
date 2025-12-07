# src/backend/lex-retraining-pipeline/build.py

import argparse
import os
import json
import zipfile
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_lex_import_zip(input_csv_path, output_zip_path, bot_locale_id):
    """
    Crea un archivo ZIP en el formato requerido por Amazon Lex V2 para la importación.

    Args:
        input_csv_path (str): Ruta al archivo CSV con las utterances preprocesadas.
        output_zip_path (str): Ruta donde se guardará el archivo ZIP de salida.
        bot_locale_id (str): El ID del locale del bot (ej. 'es_ES').
    """

    intent_name = 'FallbackIntent'

    # Crear el manifiesto BotLocale.json
    manifest = {
        "metadata": {
            "schemaVersion": "1.0",
            "importType": "UTTERANCE",
            "importStatus": "IN_PROGRESS"
        },
        "name": intent_name,
        "identifier": "FALLBACK",
        "locale": bot_locale_id,
        "voiceName": None
    }

    manifest_filename = 'BotLocale.json'
    with open(manifest_filename, 'w') as f:
        json.dump(manifest, f, indent=4)

    # Crear el archivo ZIP
    logging.info(f"Creando archivo ZIP en: {output_zip_path}")
    with zipfile.ZipFile(output_zip_path, 'w') as zipf:
        # Añadir el manifiesto en la raíz del ZIP
        zipf.write(manifest_filename, arcname=manifest_filename)

        # Añadir el archivo de utterances dentro de un directorio con el nombre del intent
        utterances_arcname = os.path.join(intent_name, os.path.basename(input_csv_path))
        zipf.write(input_csv_path, arcname=utterances_arcname)
        logging.info(f"Añadiendo {input_csv_path} como {utterances_arcname} al ZIP.")

    # Limpiar el archivo de manifiesto local
    os.remove(manifest_filename)
    logging.info("Archivo ZIP creado exitosamente.")

def main():
    """
    Función principal para empaquetar las utterances para la importación en Lex.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path', type=str, required=True, help='Ruta al directorio de datos de entrada (preprocesados).')
    parser.add_argument('--output-path', type=str, required=True, help='Ruta al directorio de salida para el archivo ZIP.')
    parser.add_argument('--bot-locale-id', type=str, required=True, help='El ID del locale del bot (ej. es_ES).')
    args = parser.parse_args()

    input_file = os.path.join(args.input_path, 'preprocessed_utterances.csv')
    output_zip = os.path.join(args.output_path, 'lex-import.zip')

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"No se encontró el archivo de entrada esperado: {input_file}")

    create_lex_import_zip(input_file, output_zip, args.bot_locale_id)

if __name__ == '__main__':
    main()

# src/backend/lex-retraining-pipeline/preprocess.py

import argparse
import os
import pandas as pd
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Función principal para el preprocesamiento de utterances.

    Lee un archivo CSV desde una ruta de entrada, elimina filas vacías y guarda
    el resultado en una ruta de salida. Este script está diseñado para ser
    ejecutado como un paso en un pipeline de SageMaker Processing.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path', type=str, required=True, help='Ruta al directorio de datos de entrada en el contenedor.')
    parser.add_argument('--output-path', type=str, required=True, help='Ruta al directorio de datos de salida en el contenedor.')
    args = parser.parse_args()

    logging.info(f"Listando archivos en el directorio de entrada: {args.input_path}")
    input_files = os.listdir(args.input_path)
    if not input_files:
        raise FileNotFoundError(f"No se encontraron archivos en el directorio de entrada: {args.input_path}")

    # Suponemos que solo hay un archivo CSV en el directorio de entrada
    input_file_path = os.path.join(args.input_path, input_files[0])
    logging.info(f"Procesando archivo de entrada: {input_file_path}")

    try:
        # Leer el CSV. Asumimos que no tiene encabezado y las utterances están en la primera columna.
        df = pd.read_csv(input_file_path, header=None, names=['utterance'])

        # Eliminar filas donde la utterance esté vacía o sea solo espacios en blanco
        df.dropna(subset=['utterance'], inplace=True)
        df = df[df['utterance'].str.strip() != '']

        # Guardar el resultado
        output_file_path = os.path.join(args.output_path, 'preprocessed_utterances.csv')
        logging.info(f"Guardando archivo preprocesado en: {output_file_path}")
        df.to_csv(output_file_path, index=False, header=False)

        logging.info("Preprocesamiento completado exitosamente.")

    except Exception as e:
        logging.error(f"Error durante el preprocesamiento: {e}")
        raise

if __name__ == '__main__':
    main()

# src/backend/lex-retraining-pipeline/pipeline.py

import sagemaker
from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
from sagemaker.workflow.steps import ProcessingStep
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.parameters import ParameterString
import boto3
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_pipeline(
    sagemaker_role_arn,
    input_data_uri,
    output_data_uri,
    bot_id,
    bot_locale_id,
    aws_region
):
    """
    Define y crea un pipeline de SageMaker para el reentrenamiento de un bot de Lex.

    Args:
        sagemaker_role_arn (str): ARN del rol de IAM para la ejecución de SageMaker.
        input_data_uri (str): URI de S3 del archivo CSV de entrada.
        output_data_uri (str): URI de S3 para los artefactos de salida.
        bot_id (str): ID del bot de Amazon Lex V2.
        bot_locale_id (str): ID del locale del bot (ej. 'es_ES').
        aws_region (str): Región de AWS.

    Returns:
        sagemaker.workflow.pipeline.Pipeline: El objeto de pipeline de SageMaker.
    """

    # 1. Definir el procesador de scripts (usaremos la misma imagen para todos los pasos)
    script_processor = ScriptProcessor(
        image_uri=sagemaker.image_uris.retrieve('sagemaker-scikit-learn', aws_region, '0.23-1'),
        command=['python3'],
        instance_count=1,
        instance_type='ml.t3.medium',
        role=sagemaker_role_arn
    )

    # 2. Definir el paso de preprocesamiento
    preprocess_step = ProcessingStep(
        name='PreprocessUtterances',
        processor=script_processor,
        inputs=[ProcessingInput(source=input_data_uri, destination='/opt/ml/processing/input')],
        outputs=[ProcessingOutput(output_name='preprocessed_data', source='/opt/ml/processing/output')],
        code='preprocess.py',
        job_arguments=[
            '--input-path', '/opt/ml/processing/input',
            '--output-path', '/opt/ml/processing/output'
        ]
    )

    # 3. Definir el paso de empaquetado (build)
    build_step = ProcessingStep(
        name='BuildLexImportPackage',
        processor=script_processor,
        inputs=[ProcessingInput(source=preprocess_step.properties.Outputs['preprocessed_data'].S3Output.S3Uri, destination='/opt/ml/processing/input')],
        outputs=[ProcessingOutput(output_name='lex_zip_package', source='/opt/ml/processing/output')],
        code='build.py',
        job_arguments=[
            '--input-path', '/opt/ml/processing/input',
            '--output-path', '/opt/ml/processing/output',
            '--bot-locale-id', bot_locale_id
        ]
    )

    # 4. Definir el paso de importación a Lex
    import_step = ProcessingStep(
        name='ImportToLex',
        processor=script_processor,
        inputs=[ProcessingInput(source=build_step.properties.Outputs['lex_zip_package'].S3Output.S3Uri, destination='/opt/ml/processing/input')],
        code='import.py',
        job_arguments=[
            '--bot-id', bot_id,
            '--bot-locale-id', bot_locale_id,
            '--aws-region', aws_region,
            '--input-path', '/opt/ml/processing/input'
        ]
    )

    # 5. Crear el pipeline con los tres pasos
    pipeline = Pipeline(
        name='LexRetrainingPipeline',
        parameters=[
            ParameterString(name="InputDataUrl", default_value=input_data_uri),
            ParameterString(name="BotId", default_value=bot_id),
            ParameterString(name="BotLocaleId", default_value=bot_locale_id),
        ],
        steps=[preprocess_step, build_step, import_step]
    )

    return pipeline

if __name__ == '__main__':
    # --- CONFIGURACIÓN: Reemplaza estos valores ---
    # El ARN del rol de ejecución de IAM que creaste.
    SAGEMAKER_ROLE_ARN = 'arn:aws:iam::<ACCOUNT_ID>:role/tu-sagemaker-execution-role'

    # El bucket S3 y la ruta al archivo de utterances.
    INPUT_DATA_URI = 's3://mi-bucket-de-datos-aqui/utterances/nuevas_utterances.csv'

    # El bucket S3 donde se guardarán los resultados (ya no es necesario un output_data_uri global).

    # ID de tu bot de Lex V2.
    BOT_ID = 'MI_BOT_ID_AQUI'

    # Locale del bot que quieres reentrenar (ej. 'es_ES').
    BOT_LOCALE_ID = 'es_ES'

    # Región de AWS.
    AWS_REGION = 'us-east-1'
    # ----------------------------------------------

    logging.info("Creando la definición del pipeline...")

    lex_pipeline = create_pipeline(
        sagemaker_role_arn=SAGEMAKER_ROLE_ARN,
        input_data_uri=INPUT_DATA_URI,
        output_data_uri=None, # Ya no es necesario
        bot_id=BOT_ID,
        bot_locale_id=BOT_LOCALE_ID,
        aws_region=AWS_REGION
    )

    logging.info("Definición del pipeline creada. Enviando a SageMaker...")

    # Crear o actualizar el pipeline en SageMaker
    lex_pipeline.upsert(role_arn=SAGEMAKER_ROLE_ARN)

    logging.info(f"Pipeline '{lex_pipeline.name}' guardado en SageMaker. "
                 "Puedes ir a la consola de SageMaker Studio para ejecutarlo.")

    # Opcional: Ejecutar el pipeline inmediatamente
    # execution = lex_pipeline.start()
    # logging.info(f"Pipeline iniciado con la ejecución ARN: {execution.arn}")
    # execution.describe()

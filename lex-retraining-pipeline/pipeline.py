import sagemaker
from sagemaker.processing import ProcessingInput, ProcessingOutput, ScriptProcessor
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep
import boto3

# --- VALORES CONFIGURADOS ---
AWS_REGION = "us-east-1"
AWS_ACCOUNT_ID = "655765967000"
LEX_BOT_ID = "JSLE3RWGRY"
SAGEMAKER_ROLE_ARN = "arn:aws:iam::655765967000:role/CafeteriaBotSageMakerPipelineRole"

DYNAMODB_TABLE_NAME = "cafeteria-chat-interactions"
S3_BUCKET_NAME = "mi-cafeteria-chatbot-assets" # El nombre de tu bucket
LEX_LOCALE_ID = "es_ES"

# --- Inicialización ---
boto_session = boto3.Session(region_name=AWS_REGION)
sagemaker_session = sagemaker.Session(boto_session=boto_session)

# --- Definición de Pasos del Pipeline ---
# (Usa una imagen de contenedor de ECR de la misma región que tu SageMaker Studio)
framework_version = "1.8"
py_version = "py3"
instance_type = "ml.t3.medium"
# Use a scikit-learn image for general python processing
image_uri = sagemaker.image_uris.retrieve(
    framework="sklearn",
    region=AWS_REGION,
    version="0.23-1",
    py_version="py3",
    instance_type=instance_type
)

# Paso 1: Extraer y Procesar Datos
extract_processor = ScriptProcessor(
    image_uri=image_uri,
    command=['python3'],
    instance_type=instance_type,
    instance_count=1,
    base_job_name='lex-extract-data',
    role=SAGEMAKER_ROLE_ARN,
    sagemaker_session=sagemaker_session,
)
step_extract = ProcessingStep(
    name='ExtractAndProcessData',
    processor=extract_processor,
    outputs=[ProcessingOutput(output_name='utterances', source='/opt/ml/processing/output')],
    code='extract_and_process.py',
    job_arguments=[
        "--table-name", DYNAMODB_TABLE_NAME,
        "--bucket-name", S3_BUCKET_NAME,
        "--output-key", "conversation-logs/processed/latest_utterances.csv"
    ]
)

# Paso 2: Reentrenar y Desplegar el Bot
retrain_processor = ScriptProcessor(
    image_uri=image_uri,
    command=['python3'],
    instance_type=instance_type,
    instance_count=1,
    base_job_name='lex-retrain-deploy',
    role=SAGEMAKER_ROLE_ARN,
    sagemaker_session=sagemaker_session,
)
step_retrain = ProcessingStep(
    name='RetrainAndDeployLexBot',
    processor=retrain_processor,
    inputs=[ProcessingInput(source=step_extract.properties.ProcessingOutputConfig.Outputs['utterances'].S3Output.S3Uri, destination='/opt/ml/processing/input')],
    code='retrain_and_deploy.py',
    job_arguments=[
        "--bucket-name", S3_BUCKET_NAME,
        "--bot-id", LEX_BOT_ID,
        "--locale-id", LEX_LOCALE_ID
    ]
)

# --- Definición del Pipeline ---
pipeline = Pipeline(
    name='LexBotRetrainingPipeline',
    steps=[step_extract, step_retrain],
    sagemaker_session=sagemaker_session,
)

if __name__ == "__main__":
    print("Validando y guardando la definición del pipeline...")
    pipeline.upsert(role_arn=SAGEMAKER_ROLE_ARN)
    print("Definición guardada. Ahora puedes ejecutarlo desde SageMaker Studio o la CLI.")

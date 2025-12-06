# Procedimiento Detallado para Crear un Chatbot de Cafetería en AWS

Este documento proporciona una guía paso a paso para crear un chatbot multilingüe para una cafetería utilizando servicios gestionados de AWS, incluyendo una canalización de MLOps para el reentrenamiento continuo.

## Arquitectura de la Solución

*   **NLU (Natural Language Understanding):** Amazon Lex V2
*   **Lógica de Negocio y Orquestación:** AWS Lambda
*   **Detección de Idioma:** Amazon Comprehend
*   **Traducción:** Amazon Translate
*   **Respuestas LLM (RAG y Fallback):** Amazon Bedrock
*   **Almacenamiento de Logs:** Amazon DynamoDB
*   **Almacenamiento de Documentos (Base de Conocimiento):** Amazon S3
*   **Notificaciones (Pedidos):** Amazon SES
*   **Pipeline de Reentrenamiento (MLOps):** SageMaker Pipelines

---

## Parte 1: Configuración de la Base (Almacenamiento)

### A. Crear Tabla en DynamoDB para Logs

1.  **Servicio:** Amazon DynamoDB
2.  **Acción:** Clic en "Crear tabla".
3.  **Nombre de la tabla:** `cafeteria-chat-interactions`
4.  **Clave de partición:** `conversationId` (Tipo: String)
5.  **Clave de ordenación:** `timestamp` (Tipo: String)
6.  **Confirmación:** Clic en "Crear tabla".

### B. Crear Bucket en S3 para Activos

1.  **Servicio:** Amazon S3
2.  **Acción:** Clic en "Crear bucket".
3.  **Nombre del bucket:** `mi-cafeteria-chatbot-assets` (debe ser único globalmente, anota el nombre).
4.  **Configuración:** Mantener "Bloquear todo el acceso público" activado.
5.  **Control de Versiones del bucket:** Habilitar.
6.  **Crear Carpetas Internas:** Una vez creado, entrar al bucket y crear dos carpetas: `knowledge-base` y `conversation-logs`.

---

## Parte 2: Creación del Cerebro del Chatbot (Amazon Lex)

### A. Creación del Bot

1.  **Servicio:** Amazon Lex (consola V2)
2.  **Acción:** Clic en "Crear bot" > "Crear un bot en blanco".
3.  **Nombre del bot:** `CafeteriaBot`
4.  **Permisos de IAM:** Seleccionar "Crear un rol con permisos básicos de Amazon Lex".
5.  **Anóta el ID del Bot:** Una vez creado, en la página de detalles del bot, copia y guarda el **ID del Bot (Bot ID)**. Lo necesitarás para el pipeline de SageMaker.

### B. Configuración de Idiomas

1.  En el menú de la izquierda, ve a "Idiomas y configuración regional".
2.  Añade los siguientes idiomas: `Spanish (ES)`, `English (US)`, `Portuguese (BR)`.

### C. Creación de Intenciones (Intents)

Repite el siguiente proceso para cada una de las intenciones listadas abajo.

**Guía Detallada: Cómo Crear una Intención**

1.  Asegúrate de estar en el idioma `Spanish (ES)`.
2.  En el menú de la izquierda, haz clic en **"Intenciones" (Intents)**.
3.  Haz clic en **"Añadir intención" > "Añadir intención en blanco"**.
4.  Asigna el **Nombre de la intención** (ej. `Saludo`).
5.  En la sección **"Frases de ejemplo"**, añade las frases correspondientes.
6.  Haz clic en **"Guardar intención"**.

**Lista de Intenciones a Crear:**

*   **`Saludo`**:
    *   **Frases de ejemplo:** "Hola", "Buenos días", "Qué tal", "Buenas".
*   **`PedirMenu`**:
    *   **Frases de ejemplo:** "Quiero ver el menú", "Qué tienes para comer", "Me muestras la carta".
*   **`PreguntarHorarios`**:
    *   **Frases de ejemplo:** "A qué hora abren", "Cuál es su horario", "Están abiertos ahora?".
*   **`HacerPedido`**:
    *   **Frases de ejemplo:** "Quiero hacer un pedido", "Me gustaría ordenar algo", "Para llevar por favor".
    *   **Configuración Adicional (Slots):** En la sección "Slots", crea un slot llamado `pedidoDetalle` de tipo `AMAZON.FreeFormInput` y asígnale el prompt: "Claro, ¿qué te gustaría pedir?".
*   **`PreguntaAbierta`**:
    *   **Frases de ejemplo:** "De dónde traen el café", "Hay estacionamiento cerca", "Tienen opciones sin gluten".
*   **Configuración del `FallbackIntent` (Intención de Respaldo):**
    *   No crees una intención llamada "Fallback". En su lugar, utiliza la intención integrada.
    *   En el listado de intenciones, haz clic en **`FallbackIntent`**.
    *   Activa la opción para **"Cumplimiento" (Fulfillment)** y configúrala para que llame a la función Lambda. Esto asegura que cualquier cosa que Lex no entienda se envíe a nuestra lógica de RAG.

**Importante:** Después de crear las intenciones en español, cambia al idioma `English (US)` y `Portuguese (BR)` y añade las frases de ejemplo traducidas para cada intención.

### D. Construir y Probar

1.  Haz clic en el botón **"Generar" (Build)**.
2.  Una vez completado, usa la ventana de **"Probar"** para verificar que las intenciones se reconocen.

---

## Parte 3: Lógica Central (AWS Lambda)

### A. Política y Rol de IAM para Lambda

1.  **Servicio:** IAM > Políticas > "Crear política".
2.  **Pestaña JSON:** Pega el siguiente código (reemplazando `REGION`, `ACCOUNT_ID`, el nombre de tu bucket y tu email verificado en SES).

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CloudWatchLogs",
                "Effect": "Allow",
                "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": "arn:aws:logs:REGION:ACCOUNT_ID:log-group:/aws/lambda/cafeteriaBotOrchestrator:*"
            },
            {
                "Sid": "ComprehendTranslate",
                "Effect": "Allow",
                "Action": ["comprehend:DetectDominantLanguage", "translate:TranslateText"],
                "Resource": "*"
            },
            {
                "Sid": "DynamoDBWrite",
                "Effect": "Allow",
                "Action": "dynamodb:PutItem",
                "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/cafeteria-chat-interactions"
            },
            {
                "Sid": "S3ReadKnowledgeBase",
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::mi-cafeteria-chatbot-assets/knowledge-base/*"
            },
            {
                "Sid": "SESSendEmail",
                "Effect": "Allow",
                "Action": "ses:SendEmail",
                "Resource": "*",
                "Condition": { "StringEquals": { "ses:FromAddress": "tu-email-verificado@dominio.com" } }
            },
            {
                "Sid": "BedrockInvokeModel",
                "Effect": "Allow",
                "Action": "bedrock:InvokeModel",
                "Resource": "arn:aws:bedrock:REGION::foundation-model/anthropic.claude-v2"
            }
        ]
    }
    ```
3.  **Nombre de la política:** `CafeteriaBotLambdaPolicy`.
4.  **Crear Rol:** Ir a IAM > Roles > "Crear rol".
5.  **Caso de Uso:** Lambda.
6.  **Adjuntar Política:** Busca y selecciona `CafeteriaBotLambdaPolicy`.
7.  **Nombre del Rol:** `CafeteriaBotLambdaRole`.

### B. Crear Función Lambda

1.  **Servicio:** AWS Lambda > "Crear función".
2.  **Nombre:** `cafeteriaBotOrchestrator`
3.  **Runtime:** Python 3.11
4.  **Rol:** Seleccionar el rol `CafeteriaBotLambdaRole` que acabas de crear.
5.  **Configuración Avanzada:**
    *   **General > Tiempo de espera:** `30 segundos`.
    *   **Variables de entorno:**
        *   `DYNAMODB_TABLE`: `cafeteria-chat-interactions`
        *   `S3_BUCKET`: `mi-cafeteria-chatbot-assets`
        *   `S3_KNOWLEDGE_KEY`: `knowledge-base/menu.txt`
        *   `SES_EMAIL_FROM`: Tu email verificado en SES.
        *   `SES_EMAIL_TO`: Email de destino para pedidos.

### C. Código de la Función Lambda

En la pestaña **"Código"** de tu función Lambda, pega el siguiente script completo:

```python
import json
import boto3
import os
import uuid
from datetime import datetime

# --- AWS Service Clients ---
comprehend = boto3.client('comprehend')
translate = boto3.client('translate')
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')
ses = boto3.client('ses')
s3 = boto3.client('s3')

# --- Environment Variables ---
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'cafeteria-chat-interactions')
S3_BUCKET = os.environ.get('S3_BUCKET', 'mi-cafeteria-chatbot-assets')
S3_KNOWLEDGE_KEY = os.environ.get('S3_KNOWLEDGE_KEY', 'knowledge-base/menu.txt')
SES_EMAIL_FROM = os.environ.get('SES_EMAIL_FROM')
SES_EMAIL_TO = os.environ.get('SES_EMAIL_TO')

# --- Constants ---
TARGET_LANGUAGES = ['es', 'en', 'pt']
BEDROCK_MODEL_ID = 'anthropic.claude-v2'

def log_interaction(session_id, user_text, detected_lang, intent, slots, bot_response):
    """Logs the full conversation turn to DynamoDB."""
    table = dynamodb.Table(DYNAMODB_TABLE)
    timestamp = datetime.utcnow().isoformat()

    try:
        table.put_item(
            Item={
                'conversationId': session_id,
                'timestamp': timestamp,
                'userInput': user_text,
                'detectedLanguage': detected_lang,
                'intent': intent,
                'slots': json.dumps(slots) if slots else '{}',
                'botResponse': bot_response,
                'isFallback': (intent == 'FallbackIntent' or intent == 'PreguntaAbierta')
            }
        )
    except Exception as e:
        print(f"ERROR logging to DynamoDB: {e}")


def detect_language(text):
    """Detects the dominant language of the user's input."""
    try:
        response = comprehend.detect_dominant_language(Text=text)
        lang_code = response['Languages'][0]['LanguageCode']
        return lang_code
    except Exception as e:
        print(f"ERROR detecting language: {e}")
        return 'en' # Default to English on error

def translate_text(text, source_lang, target_lang='en'):
    """Translates text if the source language is not the target."""
    if source_lang == target_lang:
        return text
    try:
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        return response['TranslatedText']
    except Exception as e:
        print(f"ERROR translating text: {e}")
        return text # Return original text on error

def get_rag_response(query):
    """Retrieves context from S3 and generates a response using Bedrock (RAG)."""
    try:
        # 1. Retrieve knowledge base from S3
        s3_object = s3.get_object(Bucket=S3_BUCKET, Key=S3_KNOWLEDGE_KEY)
        knowledge_base = s3_object['Body'].read().decode('utf-8')

        # 2. Construct the prompt for Bedrock
        prompt = f"""\n\nHuman: Eres un asistente de cafetería. Usando ÚNICAMENTE la siguiente información, responde la pregunta del usuario. Si la respuesta no está en la información, di amablemente que no tienes esa información.

<informacion>
{knowledge_base}
</informacion>

Pregunta del usuario: "{query}"

Assistant:"""

        # 3. Invoke Bedrock model
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 500,
            "temperature": 0.1,
            "top_p": 0.9,
        })

        response = bedrock_runtime.invoke_model(
            body=body,
            modelId=BEDROCK_MODEL_ID
        )

        response_body = json.loads(response.get('body').read())
        return response_body.get('completion').strip()

    except Exception as e:
        print(f"ERROR in RAG response: {e}")
        return "Lo siento, no pude procesar tu pregunta en este momento. Inténtalo de nuevo."

def handle_order(session_id, order_details):
    """Handles the 'HacerPedido' intent by sending an email."""
    if not SES_EMAIL_FROM or not SES_EMAIL_TO:
        print("ERROR: SES environment variables not set.")
        return "No puedo procesar pedidos en este momento debido a un problema de configuración."

    subject = f"Nuevo Pedido Recibido - ID: {session_id}"
    body = f"Se ha recibido un nuevo pedido con los siguientes detalles:\n\n{order_details}"

    try:
        ses.send_email(
            Source=SES_EMAIL_FROM,
            Destination={'ToAddresses': [SES_EMAIL_TO]},
            Message={'Subject': {'Data': subject}, 'Body': {'Text': {'Data': body}}}
        )
        return "¡Tu pedido ha sido recibido! Lo estaremos preparando."
    except Exception as e:
        print(f"ERROR sending email with SES: {e}")
        return "Hubo un problema al enviar tu pedido. Por favor, inténtalo más tarde."


def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))

    session_id = event.get('sessionId', str(uuid.uuid4()))
    user_text = event.get('inputTranscript', '')

    detected_lang = detect_language(user_text)

    intent_name = event['interpretations'][0]['intent']['name']
    slots = event['interpretations'][0]['intent'].get('slots', {})

    bot_response = ""

    # --- Intent Routing ---
    if intent_name == 'HacerPedido':
        order_details = slots.get('pedidoDetalle', {}).get('value', {}).get('interpretedValue')
        if order_details:
            bot_response = handle_order(session_id, order_details)
        else:
            # This case should be handled by Lex prompting for the slot
            bot_response = "No entendí los detalles de tu pedido. ¿Podrías repetirlo?"

    elif intent_name in ['PreguntaAbierta', 'FallbackIntent']:
        bot_response = get_rag_response(user_text)

    else:
        # This part assumes a response is configured in the Lex console.
        messages = event.get('messages', [{'contentType': 'PlainText', 'content': 'Respuesta no configurada.'}])
        bot_response = messages[0]['content']

    # Translate the final response back to the user's language
    final_response_text = translate_text(bot_response, 'en', detected_lang)

    log_interaction(session_id, user_text, detected_lang, intent_name, slots, final_response_text)

    # --- Construct Final Response for Lex ---
    response = {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": intent_name,
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": final_response_text
            }
        ]
    }

    return response
```

### D. Conectar y Desplegar

1.  Haz clic en el botón **"Deploy"** en la Lambda.
2.  Vuelve a la consola de **Lex > Implementación > Alias**. Haz clic en `TestBotAlias`.
3.  Para cada idioma (`Spanish (ES)`, `English (US)`, `Portuguese (BR)`), haz clic en el idioma y asocia la función Lambda `cafeteriaBotOrchestrator`. Guarda la configuración del alias.
4.  Haz clic en **"Generar" (Build)** en el bot una vez más para aplicar todos los cambios.

---

## Parte 4: Pipeline de Reentrenamiento (SageMaker)

### A. Rol de IAM para SageMaker

1.  Crea una política en IAM llamada `CafeteriaBotSageMakerPipelinePolicy`.
2.  En la pestaña JSON, pega el siguiente código, reemplazando `REGION`, `ACCOUNT_ID`, y el `YOUR_BOT_ID` que anotaste previamente.

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DynamoDBRead",
                "Effect": "Allow",
                "Action": [ "dynamodb:Scan", "dynamodb:Query" ],
                "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/cafeteria-chat-interactions"
            },
            {
                "Sid": "S3BucketAccess",
                "Effect": "Allow",
                "Action": [ "s3:PutObject", "s3:GetObject", "s3:ListBucket" ],
                "Resource": [
                    "arn:aws:s3:::mi-cafeteria-chatbot-assets",
                    "arn:aws:s3:::mi-cafeteria-chatbot-assets/*"
                ]
            },
            {
                "Sid": "LexModelBuilding",
                "Effect": "Allow",
                "Action": [
                    "lex:StartImport", "lex:DescribeImport", "lex:CreateBotLocale",
                    "lex:DescribeBotLocale", "lex:BuildBotLocale", "lex:UpdateBotLocale"
                ],
                "Resource": "arn:aws:lex:REGION:ACCOUNT_ID:bot/YOUR_BOT_ID"
            },
            {
                "Sid": "IAMPassRoleForLex",
                "Effect": "Allow",
                "Action": "iam:PassRole",
                "Resource": "arn:aws:iam::ACCOUNT_ID:role/aws-service-role/lexv2.amazonaws.com/AWSServiceRoleForLexV2Bots*",
                "Condition": { "StringEquals": { "iam:PassedToService": "lexv2.amazonaws.com" } }
            }
        ]
    }
    ```
3.  Crea un rol para el caso de uso **SageMaker** llamado `CafeteriaBotSageMakerPipelineRole` y adjúntale la política recién creada.

### B. Creación de Scripts en SageMaker Studio

1.  Abre SageMaker Studio.
2.  Usando el explorador de archivos, crea una nueva carpeta `lex-retraining-pipeline`.
3.  Dentro de esa carpeta, crea los siguientes tres archivos de Python y pega el contenido correspondiente en cada uno.

#### 1. `extract_and_process.py`
```python
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
        open("/opt/ml/processing/output/utterances.csv", 'w').close()
        return

    lex_df = transform_for_lex(raw_data)

    if lex_df is None or lex_df.empty:
        print("No fallback utterances to process. Exiting.")
        open("/opt/ml/processing/output/utterances.csv", 'w').close()
        return

    output_path = "/opt/ml/processing/output/utterances.csv"
    lex_df.to_csv(output_path, index=False, header=False)

    s3_client = boto3.client('s3')
    s3_client.upload_file(output_path, args.bucket_name, args.output_key)
    print(f"Processed data uploaded to s3://{args.bucket_name}/{args.output_key}")

if __name__ == "__main__":
    main()
```

#### 2. `retrain_and_deploy.py`
```python
import boto3
import time
import argparse
import uuid
import os

def upload_to_s3(file_path, bucket, key):
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_path, bucket, key)
    return f"s3://{bucket}/{key}"

def start_lex_import(bot_id, bot_version, locale_id, s3_uri):
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
    lex_client = boto3.client('lexv2-models')
    while True:
        response = lex_client.describe_import(importId=import_id)
        status = response['importStatus']
        print(f"Import status: {status}")
        if status in ['Completed', 'Failed']:
            if status == 'Failed':
                raise Exception(f"Lex import failed: {response.get('failureReasons')}")
            break
        time.sleep(30)

def build_bot_locale(bot_id, bot_version, locale_id):
    lex_client = boto3.client('lexv2-models')
    print("Starting bot build...")
    lex_client.build_bot_locale(botId=bot_id, botVersion=bot_version, localeId=locale_id)
    while True:
        response = lex_client.describe_bot_locale(
            botId=bot_id, botVersion=bot_version, localeId=locale_id
        )
        status = response['botLocaleStatus']
        print(f"Build status: {status}")
        if status in ['Built', 'Failed']:
            if status != 'Built':
                raise Exception(f"Bot build failed with status: {status}")
            break
        time.sleep(30)
    print("Bot build completed.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket-name", type=str, required=True)
    parser.add_argument("--bot-id", type=str, required=True)
    parser.add_argument("--bot-version", type=str, default="DRAFT")
    parser.add_argument("--locale-id", type=str, default="es_ES")
    args = parser.parse_args()

    input_file = "/opt/ml/processing/input/utterances.csv"
    if os.path.getsize(input_file) == 0:
        print("No new utterances to train. Skipping.")
        return

    s3_key = f"conversation-logs/retraining-input-{uuid.uuid4()}.csv"
    s3_uri = upload_to_s3(input_file, args.bucket_name, s3_key)

    print("Starting Lex import...")
    import_id = start_lex_import(args.bot_id, args.bot_version, args.locale_id, s3_uri)

    wait_for_import(import_id)

    build_bot_locale(args.bot_id, args.bot_version, args.locale_id)

if __name__ == "__main__":
    main()
```

#### 3. `pipeline.py`
```python
import sagemaker
from sagemaker.processing import ProcessingInput, ProcessingOutput, ScriptProcessor
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep
import boto3

# --- ¡¡¡IMPORTANTE!!! ---
# --- Reemplaza estos valores con los tuyos ---
AWS_REGION = "us-east-1" # La región donde están tus recursos
AWS_ACCOUNT_ID = "TÚ_ACCOUNT_ID_DE_AWS"
SAGEMAKER_ROLE_ARN = f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/CafeteriaBotSageMakerPipelineRole"

DYNAMODB_TABLE_NAME = "cafeteria-chat-interactions"
S3_BUCKET_NAME = "mi-cafeteria-chatbot-assets" # El nombre de tu bucket

LEX_BOT_ID = "TÚ_BOT_ID_DE_LEX" # El ID que guardaste en la Parte 2
LEX_LOCALE_ID = "es_ES"

# --- Inicialización ---
sagemaker_session = sagemaker.Session()

# --- Definición de Pasos del Pipeline ---
# (Usa una imagen de contenedor de ECR de la misma región que tu SageMaker Studio)
framework_version = "1.8"
py_version = "py3"
instance_type = "ml.t3.medium"
image_uri = sagemaker.image_uris.retrieve(
    framework="pytorch",
    region=AWS_REGION,
    version=framework_version,
    py_version=py_version,
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
```

### C. Ejecución del Pipeline

1.  Actualiza los placeholders (`AWS_ACCOUNT_ID`, `TÚ_BOT_ID_DE_LEX`, etc.) en el archivo `pipeline.py`.
2.  Abre un terminal dentro de SageMaker Studio (`File > New > Terminal`).
3.  Navega a tu carpeta: `cd lex-retraining-pipeline`
4.  Ejecuta el script: `python pipeline.py`
5.  Esto registrará el pipeline en SageMaker. Podrás verlo y ejecutarlo desde la consola de AWS: **SageMaker > Canalizaciones (Pipelines)**.
6.  (Opcional) Automatiza la ejecución con una regla de **Amazon EventBridge** (ej. una vez a la semana).

---

## Parte 5: Consideraciones Finales

### A. Limitaciones

*   **Calidad del NLU:** El NLU de Lex mejora con más frases de ejemplo nativas. El reentrenamiento automático ayuda, pero una curación manual periódica es recomendable.
*   **Cold Starts:** La primera llamada a Lambda puede ser más lenta. Usar "Provisioned Concurrency" para producción.
*   **Calidad de RAG:** La efectividad de Bedrock depende de la calidad y estructura de los documentos en S3.

### B. Costos Relativos (Mayor a Menor)

1.  **SageMaker:** Costo por tiempo de uso de instancias de Studio y jobs de procesamiento.
2.  **Amazon Bedrock:** Costo por tokens de entrada/salida.
3.  **AWS Lambda:** Generalmente económico, con un generoso nivel gratuito.
4.  **Lex, Comprehend, Translate:** Costo por número de solicitudes.
5.  **DynamoDB, S3:** Costos de almacenamiento y operaciones, usualmente bajos a esta escala.

### C. Recomendaciones para Producción

*   **Alias de Lex:** Usar diferentes alias (`dev`, `staging`, `prod`) para gestionar el ciclo de vida del bot.
*   **Manejo de Secretos:** Usar **AWS Secrets Manager** en lugar de variables de entorno para valores sensibles.
*   **Pruebas Automatizadas:** Añadir un paso de validación al pipeline para medir la precisión del nuevo modelo antes de desplegarlo.
*   **Manejo de Errores:** Implementar Dead-Letter Queues (DLQs) en Lambda para capturar y manejar fallos de procesamiento.

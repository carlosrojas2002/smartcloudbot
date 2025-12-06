import json
import boto3
import os
import uuid
from datetime import datetime

# --- Clientes de AWS ---
# Es una buena práctica inicializarlos fuera del handler para reutilizar conexiones
comprehend_client = boto3.client('comprehend')
translate_client = boto3.client('translate')
lex_client = boto3.client('lexv2-runtime')
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# --- Variables de Entorno ---
# Cargar configuración desde las variables de entorno de Lambda
LEX_BOT_ID = os.environ.get('LEX_BOT_ID', 'YOUR_LEX_BOT_ID')
LEX_BOT_ALIAS_ID = os.environ.get('LEX_BOT_ALIAS_ID', 'YOUR_LEX_BOT_ALIAS_ID')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'chatbot_conversations')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'mi-cafeteria-chatbot-logs')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-v2')

# Tabla de DynamoDB
conversation_table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# --- Funciones Auxiliares ---

def detect_language(text):
    """Detecta el idioma principal del texto usando Amazon Comprehend."""
    try:
        response = comprehend_client.detect_dominant_language(Text=text)
        language_code = response['Languages'][0]['LanguageCode']
        print(f"Idioma detectado: {language_code}")
        return language_code
    except Exception as e:
        print(f"Error al detectar el idioma: {e}")
        return 'es' # Devuelve un idioma por defecto en caso de error

def translate_text(text, source_lang, target_lang):
    """Traduce texto de un idioma a otro usando Amazon Translate."""
    if source_lang == target_lang:
        return text
    try:
        response = translate_client.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        translated_text = response['TranslatedText']
        print(f"Texto traducido de '{source_lang}' a '{target_lang}': {translated_text}")
        return translated_text
    except Exception as e:
        print(f"Error al traducir: {e}")
        return text # Devuelve el texto original en caso de error

def invoke_lex(text, session_id, locale_id):
    """Envía el texto del usuario a Amazon Lex V2 para procesar el NLU."""
    try:
        response = lex_client.recognize_text(
            botId=LEX_BOT_ID,
            botAliasId=LEX_BOT_ALIAS_ID,
            localeId=locale_id,
            sessionId=session_id,
            text=text
        )
        print(f"Respuesta de Lex: {json.dumps(response)}")
        return response
    except Exception as e:
        print(f"Error al invocar Lex: {e}")
        return None

def invoke_bedrock(text):
    """
    Invoca a un modelo de Amazon Bedrock para obtener una respuesta a preguntas abiertas.
    Utiliza el modelo Claude de Anthropic en este ejemplo.
    """
    prompt = f"\\n\\nHuman: Eres un asistente de una cafetería. Responde a la siguiente pregunta de un cliente de forma amable y concisa: '{text}'\\n\\nAssistant:"

    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": 300,
        "temperature": 0.7,
        "top_p": 0.9,
    })

    try:
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId=BEDROCK_MODEL_ID,
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(response.get('body').read())
        completion = response_body.get('completion')
        print(f"Respuesta de Bedrock: {completion}")
        return completion
    except Exception as e:
        print(f"Error al invocar Bedrock: {e}")
        return "Lo siento, no he podido procesar tu solicitud en este momento."

def log_interaction(session_id, user_input, detected_lang, translated_input, intent, slots, response_text, source):
    """Registra la conversación completa en DynamoDB y S3."""
    timestamp = datetime.utcnow().isoformat()
    log_item = {
        'interactionId': str(uuid.uuid4()),
        'sessionId': session_id,
        'timestamp': timestamp,
        'userInput': user_input,
        'detectedLanguage': detected_lang,
        'translatedInput': translated_input,
        'intent': intent,
        'slots': json.dumps(slots) if slots else '{}',
        'responseText': response_text,
        'sourceService': source # 'Lex' o 'Bedrock'
    }

    # Guardar en DynamoDB
    try:
        conversation_table.put_item(Item=log_item)
        print("Interacción guardada en DynamoDB.")
    except Exception as e:
        print(f"Error al guardar en DynamoDB: {e}")

    # Guardar en S3 (para reentrenamiento)
    try:
        s3_object_key = f"logs/{timestamp.split('T')[0]}/{log_item['interactionId']}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_object_key,
            Body=json.dumps(log_item),
            ContentType='application/json'
        )
        print(f"Interacción guardada en S3: {s3_object_key}")
    except Exception as e:
        print(f"Error al guardar en S3: {e}")

# --- Handler Principal ---

def lambda_handler(event, context):
    """
    Punto de entrada de la función Lambda.
    El evento de entrada puede variar según el origen (API Gateway, Lex, etc.).
    Este ejemplo asume una entrada simple desde API Gateway:
    { "inputText": "...", "sessionId": "..." }
    """
    print(f"Evento recibido: {json.dumps(event)}")

    user_input = event.get('inputText', '')
    session_id = event.get('sessionId', str(uuid.uuid4())) # Genera un ID de sesión si no se proporciona

    # 1. Detectar el idioma del usuario
    detected_lang = detect_language(user_input)

    # 2. Traducir si es necesario (asumimos que Lex está configurado en español como idioma operativo principal)
    operational_lang = 'es'
    text_to_process = translate_text(user_input, detected_lang, operational_lang)

    # 3. Reenviar a Lex para NLU
    lex_response = invoke_lex(text_to_process, session_id, 'es_ES') # Siempre enviamos en el idioma de operación

    final_response_text = ""
    intent_name = "Fallback"
    slots = {}
    source = "Bedrock"

    # 4. Decidir si usar la respuesta de Lex o escalar a Bedrock
    if lex_response and lex_response.get('sessionState', {}).get('intent', {}).get('name') and lex_response['sessionState']['intent']['confidence'] > 0.6:
        # Si Lex tiene una alta confianza, usamos su respuesta
        intent_name = lex_response['sessionState']['intent']['name']
        slots = lex_response['sessionState']['intent'].get('slots', {})
        # Extraer el mensaje de la respuesta de Lex
        messages = lex_response.get('messages', [])
        if messages:
            final_response_text = messages[0].get('content', "No he entendido tu pregunta.")
        source = "Lex"
    else:
        # Si Lex no está seguro o falla, usamos Bedrock
        print("Lex no pudo resolver la intención con confianza. Escalando a Bedrock.")
        final_response_text = invoke_bedrock(text_to_process)

    # 5. Traducir la respuesta de vuelta al idioma del usuario
    final_response_translated = translate_text(final_response_text, operational_lang, detected_lang)

    # 6. Guardar la interacción
    log_interaction(
        session_id=session_id,
        user_input=user_input,
        detected_lang=detected_lang,
        translated_input=text_to_process,
        intent=intent_name,
        slots=slots,
        responseText=final_response_translated,
        source=source
    )

    # 7. Devolver la respuesta al cliente
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'response': final_response_translated
        })
    }

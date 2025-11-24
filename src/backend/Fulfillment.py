import boto3
import json
import re
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_faq = dynamodb.Table('FAQKnowledgeBase')
table_logs = dynamodb.Table('ChatSessionLogs')

def lambda_handler(event, context):
    print("Event received:", json.dumps(event, ensure_ascii=False))
    
    try:
        # Obtener el topic y idioma
        topic = obtener_topic(event)
        session_attributes = event.get('sessionState', {}).get('sessionAttributes', {})
        idioma = session_attributes.get('idioma', 'es')
        
        print(f"Topic: {topic}, Idioma: {idioma}")
        
        # Buscar en DynamoDB
        respuesta = buscar_respuesta(topic, idioma)
        
        # Analizar sentimiento mejorado
        input_text = event.get('inputTranscript', '')
        sentimiento = analizar_sentimiento_mejorado(input_text, idioma)
        
        # Log de la sesión
        guardar_log(event, respuesta, idioma, sentimiento)
        
        return construir_respuesta_lex(respuesta, sentimiento, idioma)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return construir_respuesta_error(idioma)

def obtener_topic(event):
    """Extrae el topic de forma robusta"""
    try:
        slots = event.get('sessionState', {}).get('intent', {}).get('slots', {})
        topic_slot = slots.get('Topic', {})
        
        # Múltiples formas de extraer el valor
        topic = (
            topic_slot.get('value', {}).get('interpretedValue') or
            topic_slot.get('value', {}).get('originalValue') or
            topic_slot.get('interpretedValue') or
            topic_slot.get('originalValue') or
            topic_slot.get('value') or
            "general"
        )
        
        if isinstance(topic, dict):
            topic = topic.get('interpretedValue') or topic.get('originalValue') or "general"
        
        return str(topic).lower().strip()
        
    except Exception as e:
        print(f"Error obteniendo topic: {e}")
        return "general"

def buscar_respuesta(topic, idioma):
    """Busca respuesta considerando variaciones y sinónimos"""
    try:
        # Primero buscar por keyword exacto
        response = table_faq.get_item(Key={'keyword': topic})
        
        if 'Item' in response:
            item = response['Item']
            respuesta = item.get(f'respuesta_{idioma}') or item.get('respuesta_es')
            if respuesta:
                return respuesta
        
        # Búsqueda por variaciones en la tabla
        response = table_faq.scan()
        for item in response.get('Items', []):
            variaciones = item.get('variaciones', [])
            if topic in variaciones:
                respuesta = item.get(f'respuesta_{idioma}') or item.get('respuesta_es')
                if respuesta:
                    return respuesta
        
        # Respuesta por defecto
        respuestas_default = {
            'es': 'Lo siento, no tengo información sobre ese tema. ¿Puedes intentar con "precio", "horario" o "ubicación"?',
            'en': "I'm sorry, I don't have information about that topic. Can you try with 'price', 'schedule' or 'location'?",
            'pt': 'Desculpe, não tenho informações sobre esse tópico. Pode tentar com "preço", "horário" ou "localização"?'
        }
        return respuestas_default.get(idioma, respuestas_default['es'])
        
    except Exception as e:
        print(f"Error buscando respuesta: {e}")
        return "Ocurrió un error al buscar la información."

def analizar_sentimiento_mejorado(texto, idioma):
    """Análisis de sentimiento mejorado con más vocabulario"""
    try:
        palabras_positivas = {
            'es': ['excelente', 'bueno', 'genial', 'perfecto', 'gracias', 'ayuda', 'útil', 'fantástico', 'maravilloso', 'agradecido'],
            'en': ['excellent', 'good', 'great', 'perfect', 'thanks', 'helpful', 'awesome', 'fantastic', 'wonderful', 'thank you'],
            'pt': ['excelente', 'bom', 'ótimo', 'perfeito', 'obrigado', 'útil', 'maravilhoso', 'fantástico', 'agradecido']
        }
        
        palabras_negativas = {
            'es': ['malo', 'horrible', 'terrible', 'pésimo', 'odio', 'frustrado', 'enojado', 'molesto', 'insatisfecho', 'decepcionado'],
            'en': ['bad', 'horrible', 'terrible', 'awful', 'hate', 'frustrated', 'angry', 'upset', 'dissatisfied', 'disappointed'],
            'pt': ['ruim', 'horrível', 'terrível', 'péssimo', 'ódio', 'frustrado', 'nervoso', 'chateado', 'insatisfeito', 'decepcionado']
        }
        
        positivas = palabras_positivas.get(idioma, palabras_positivas['es'])
        negativas = palabras_negativas.get(idioma, palabras_negativas['es'])
        
        score = 0
        texto_lower = texto.lower()
        
        for palabra in positivas:
            if palabra in texto_lower:
                score += 1
        
        for palabra in negativas:
            if palabra in texto_lower:
                score -= 1
        
        if score > 0:
            return 'positivo'
        elif score < 0:
            return 'negativo'
        else:
            return 'neutral'
            
    except Exception as e:
        print(f"Error analizando sentimiento: {e}")
        return 'neutral'

def guardar_log(event, respuesta, idioma, sentimiento):
    """Guarda el log mejorado con más información"""
    try:
        table_logs.put_item(Item={
            'sessionId': event.get('sessionId', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'inputText': event.get('inputTranscript', ''),
            'detectedLanguage': idioma,
            'sentiment': sentimiento,
            'botResponse': respuesta,
            'intent': event.get('sessionState', {}).get('intent', {}).get('name', 'Unknown')
        })
    except Exception as e:
        print(f"Error guardando log: {e}")

def construir_respuesta_lex(respuesta, sentimiento, idioma):
    """Construye respuesta con personalización por sentimiento"""
    try:
        # Personalizar respuesta basada en sentimiento
        if sentimiento == 'positivo':
            prefijos = {
                'es': '¡Me alegra saber que estás contento! ',
                'en': "I'm glad you're happy! ",
                'pt': 'Fico feliz em saber que está contente! '
            }
            respuesta = prefijos.get(idioma, '') + respuesta
        elif sentimiento == 'negativo':
            sufijos = {
                'es': ' Lamento escuchar eso. ¿Hay algo más en lo que pueda ayudarte para mejorar tu experiencia?',
                'en': ' Sorry to hear that. Is there anything else I can help you with to improve your experience?',
                'pt': ' Lamento ouvir isso. Há algo mais em que posso ajudá-lo para melhorar sua experiência?'
            }
            respuesta = respuesta + sufijos.get(idioma, '')
        
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': 'AskFAQ',
                    'state': 'Fulfilled'
                },
                'sessionAttributes': {
                    'idioma': idioma,
                    'ultimoSentimiento': sentimiento
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': respuesta
                }
            ]
        }
    except Exception as e:
        print(f"Error construyendo respuesta: {e}")
        return construir_respuesta_error(idioma)

def construir_respuesta_error(idioma):
    """Construye respuesta de error"""
    mensajes_error = {
        'es': 'Lo siento, ocurrió un error. Por favor, intenta de nuevo.',
        'en': "I'm sorry, an error occurred. Please try again.",
        'pt': 'Desculpe, ocorreu um erro. Por favor, tente novamente.'
    }
    
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': 'AskFAQ',
                'state': 'Failed'
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': mensajes_error.get(idioma, mensajes_error['es'])
            }
        ]
    }
import json
import boto3

# Diccionario de traducciones expandido
TRADUCCIONES = {
    'en': {
        # Preguntas comunes en inglés
        'price': 'precio',
        'cost': 'precio',
        'schedule': 'horario', 
        'hours': 'horario',
        'time': 'horario',
        'location': 'ubicacion',
        'address': 'ubicacion',
        'place': 'ubicacion',
        'contact': 'contacto',
        'support': 'contacto',
        'help': 'contacto',
        
        # Palabras de contexto
        'what': 'qué',
        'how': 'cómo',
        'where': 'dónde',
        'when': 'cuándo',
        'why': 'por qué',
        'want': 'quiero',
        'need': 'necesito',
        'know': 'saber',
        'information': 'información',
        'about': 'sobre'
    },
    'pt': {
        # Preguntas comunes en portugués
        'preço': 'precio',
        'custo': 'precio',
        'horário': 'horario',
        'hora': 'horario',
        'localização': 'ubicacion',
        'endereço': 'ubicacion',
        'contato': 'contacto',
        'suporte': 'contacto',
        'ajuda': 'contacto',
        
        # Palabras de contexto
        'qual': 'qué',
        'como': 'cómo',
        'onde': 'dónde',
        'quando': 'cuándo',
        'porque': 'por qué',
        'quero': 'quiero',
        'preciso': 'necesito',
        'saber': 'saber',
        'informação': 'información',
        'sobre': 'sobre'
    }
}

# Respuestas por defecto en 3 idiomas
RESPUESTAS_DEFAULT = {
    'es': {
        'error': 'Lo siento, no tengo información sobre ese tema. ¿Puedes intentar con "precio", "horario" o "ubicación"?',
        'saludo': '¡Hola! ¿En qué puedo ayudarte? Puedes preguntar sobre precios, horarios, ubicación o contacto.',
        'despedida': '¡Gracias por contactarnos! ¿Hay algo más en lo que pueda ayudarte?'
    },
    'en': {
        'error': "I'm sorry, I don't have information about that topic. Can you try with 'price', 'schedule' or 'location'?",
        'saludo': "Hello! How can I help you? You can ask about prices, schedules, location or contact.",
        'despedida': "Thank you for contacting us! Is there anything else I can help you with?"
    },
    'pt': {
        'error': 'Desculpe, não tenho informações sobre esse tópico. Pode tentar com "preço", "horário" ou "localização"?',
        'saludo': 'Olá! Como posso ajudá-lo? Pode perguntar sobre preços, horários, localização ou contato.',
        'despedida': 'Obrigado por entrar em contato! Há algo mais em que posso ajudá-lo?'
    }
}

def lambda_handler(event, context):
    print("🔍 === LAMBDA ORQUESTADOR MULTILINGÜE ===")
    
    # Headers CORS
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, DELETE',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Credentials': 'false'
    }
    
    # Manejar preflight OPTIONS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'status': 'OK'})
        }
    
    try:
        # Parsear body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body_data = json.loads(body)
        else:
            body_data = body
            
        user_message = body_data.get('message', '').strip()
        session_id = body_data.get('sessionId', 'default-session')
        
        print(f"💬 Mensaje recibido: '{user_message}'")
        
        if not user_message:
            return respuesta_error('Mensaje vacío', 'es', cors_headers)
        
        # 1. Detectar idioma MEJORADO
        detected_language = detectar_idioma_mejorado(user_message)
        print(f"🌐 Idioma detectado: {detected_language}")
        
        # 2. Generar respuesta en el idioma detectado
        response_text = generar_respuesta_multilingue(user_message, detected_language)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'response': response_text,
                'detectedLanguage': detected_language,
                'status': 'success'
            })
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return respuesta_error('Error interno', 'es', cors_headers)

def detectar_idioma_mejorado(texto):
    """Detección MEJORADA de idioma con scoring"""
    texto_lower = texto.lower()
    
    # Scoring por idioma
    scores = {'es': 0, 'en': 0, 'pt': 0}
    
    # Palabras clave por idioma
    palabras_es = ['hola', 'precio', 'horario', 'ubicacion', 'contacto', 'gracias', 'por favor', 'qué', 'cómo', 'dónde']
    palabras_en = ['hello', 'hi', 'price', 'cost', 'schedule', 'hours', 'location', 'address', 'contact', 'thanks', 'please', 'what', 'how', 'where']
    palabras_pt = ['olá', 'oi', 'preço', 'custo', 'horário', 'hora', 'localização', 'endereço', 'contato', 'obrigado', 'por favor', 'qual', 'como', 'onde']
    
    # Calcular scores
    for palabra in palabras_es:
        if palabra in texto_lower:
            scores['es'] += 1
    
    for palabra in palabras_en:
        if palabra in texto_lower:
            scores['en'] += 1
            
    for palabra in palabras_pt:
        if palabra in texto_lower:
            scores['pt'] += 1
    
    # Determinar idioma ganador
    idioma_ganador = max(scores, key=scores.get)
    
    # Si no hay suficientes indicadores, usar español por defecto
    if scores[idioma_ganador] == 0:
        return 'es'
    
    return idioma_ganador

def generar_respuesta_multilingue(mensaje, idioma):
    """Genera respuesta en el idioma correspondiente"""
    mensaje_lower = mensaje.lower()
    
    # Primero traducir el mensaje a español para procesamiento
    mensaje_es = traducir_a_espanol(mensaje, idioma)
    
    # Respuestas en diferentes idiomas basadas en palabras clave
    if any(palabra in mensaje_lower for palabra in ['precio', 'price', 'preço', 'cost', 'custo']):
        return obtener_respuesta_precio(idioma)
    
    elif any(palabra in mensaje_lower for palabra in ['horario', 'schedule', 'horário', 'hours', 'time', 'hora']):
        return obtener_respuesta_horario(idioma)
    
    elif any(palabra in mensaje_lower for palabra in ['ubicacion', 'location', 'localização', 'address', 'place', 'endereço']):
        return obtener_respuesta_ubicacion(idioma)
    
    elif any(palabra in mensaje_lower for palabra in ['contacto', 'contact', 'contato', 'support', 'suporte', 'help', 'ajuda']):
        return obtener_respuesta_contacto(idioma)
    
    elif any(palabra in mensaje_lower for palabra in ['hola', 'hello', 'hi', 'olá', 'oi']):
        return RESPUESTAS_DEFAULT[idioma]['saludo']
    
    else:
        return RESPUESTAS_DEFAULT[idioma]['error']

def traducir_a_espanol(texto, idioma_original):
    """Traduce palabras clave al español para procesamiento"""
    if idioma_original == 'es':
        return texto.lower()
    
    texto_traducido = texto.lower()
    for palabra_ext, palabra_es in TRADUCCIONES[idioma_original].items():
        texto_traducido = texto_traducido.replace(palabra_ext, palabra_es)
    
    return texto_traducido

# Respuestas específicas por idioma
def obtener_respuesta_precio(idioma):
    respuestas = {
        'es': "💰 *Precios:*\n• Plan Básico: $50/mes\n• Plan Premium: $80/mes\n• Plan Empresarial: $120/mes\n\n¿Te gustaría más información sobre algún plan en específico?",
        'en': "💰 *Prices:*\n• Basic Plan: $50/month\n• Premium Plan: $80/month\n• Enterprise Plan: $120/month\n\nWould you like more information about a specific plan?",
        'pt': "💰 *Preços:*\n• Plano Básico: $50/mês\n• Plano Premium: $80/mês\n• Plano Empresarial: $120/mês\n\nGostaria de mais informações sobre algum plano específico?"
    }
    return respuestas.get(idioma, respuestas['es'])

def obtener_respuesta_horario(idioma):
    respuestas = {
        'es': "🕐 *Horario de Atención:*\n• Lunes a Viernes: 9:00 AM - 6:00 PM\n• Sábados: 9:00 AM - 1:00 PM\n• Soporte 24/7 para emergencias\n\n¿Necesitas información específica sobre algún horario?",
        'en': "🕐 *Business Hours:*\n• Monday to Friday: 9:00 AM - 6:00 PM\n• Saturdays: 9:00 AM - 1:00 PM\n• 24/7 support for emergencies\n\nDo you need specific information about any schedule?",
        'pt': "🕐 *Horário de Atendimento:*\n• Segunda a Sexta: 9:00 às 18:00\n• Sábados: 9:00 às 13:00\n• Suporte 24/7 para emergências\n\nPrecisa de informações específicas sobre algum horário?"
    }
    return respuestas.get(idioma, respuestas['es'])

def obtener_respuesta_ubicacion(idioma):
    respuestas = {
        'es': "📍 *Ubicación:*\n• Dirección: Av. Principal 123, Ciudad\n• Teléfono: +1-234-567-8900\n• Email: info@smartcloud.com\n\n¿Necesitas direcciones específicas o información de transporte?",
        'en': "📍 *Location:*\n• Address: Main Ave 123, City\n• Phone: +1-234-567-8900\n• Email: info@smartcloud.com\n\nDo you need specific directions or transportation information?",
        'pt': "📍 *Localização:*\n• Endereço: Av. Principal 123, Cidade\n• Telefone: +1-234-567-8900\n• Email: info@smartcloud.com\n\nPrecisa de direções específicas ou informações de transporte?"
    }
    return respuestas.get(idioma, respuestas['es'])

def obtener_respuesta_contacto(idioma):
    respuestas = {
        'es': "📞 *Contacto:*\n• Teléfono: +1-234-567-8900\n• Email: soporte@smartcloud.com\n• Chat en vivo: Disponible en nuestro sitio web\n• Redes sociales: @SmartCloudBot\n\n¿Por cuál medio prefieres contactarnos?",
        'en': "📞 *Contact:*\n• Phone: +1-234-567-8900\n• Email: support@smartcloud.com\n• Live chat: Available on our website\n• Social media: @SmartCloudBot\n\nWhich contact method do you prefer?",
        'pt': "📞 *Contato:*\n• Telefone: +1-234-567-8900\n• Email: suporte@smartcloud.com\n• Chat ao vivo: Disponível em nosso site\n• Redes sociais: @SmartCloudBot\n\nPor qual meio prefere nos contactar?"
    }
    return respuestas.get(idioma, respuestas['es'])

def respuesta_error(mensaje, idioma, headers):
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'response': RESPUESTAS_DEFAULT[idioma]['error'],
            'detectedLanguage': idioma,
            'status': 'error'
        })
    }
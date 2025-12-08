import json

# --- Funciones de Ayuda para construir la respuesta de Lex ---

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Construye una respuesta para que Lex pida al usuario el valor de un slot específico.
    """
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': {
                'name': intent_name,
                'slots': slots
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': message
            }
        ]
    }

def close(session_attributes, intent_name, state, message):
    """
    Construye una respuesta para cerrar la conversación con un estado final (ej. 'Fulfilled').
    """
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': intent_name,
                'state': state
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': message
            }
        ]
    }

# --- Lógica principal del Intent 'RealizarPedido' ---

def validar_pedido(slots):
    """
    Valida los slots del pedido uno por uno.
    Si un slot es inválido o falta, devuelve un diccionario indicando el error.
    Si todo es válido, devuelve {'isValid': True}.
    """
    # 1. Validar TiposDeBebida
    if not slots.get('TiposDeBebida'):
        return {
            'isValid': False,
            'violatedSlot': 'TiposDeBebida',
            'message': '¿Qué tipo de bebida te gustaría pedir?'
        }

    valid_bebidas = ["Espresso", "Cappuccino", "Latte", "Americano", "Tinto", "Café"]
    valid_bebidas_lower = [b.lower() for b in valid_bebidas]

    bebida_slot = slots['TiposDeBebida']
    # El valor puede no estar presente si el usuario introduce algo no reconocido
    if not bebida_slot or not bebida_slot.get('value') or not bebida_slot['value'].get('interpretedValue'):
         return {
            'isValid': False,
            'violatedSlot': 'TiposDeBebida',
            'message': f"No entendí tu bebida. Solo tenemos: {', '.join(valid_bebidas)}. ¿Cuál prefieres?"
        }

    bebida = bebida_slot['value']['interpretedValue'].lower()

    if bebida not in valid_bebidas_lower:
        return {
            'isValid': False,
            'violatedSlot': 'TiposDeBebida',
            'message': f"Lo siento, solo tenemos: {', '.join(valid_bebidas)}. ¿Cuál te gustaría?"
        }

    # 2. Validar Tamaño (Asumiendo que el slot se llama 'Tamao' sin ñ)
    if not slots.get('Tamao'):
        return {
            'isValid': False,
            'violatedSlot': 'Tamao',
            'message': f"Perfecto, un {bebida.capitalize()}. ¿En qué tamaño lo quieres: pequeño, mediano o grande?"
        }

    valid_tamanos = ["pequeño", "mediano", "grande"]
    tamano_slot = slots['Tamao']
    if not tamano_slot or not tamano_slot.get('value') or not tamano_slot['value'].get('interpretedValue'):
        return {
            'isValid': False,
            'violatedSlot': 'Tamao',
            'message': "No entendí el tamaño. Solo tenemos pequeño, mediano o grande. ¿Cuál prefieres?"
        }

    tamano = tamano_slot['value']['interpretedValue'].lower()

    if tamano not in valid_tamanos:
         return {
            'isValid': False,
            'violatedSlot': 'Tamao',
            'message': "Solo tenemos tamaños pequeño, mediano o grande. ¿Cuál prefieres?"
        }

    # 3. Validar Cantidad
    if not slots.get('Cantidad'):
        return {
            'isValid': False,
            'violatedSlot': 'Cantidad',
            'message': f"Ok, un {bebida.capitalize()} {tamano}. ¿Cuántos vas a querer?"
        }

    cantidad_slot = slots['Cantidad']
    if not cantidad_slot or not cantidad_slot.get('value') or not cantidad_slot['value'].get('interpretedValue'):
        return {
            'isValid': False,
            'violatedSlot': 'Cantidad',
            'message': "No entendí la cantidad. Por favor, dime un número."
        }

    try:
        cantidad = int(cantidad_slot['value']['interpretedValue'])
        if not (1 <= cantidad <= 10):
            raise ValueError()
    except (ValueError, TypeError):
        return {
            'isValid': False,
            'violatedSlot': 'Cantidad',
            'message': "Por favor, dime un número entre 1 y 10."
        }

    # Si todo es válido
    return {'isValid': True}


def realizar_pedido(event):
    """
    Maneja el intent de realizar un pedido, validando y pidiendo slots.
    """
    intent_name = event['sessionState']['intent']['name']
    slots = event['sessionState']['intent']['slots']
    session_attributes = event.get('sessionState', {}).get('sessionAttributes', {})

    # Validar todos los slots
    validation_result = validar_pedido(slots)

    # Si la validación falla, significa que un slot falta o es incorrecto
    if not validation_result['isValid']:
        next_slot = validation_result['violatedSlot']
        message = validation_result['message']

        # Limpiamos el valor del slot si es inválido para que Lex lo pida de nuevo
        if slots.get(next_slot):
            slots[next_slot] = None

        return elicit_slot(session_attributes, intent_name, slots, next_slot, message)

    # Si todo es válido, preparamos el mensaje final y cerramos la conversación
    bebida = slots['TiposDeBebida']['value']['interpretedValue']
    tamano = slots['Tamao']['value']['interpretedValue']
    cantidad = int(slots['Cantidad']['value']['interpretedValue'])

    # Pluralización simple
    bebida_plural = f"{bebida}s" if cantidad > 1 else bebida

    confirmation_message = f"¡Pedido confirmado! {cantidad} {bebida_plural.capitalize()} de tamaño {tamano}. ¡Estará listo en unos minutos!"

    return close(session_attributes, intent_name, 'Fulfilled', confirmation_message)


# --- Dispatcher ---

def dispatch(event):
    """
    Llama al manejador del intent correspondiente.
    """
    intent_name = event['sessionState']['intent']['name']

    # Asumimos que el único intent que maneja esta Lambda es 'RealizarPedido'
    if intent_name == 'RealizarPedido':
        return realizar_pedido(event)

    raise Exception(f'El intent "{intent_name}" no es soportado por esta Lambda.')


# --- Handler Principal ---

def lambda_handler(event, context):
    """
    Punto de entrada principal para la función Lambda.
    """
    # Imprimir el evento para depuración
    print("Evento recibido de Lex:", json.dumps(event, ensure_ascii=False))

    try:
        response = dispatch(event)
        return response
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        # Respuesta de error genérica para Lex
        return close({}, event.get('sessionState', {}).get('intent', {}).get('name', 'FallbackIntent'), 'Failed', "Lo siento, ocurrió un error inesperado al procesar tu pedido. Por favor, intenta de nuevo.")

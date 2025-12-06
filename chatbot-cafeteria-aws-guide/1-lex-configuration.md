# Guía de Configuración de Amazon Lex V2

Este documento detalla los pasos para crear y configurar el bot `CafeteriaBot` en la consola de Amazon Lex V2.

## 1. Creación del Bot en la Consola de AWS

1.  **Navegar a Amazon Lex**: Inicia sesión en la [Consola de AWS](https://aws.amazon.com/console/), busca "Lex" en la barra de búsqueda y selecciona el servicio.
2.  **Asegurarse de estar en V2**: La consola de Lex tiene dos versiones. Asegúrate de que en el menú de la izquierda ponga "Bots V2".
3.  **Crear el Bot**:
    *   Haz clic en el botón **"Create bot"**.
    *   Selecciona la opción **"Create a blank bot"**.
    *   **Bot name**: `CafeteriaBot`.
    *   **IAM permissions**: Elige **"Create a role with basic Amazon Lex permissions"**. AWS creará automáticamente un rol con los permisos necesarios.
    *   **Children's Online Privacy Protection Act (COPPA)**: Selecciona **"No"**.
    *   **Idle session timeout**: Deja el valor por defecto de **5 minutos**.
    *   Haz clic en **"Next"**.
4.  **Configurar el Primer Idioma**:
    *   **Language**: Selecciona **"Spanish (ES)"**. Puedes elegir otra variante de español si lo prefieres.
    *   **Voice interaction**: Elige una voz que te guste, por ejemplo, **"Lucia"**.
    *   **Intent classification confidence score threshold**: Deja el valor por defecto de **0.40**.
    *   Haz clic en **"Done"**.

## 2. Añadir Idiomas Adicionales (Inglés y Portugués)

Una vez creado el bot, estarás en la configuración del idioma español.

1.  En el menú de la izquierda, bajo "Bot details", haz clic en **"Languages"**.
2.  Haz clic en el botón **"Add language"**.
3.  **Seleccionar Inglés**:
    *   En la ventana emergente, selecciona **"English (US)"**.
    *   Elige una voz, por ejemplo, **"Joanna"**.
    *   Haz clic en **"Add"**.
4.  **Seleccionar Portugués**:
    *   Vuelve a hacer clic en **"Add language"**.
    *   Selecciona **"Portuguese (BR)"**.
    *   Elige una voz, por ejemplo, **"Camila"**.
    *   Haz clic en **"Add"**.

Ahora tu bot está listo para ser configurado en tres idiomas. Deberás definir los intents y utterances para cada uno por separado.

## 3. Creación de Intents y Utterances

A continuación, se definen los intents principales. Debes añadirlos para cada idioma, traduciendo los utterances correspondientes.

---

### Intent 1: `Saludo`

Este intent gestiona los saludos iniciales del usuario.

- **Intent name**: `Saludo`
- **Sample utterances**:
    - **Español**: `hola`, `buenos dias`, `que tal`, `hey`, `buenas tardes`
    - **Inglés**: `hello`, `hi`, `good morning`, `hey`, `good afternoon`
    - **Portugués**: `oi`, `olá`, `bom dia`, `boa tarde`
- **Responses (Closing response)**:
    - **Español**: `¡Hola! Soy el asistente virtual de la cafetería. ¿En qué puedo ayudarte?`
    - **Inglés**: `Hello! I'm the coffee shop's virtual assistant. How can I help you?`
    - **Portugués**: `Olá! Eu sou o assistente virtual da cafeteria. Como posso ajudar?`

---

### Intent 2: `PedirMenu`

Proporciona al usuario el menú de la cafetería.

- **Intent name**: `PedirMenu`
- **Sample utterances**:
    - **Español**: `me das el menu`, `que tienes para tomar`, `quiero ver la carta`, `que cafes teneis`, `menu por favor`
    - **Inglés**: `can I see the menu`, `what do you have`, `show me the menu`, `what coffees are available`, `menu please`
    - **Portugués**: `pode me dar o cardapio`, `o que voce tem`, `quero ver o menu`, `quais cafes voces tem`, `cardapio por favor`
- **Responses (Closing response)**:
    - **Español**: `Claro, aquí tienes nuestro menú: [Enlace a tu menú online o descripción en texto].`
    - **Inglés**: `Of course, here is our menu: [Link to your online menu or text description].`
    - **Portugués**: `Claro, aqui está o nosso cardápio: [Link para o seu cardápio online ou descrição em texto].`

---

### Intent 3: `PreguntarHorario`

Informa sobre el horario de apertura.

- **Intent name**: `PreguntarHorario`
- **Sample utterances**:
    - **Español**: `a que hora abren`, `cual es el horario`, `estan abiertos ahora`, `cuando cierran`
    - **Inglés**: `what are your hours`, `when do you open`, `are you open now`, `when do you close`
    - **Portugués**: `qual e o seu horario`, `a que horas voces abrem`, `voces estao abertos agora`, `quando voces fecham`
- **Responses (Closing response)**:
    - **Español**: `Nuestro horario es de Lunes a Sábado, de 8:00 a 20:00. ¡Te esperamos!`
    - **Inglés**: `Our hours are Monday to Saturday, from 8:00 AM to 8:00 PM. We look forward to seeing you!`
    - **Portugués**: `Nosso horário de funcionamento é de segunda a sábado, das 8h00 às 20h00. Esperamos por você!`

---

### Intent 4: `HacerPedido` (con Slots)

Gestiona la toma de un nuevo pedido. Este intent es más complejo porque necesita capturar información específica.

- **Intent name**: `HacerPedido`
- **Slots (información a capturar)**:
    1.  **`bebida`**:
        - **Slot name**: `bebida`
        - **Slot type**: `AMAZON.Food` (es un buen punto de partida, pero para producción se recomienda un tipo de slot personalizado con tu menú: `TipoBebida`).
        - **Prompt (Español)**: `¿Qué bebida te gustaría pedir?`
    2.  **`cantidad`**:
        - **Slot name**: `cantidad`
        - **Slot type**: `AMAZON.Number`
        - **Prompt (Español)**: `¿Cuántos quieres?`
    3.  **`tamano`**:
        - **Slot name**: `tamano`
        - **Slot type**: Crea un tipo de slot personalizado (`Custom slot type`).
            - **Slot type name**: `TipoTamano`
            - **Values**: `pequeño`, `mediano`, `grande`.
        - **Prompt (Español)**: `¿En qué tamaño: pequeño, mediano o grande?`
- **Sample utterances**:
    - **Español**: `quiero pedir un {bebida}`, `me pones {cantidad} cafe`, `dame un {bebida} de tamaño {tamano}`
    - **Inglés**: `I want to order a {bebida}`, `give me {cantidad} coffees`, `I'll have a {tamano} {bebida}`
    - **Portugués**: `eu quero pedir um {bebida}`, `me ve {cantidad} cafes`, `me da um {bebida} de tamanho {tamano}`
- **Confirmation Prompt**:
    - Activa la confirmación para que el bot verifique el pedido antes de procesarlo.
    - **Confirmation message (Español)**: `Entonces, quieres {cantidad} {bebida}(s) de tamaño {tamano}, ¿es correcto?`
- **Fulfillment**:
    - Por ahora, podemos usar una respuesta simple. La lógica real se ejecutará en la Lambda.
    - **Closing response (Español)**: `¡Perfecto! He registrado tu pedido.`

## 4. Guardar, Construir y Probar

1.  **Guardar**: Después de configurar cada intent, haz clic en **"Save intent"**.
2.  **Construir**: Una vez que hayas añadido todos los intents para un idioma, haz clic en el botón **"Build"** en la esquina superior derecha. Este proceso puede tardar un par de minutos. El *build* entrena el modelo NLU con los datos que has proporcionado.
3.  **Probar**:
    *   Cuando el *build* se complete, aparecerá una notificación.
    *   Haz clic en **"Test"** para abrir la ventana de chat de prueba.
    *   Escribe o di algunas de las *utterances* que definiste para verificar que el bot reconoce los intents y captura los slots correctamente.
    *   Repite el proceso de **Añadir Intents -> Construir -> Probar** para cada idioma.

Con estos pasos, tendrás la base de tu bot NLU lista para ser integrada con la función Lambda.
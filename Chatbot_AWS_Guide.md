# Procedimiento Detallado para Crear un Chatbot de Cafetería en AWS

Este documento proporciona una guía paso a paso para crear un chatbot multilingüe para una cafetería utilizando servicios gestionados de AWS.

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
4.  **Clave de partición:** `conversationId` (String)
5.  **Clave de ordenación:** `timestamp` (String)
6.  **Confirmación:** Clic en "Crear tabla".

### B. Crear Bucket en S3 para Activos

1.  **Servicio:** Amazon S3
2.  **Acción:** Clic en "Crear bucket".
3.  **Nombre del bucket:** `mi-cafeteria-chatbot-assets` (debe ser único globalmente).
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

### B. Configuración de Idiomas

1.  Añadir los siguientes idiomas: `Spanish (ES)`, `English (US)`, `Portuguese (BR)`.

### C. Creación de Intenciones (Intents)

*Para el idioma `Spanish (ES)` (y luego añadir utterances equivalentes para los otros idiomas):*

1.  **`Saludo`**:
    *   **Utterances:** "Hola", "Buenos días", "Qué tal".
2.  **`PedirMenu`**:
    *   **Utterances:** "Quiero ver el menú", "Qué tienes para comer", "Me muestras la carta".
3.  **`PreguntarHorarios`**:
    *   **Utterances:** "A qué hora abren", "Cuál es su horario", "Están abiertos ahora?".
4.  **`HacerPedido`**:
    *   **Utterances:** "Quiero hacer un pedido", "Quisiera pedir {pedidoDetalle}".
    *   **Slot:** Crear un slot llamado `pedidoDetalle`, de tipo `AMAZON.FreeFormInput`, con el prompt: "Claro, ¿qué te gustaría pedir?".
5.  **`PreguntaAbierta`**:
    *   **Utterances:** "De dónde traen el café", "Hay estacionamiento cerca", "Tienen opciones sin gluten".
6.  **`Fallback`**:
    *   Crear una intención con este nombre exacto. Lex la usará automáticamente cuando no entienda al usuario. No necesita utterances.

### D. Construir y Probar

1.  Hacer clic en el botón **"Generar" (Build)**.
2.  Una vez completado, usar la ventana de **"Probar"** para verificar que las intenciones se reconocen.

---

## Parte 3: Lógica Central (AWS Lambda)

### A. Política y Rol de IAM para Lambda

1.  **Servicio:** IAM > Políticas > "Crear política".
2.  **Pestaña JSON:** Pegar el siguiente código (reemplazando `ACCOUNT_ID`, `REGION`, y los nombres de tus recursos).

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
6.  **Adjuntar Políticas:** `CafeteriaBotLambdaPolicy` y `AWSLambdaBasicExecutionRole`.
7.  **Nombre del Rol:** `CafeteriaBotLambdaRole`.

### B. Crear Función Lambda

1.  **Servicio:** AWS Lambda > "Crear función".
2.  **Nombre:** `cafeteriaBotOrchestrator`
3.  **Runtime:** Python 3.11
4.  **Rol:** Seleccionar `CafeteriaBotLambdaRole`.
5.  **Configuración:**
    *   **General > Tiempo de espera:** `30 segundos`.
    *   **Variables de entorno:**
        *   `DYNAMODB_TABLE`: `cafeteria-chat-interactions`
        *   `S3_BUCKET`: `mi-cafeteria-chatbot-assets`
        *   `S3_KNOWLEDGE_KEY`: `knowledge-base/menu.txt`
        *   `SES_EMAIL_FROM`: Tu email verificado en SES.
        *   `SES_EMAIL_TO`: Email de destino para pedidos.

### C. Código de la Función Lambda

*En la pestaña "Código", pegar el script de Python completo proporcionado en el Paso 3 del plan.*

### D. Conectar y Desplegar

1.  Hacer clic en **"Deploy"** en la Lambda.
2.  Volver a la consola de **Lex > Alias > `TestBotAlias`**.
3.  Para cada idioma (`ES`, `EN`, `PT`), asociar la función Lambda `cafeteriaBotOrchestrator`.
4.  Hacer clic en **"Generar" (Build)** en el bot una vez más.

---

## Parte 4: Pipeline de Reentrenamiento (SageMaker)

*Los siguientes scripts deben crearse dentro de un entorno de SageMaker Studio.*

### A. Rol de IAM para SageMaker

1.  Crear una política en IAM llamada `CafeteriaBotSageMakerPipelinePolicy` con el JSON del **Paso 5** del plan.
2.  Crear un rol para el caso de uso **SageMaker** llamado `CafeteriaBotSageMakerPipelineRole` y adjuntarle la política recién creada.

### B. Scripts del Pipeline

1.  **`extract_and_process.py`**: Script para extraer datos de DynamoDB y formatearlos.
2.  **`retrain_and_deploy.py`**: Script para importar datos a Lex, reentrenar y desplegar.
3.  **`pipeline.py`**: Script de definición que orquesta los pasos anteriores.

*Los códigos completos para estos tres archivos se encuentran en el **Paso 4** del plan.*

### C. Ejecución del Pipeline

1.  Actualizar los placeholders (`ACCOUNT_ID`, `YOUR_BOT_ID`, etc.) en `pipeline.py`.
2.  Ejecutar `python pipeline.py` desde un terminal de SageMaker Studio para registrar el pipeline.
3.  Iniciar ejecuciones desde la consola de AWS: **SageMaker > Canalizaciones**.
4.  (Opcional) Automatizar la ejecución con una regla de **Amazon EventBridge**.

---

## Parte 5: Consideraciones Finales

### A. Limitaciones

*   **Calidad del NLU:** El NLU de Lex mejora significativamente con más utterances de entrenamiento nativas en cada idioma.
*   **Cold Starts:** La primera llamada a Lambda puede ser más lenta. Usar "Provisioned Concurrency" para aplicaciones sensibles a la latencia.
*   **Calidad de RAG:** La efectividad de las respuestas de Bedrock depende de la calidad de los documentos en S3.

### B. Costos Relativos (Mayor a Menor)

1.  **SageMaker:** Costo por tiempo de uso de instancias de Studio y jobs de procesamiento.
2.  **Amazon Bedrock:** Costo por tokens de entrada/salida procesados.
3.  **AWS Lambda:** Generalmente económico, con un generoso nivel gratuito.
4.  **Lex, Comprehend, Translate:** Costo por número de solicitudes.
5.  **DynamoDB, S3:** Costos de almacenamiento y operaciones, usualmente bajos a esta escala.

### C. Recomendaciones para Producción

*   **Alias de Lex:** Usar diferentes alias (`dev`, `staging`, `prod`) para gestionar el ciclo de vida del bot.
*   **Manejo de Secretos:** Usar **AWS Secrets Manager** para credenciales y valores sensibles.
*   **Pruebas Automatizadas:** Añadir un paso de validación al pipeline para medir la precisión del nuevo modelo antes de desplegarlo.
*   **Manejo de Errores:** Implementar Dead-Letter Queues (DLQs) en Lambda para manejar fallos de procesamiento.

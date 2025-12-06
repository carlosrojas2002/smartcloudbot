# Guía de Orquestación con AWS Lambda

Esta guía cubre la creación de la función Lambda que actúa como el "cerebro" del chatbot, conectando los servicios de AWS para procesar las solicitudes de los usuarios.

## 1. Creación de la Política de IAM

Antes de crear la función Lambda, es una buena práctica definir una política de IAM con los permisos mínimos necesarios.

1.  **Navegar a IAM**: En la [Consola de AWS](https://aws.amazon.com/console/), busca y selecciona "IAM".
2.  **Ir a Políticas**: En el menú de la izquierda, haz clic en **"Policies"**.
3.  **Crear Política**:
    *   Haz clic en **"Create policy"**.
    *   Selecciona la pestaña **"JSON"**.
    *   Copia y pega el contenido del archivo `iam_policy.json` que se encuentra en el directorio `lambda_function/`.
    *   **Importante**: Reemplaza los valores de placeholder como `<REGION>`, `<ACCOUNT_ID>`, `<BOT_ID>`, `<BOT_ALIAS_ID>`, `<TABLE_NAME>` y `<BUCKET_NAME>` con los valores reales de tus recursos.
    *   Haz clic en **"Next: Tags"**, luego en **"Next: Review"**.
    *   **Policy name**: `ChatbotCafeteriaLambdaPolicy`.
    *   **Description**: `Política con los permisos mínimos para la función Lambda del chatbot de la cafetería.`
    *   Haz clic en **"Create policy"**.

## 2. Creación del Rol de IAM

Ahora, crearás un rol que usará esta política. La función Lambda asumirá este rol para obtener los permisos.

1.  **Ir a Roles**: En el menú de la izquierda de IAM, haz clic en **"Roles"**.
2.  **Crear Rol**:
    *   Haz clic en **"Create role"**.
    *   **Trusted entity type**: Selecciona **"AWS service"**.
    *   **Use case**: Selecciona **"Lambda"**.
    *   Haz clic en **"Next"**.
3.  **Adjuntar la Política**:
    *   En la barra de búsqueda de políticas, busca y selecciona la política que acabas de crear: `ChatbotCafeteriaLambdaPolicy`.
    *   Haz clic en **"Next"**.
4.  **Nombrar el Rol**:
    *   **Role name**: `ChatbotCafeteriaLambdaRole`.
    *   **Description**: `Rol para la función Lambda del chatbot de la cafetería.`
    *   Haz clic en **"Create role"**.

## 3. Creación de la Función Lambda

1.  **Navegar a Lambda**: En la [Consola de AWS](https://aws.amazon.com/console/), busca y selecciona "Lambda".
2.  **Crear Función**:
    *   Haz clic en **"Create function"**.
    *   Selecciona **"Author from scratch"**.
    *   **Function name**: `chatbotCafeteriaOrchestrator`.
    *   **Runtime**: Selecciona **"Python 3.9"** o una versión más reciente.
    *   **Architecture**: Deja **"x86_64"**.
    *   **Permissions**: Expande "Change default execution role" y selecciona **"Use an existing role"**.
    *   En la lista de roles, elige el `ChatbotCafeteriaLambdaRole` que creaste anteriormente.
    *   Haz clic en **"Create function"**.
3.  **Subir el Código**:
    *   Una vez creada la función, serás llevado a su página de configuración.
    *   En la pestaña **"Code"**, verás un editor de código en línea (`lambda_function.py`).
    *   Borra el contenido por defecto y copia y pega el código del archivo `lambda_function/lambda_function.py` de esta guía.
4.  **Configurar Variables de Entorno**:
    *   Ve a la pestaña **"Configuration"** y luego a **"Environment variables"**.
    *   Haz clic en **"Edit"** y añade las siguientes variables. Esto evita tener que *hardcodear* valores en el código.
        *   `LEX_BOT_ID`: El ID de tu bot de Lex (ej. `A1B2C3D4E5`).
        *   `LEX_BOT_ALIAS_ID`: El ID del alias de tu bot de Lex (ej. `TSTALIASID`).
        *   `DYNAMODB_TABLE_NAME`: El nombre de tu tabla de DynamoDB (ej. `chatbot_conversations`).
        *   `S3_BUCKET_NAME`: El nombre de tu bucket de S3 (ej. `mi-cafeteria-chatbot-logs`).
        *   `BEDROCK_MODEL_ID`: El ID del modelo de Bedrock que quieres usar (ej. `anthropic.claude-v2`).
5.  **Ajustar la Configuración Básica**:
    *   En la pestaña **"Configuration"** -> **"General configuration"**, haz clic en **"Edit"**.
    *   Aumenta el **Timeout** a, por ejemplo, **15 segundos**. Esto da margen a los servicios de IA para responder.
    *   Haz clic en **"Save"**.
6.  **Desplegar los Cambios**:
    *   Después de pegar el código y configurar las variables, haz clic en el botón **"Deploy"** que aparece sobre el editor de código.

## 4. Conectar Lex a Lambda

El último paso es decirle a Lex que use esta función Lambda para la lógica de validación y *fulfillment*.

1.  **Volver a Lex**: Navega de vuelta a la consola de Amazon Lex y selecciona tu `CafeteriaBot`.
2.  **Seleccionar el Alias**: En el menú de la izquierda, haz clic en **"Aliases"** y selecciona el alias que estás usando (normalmente `TestBotAlias`).
3.  **Asociar la Lambda**:
    *   En la sección de **"Languages"**, haz clic en el idioma que quieres configurar (ej. "Spanish (ES)").
    *   Aparecerá una ventana para configurar el *fulfillment*.
    *   Selecciona la función `chatbotCafeteriaOrchestrator` que acabas de crear.
    *   Deja la versión como `$LATEST`.
    *   Haz clic en **"Save"**.
4.  **Habilitar en los Intents**:
    *   Ahora, ve a cada *intent* que deba invocar la lógica de la Lambda (como `HacerPedido`).
    *   Dentro del editor de intents, ve a la sección **"Fulfillment"**.
    *   Activa la opción **"Use a Lambda function for fulfillment"**.
    *   Guarda el intent y reconstruye (**Build**) el bot.

Tu función Lambda está ahora conectada y lista para orquestar la conversación.
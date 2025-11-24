```markdown
# Documentación de Arquitectura

Esta sección describe el flujo de datos y la interacción entre los servicios de AWS utilizados en el proyecto **SmartCloudBot**.

## Diagrama de Arquitectura

![Diagrama AWS](../architecture/ProyectoServidores.drawio.png)

## Flujo de Datos (Paso a Paso)

El sistema funciona mediante una cadena de eventos síncronos:

### 1. Capa de Presentación (Frontend)
* **Servicio:** Amazon S3.
* **Descripción:** El usuario accede a una página web estática (`index.html`). El navegador ejecuta JavaScript para capturar el input del usuario y enviarlo mediante una petición `POST` segura.

### 2. Capa de Entrada (Gateway)
* **Servicio:** Amazon API Gateway (HTTP API).
* **Descripción:** Actúa como la puerta de entrada pública. Recibe la petición JSON del frontend, maneja los encabezados CORS (seguridad del navegador) y enruta la solicitud hacia el backend.

### 3. Capa de Orquestación
* **Servicio:** AWS Lambda (`ChatbotOrchestrator`).
* **Función:**
    * Recibe el mensaje crudo.
    * Detecta el idioma del usuario (Inglés o Español).
    * Si es Inglés, realiza una traducción de entrada (Input Translation) para que el núcleo del bot lo entienda.
    * Envía el mensaje procesado a Amazon Lex.
    * Recibe la respuesta final, la traduce de vuelta al idioma del usuario y la entrega a la API.

### 4. Capa Cognitiva (NLU)
* **Servicio:** Amazon Lex V2.
* **Función:**
    * Analiza el texto para determinar la **Intención** (Intent), por ejemplo: `AskFAQ`.
    * Extrae las variables o **Ranuras** (Slots), por ejemplo: `Topic = 'precio'`.
    * Delega el cumplimiento de la intención a la Lambda de lógica.

### 5. Capa de Lógica y Datos (Fulfillment)
* **Servicio:** AWS Lambda (`ChatbotFulfillment`).
* **Función:**
    * Recibe la intención confirmada por Lex.
    * Realiza un **Análisis de Sentimiento** local (Positive/Negative/Neutral).
    * Consulta la tabla `FAQKnowledgeBase` en **DynamoDB** buscando la palabra clave.
    * Guarda un registro de auditoría en la tabla `ChatSessionLogs` en **DynamoDB**.
    * Construye la respuesta de texto y la devuelve a Lex.

## Decisiones de Diseño

* **Enfoque Serverless:** Se eligió para reducir costos operativos y permitir escalado automático a cero cuando no hay tráfico.
* **Separación de Lambdas:** Se separó la lógica de "Orquestación" (Web/Idiomas) de la lógica de "Negocio" (Datos/Lex) para mantener el principio de responsabilidad única.
* **Persistencia NoSQL:** DynamoDB fue seleccionado por su baja latencia (milisegundos) requerida para una experiencia de chat fluida.
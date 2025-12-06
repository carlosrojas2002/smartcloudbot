# Guía de Reentrenamiento Continuo con SageMaker Pipelines

El verdadero valor de un chatbot avanzado reside en su capacidad para "aprender" de las interacciones del mundo real. Un modelo estático se degrada con el tiempo a medida que los usuarios cambian la forma en que hablan. Esta guía describe una estrategia de MLOps (Machine Learning Operations) para el reentrenamiento continuo utilizando SageMaker Pipelines.

## 1. Estrategia de Aprendizaje Continuo

El objetivo es automatizar el proceso de tomar las conversaciones guardadas en S3, usarlas para mejorar el modelo NLU (o afinar el LLM) y desplegar la nueva versión sin intervención manual.

El ciclo de vida es el siguiente:
1.  **Acumulación de Datos**: La función Lambda guarda cada interacción en el bucket de S3. Con el tiempo, se acumula un valioso conjunto de datos de *utterances* reales.
2.  **Ejecución de la Canalización**: La canalización de SageMaker se activa de forma periódica (ej. cada dos semanas) o por un evento (ej. cuando se han acumulado 1,000 nuevas interacciones).
3.  **Procesamiento y Entrenamiento**: La canalización procesa los datos brutos, los formatea para el entrenamiento, reentrena el modelo y evalúa su rendimiento.
4.  **Validación y Despliegue**: Si el nuevo modelo supera al anterior en un conjunto de pruebas de validación, se despliega automáticamente, reemplazando a la versión en producción.

## 2. Componentes de SageMaker Pipeline

Una canalización de SageMaker es un flujo de trabajo compuesto por varios pasos. Para nuestro chatbot, los pasos serían:

*Nota: El siguiente diagrama es una representación conceptual. Para un despliegue en producción, se recomienda crear un diagrama detallado con una herramienta como Lucidchart o CloudFormation Designer.*

![SageMaker Pipeline](https://user-images.githubusercontent.com/12345678/98765433-fedcba987654.png) <!-- Placeholder para un diagrama futuro -->

### Paso 1: Extracción y Preprocesamiento de Datos
- **Propósito**: Leer los archivos JSON de logs desde S3, limpiarlos y transformarlos en un formato que Lex o un modelo de fine-tuning puedan entender.
- **Implementación**: Un **`ProcessingStep`** de SageMaker que ejecuta un script de Python (usando Scikit-learn o Pandas).
- **Lógica del Script**:
    - Listar y leer los archivos `.json` del bucket `mi-cafeteria-chatbot-logs/logs/`.
    - Extraer el `userInput` y el `intent` (si fue identificado por Lex).
    - **Filtrado Clave**:
        - Descartar interacciones con baja confianza o que fueron directamente al *fallback*.
        - Identificar nuevas *utterances* para intents existentes.
        - **Detección de Nuevos Intents**: Agrupar semánticamente las *utterances* que cayeron en el *fallback* para sugerir la creación de nuevos intents (ej. si muchos usuarios preguntan por "wifi", podría ser un nuevo intent `PreguntarWifi`).
    - Formatear los datos en el formato requerido para un *build* de Lex o para el fine-tuning de un LLM.
    - Dividir los datos en conjuntos de entrenamiento y validación.

### Paso 2: Reentrenamiento del Modelo
- **Propósito**: Entrenar una nueva versión del modelo con los datos preprocesados.
- **Implementación**:
    - **Para Lex**: Usar el SDK de AWS (Boto3) en un **`TrainingStep`** para iniciar un nuevo *build* del bot de Lex con el conjunto de datos actualizado. Esto se hace mediante programación, no es un *training job* tradicional de SageMaker.
    - **Para Bedrock/SageMaker LLM**: Si se usa un modelo propio, este sería un **`TuningStep`** para realizar el *fine-tuning* del modelo de lenguaje con los nuevos ejemplos de conversación.

### Paso 3: Evaluación del Modelo
- **Propósito**: Comparar objetivamente el rendimiento del nuevo modelo con el modelo actual en producción.
- **Implementación**: Un **`ProcessingStep`** que ejecuta un script de evaluación.
- **Lógica del Script**:
    - Tomar el conjunto de datos de validación (que el modelo no ha visto).
    - Enviar cada *utterance* de validación tanto al nuevo modelo como al modelo antiguo.
    - Comparar las métricas clave: precisión, F1-score por intent, etc.
    - Generar un informe de evaluación (ej. `evaluation.json`).

### Paso 4: Despliegue Condicional
- **Propósito**: Desplegar el nuevo modelo solo si es mejor que el anterior.
- **Implementación**: Un **`ConditionStep`**.
- **Lógica del Paso**:
    - Lee el resultado del informe de evaluación del paso anterior.
    - Si `new_model_accuracy > old_model_accuracy`, procede al paso de despliegue.
    - De lo contrario, finaliza la canalización y notifica a un administrador (ej. vía SNS).

### Paso 5: Despliegue del Modelo
- **Propósito**: Poner en producción la nueva versión del modelo.
- **Implementación**: Un **`LambdaStep`** o un paso que use Boto3.
- **Lógica**:
    - **Para Lex**: Actualizar el alias del bot para que apunte a la nueva versión del modelo que se acaba de construir y validar.
    - **Para un LLM**: Crear un nuevo *endpoint* de SageMaker o actualizar uno existente con el nuevo artefacto del modelo.

## 3. Creación y Ejecución de la Canalización

1.  **Navegar a SageMaker**: En la [Consola de AWS](https://aws.amazon.com/console/), busca y selecciona "Amazon SageMaker".
2.  **Crear un Rol de IAM para SageMaker**: SageMaker necesitará permisos para acceder a S3, Lex, y otros servicios de AWS. Crea un rol con las políticas gestionadas `AmazonSageMakerFullAccess` y añade los permisos específicos para interactuar con Lex.
3.  **Usar SageMaker Studio**: Es el entorno de desarrollo ideal para construir estas canalizaciones.
    - Abre SageMaker Studio.
    - Crea un nuevo Notebook de Python.
    - Usando el **SageMaker SDK para Python**, define cada uno de los pasos descritos anteriormente.
4.  **Definir la Canalización**:
    - Escribe el código Python que define la secuencia de pasos y las dependencias entre ellos.
5.  **Crear y Ejecutar**:
    - Sube la definición de la canalización a SageMaker.
    - Puedes ejecutarla manualmente desde el Studio para probarla.
6.  **Automatizar la Ejecución**:
    - Para ejecutarla periódicamente, usa **Amazon EventBridge (CloudWatch Events)** para crear una regla que inicie la canalización según una programación (ej. `cron(0 12 */15 * ? *)` para ejecutarla cada 15 días a las 12:00).

Esta canalización de MLOps es una inversión inicial significativa, pero es la clave para que el chatbot mejore continuamente y no se vuelva obsoleto.
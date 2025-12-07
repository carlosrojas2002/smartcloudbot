# Pipeline de Reentrenamiento para Amazon Lex con SageMaker

Este documento proporciona una guía detallada para configurar y ejecutar un pipeline de MLOps con AWS SageMaker. El objetivo de este pipeline es automatizar el proceso de reentrenamiento de un bot de Amazon Lex V2 utilizando nuevas utterances (frases de usuario) almacenadas en Amazon S3.

## Propósito

Cuando un bot de Amazon Lex no entiende una frase de un usuario, la registra como un `FallbackIntent`. Analizar estas frases y reincorporarlas al bot es crucial para mejorar su precisión. Este pipeline automatiza los siguientes pasos:

1.  **Extracción y Preprocesamiento**: Lee las utterances desde un archivo CSV en un bucket de S3.
2.  **Empaquetado**: Transforma y empaqueta las utterances en el formato ZIP requerido por la API de importación de Lex V2.
3.  **Importación a Lex**: Llama a la API de Amazon Lex para iniciar un trabajo de importación con el archivo ZIP generado, añadiendo las nuevas utterances al `FallbackIntent` y mejorando así el modelo de lenguaje natural del bot.

## Prerrequisitos

Antes de ejecutar el pipeline, asegúrate de tener lo siguiente:

1.  **AWS CLI y SDK de Python (Boto3)**: Configuradas en tu entorno de desarrollo con las credenciales adecuadas.
2.  **Un Bucket de S3**: Donde se almacenarán los datos de entrada (utterances) y los artefactos de salida del pipeline.
3.  **Un Bot de Amazon Lex V2**: El bot que deseas reentrenar. Necesitarás su ID y el ID del locale (por ejemplo, `es_ES`).
4.  **Un archivo de utterances**: Un archivo CSV subido a tu bucket de S3 con las nuevas utterances.

## Configuración del Rol de Ejecución de IAM

El pipeline de SageMaker necesita un rol de IAM con permisos específicos para acceder a S3, Lex y otros servicios de AWS.

**Pasos para crear el rol:**

1.  **Ve a la consola de IAM en AWS.**
2.  **Crea un nuevo rol.**
    *   Para el servicio que usará este rol, selecciona **SageMaker**.
3.  **Adjunta Políticas:**
    *   Busca y añade la política administrada por AWS llamada `AmazonSageMakerFullAccess`.
4.  **Crea una política personalizada:**
    *   Ve a la sección de "Políticas" y haz clic en "Crear política".
    *   Selecciona la pestaña **JSON**.
    *   Copia el contenido del archivo `sagemaker-execution-role-policy.json` que se encuentra en este mismo directorio.
    *   **Importante**: Antes de guardar, reemplaza los siguientes placeholders en el JSON con tus valores específicos:
        *   `mi-bucket-de-datos-aqui`: El nombre de tu bucket de S3.
        *   `mi-bot-id-aqui`: El ID de tu bot de Lex.
        *   `mi-region-aws-aqui`: La región de AWS donde operan tus servicios (ej. `us-east-1`).
        *   `<ACCOUNT_ID>`: Tu ID de cuenta de AWS.
    *   Nombra la política (ej. `SageMakerLexRetrainingPolicy`) y créala.
5.  **Adjunta la política personalizada a tu rol:**
    *   Vuelve al rol que creaste, ve a la pestaña de "Permisos" y adjunta la política que acabas de crear.
6.  **Copia el ARN del rol**: Lo necesitarás para ejecutar el script del pipeline.

## Ejecución del Pipeline

Para ejecutar el pipeline, sigue estos pasos:

1.  **Instala las dependencias de Python:**
    ```bash
    pip install "sagemaker~=2.0" boto3
    ```
    *Nota: Es importante usar la versión 2.x de sagemaker para asegurar la compatibilidad.*

2.  **Actualiza los parámetros en `pipeline.py`:**
    *   Abre el archivo `pipeline.py` y modifica los valores de los parámetros en la sección `if __name__ == "__main__":`. Reemplaza los placeholders con tus datos.

3.  **Ejecuta el script desde este directorio:**
    ```bash
    cd src/backend/lex-retraining-pipeline
    python3 pipeline.py
    ```

## Descripción de los Parámetros del Pipeline

Estos son los parámetros que deberás configurar en el script `pipeline.py`:

*   `input_data_uri`: La ruta S3 completa (`s3://...`) a tu archivo CSV de utterances.
*   `output_data_uri`: La ruta S3 donde el pipeline guardará los artefactos de salida (como el archivo ZIP para Lex).
*   `sagemaker_role_arn`: El ARN del rol de IAM que creaste en los pasos anteriores.
*   `bot_id`: El ID de tu bot de Amazon Lex V2.
*   `bot_locale_id`: El ID del locale que deseas actualizar (ej. `es_ES`, `en_US`).
*   `aws_region`: La región de AWS donde se ejecutará el pipeline.

# Guía de Configuración de Almacenamiento

Para que el chatbot pueda aprender y para tener un registro de las conversaciones, es fundamental configurar un almacenamiento persistente. Usaremos Amazon DynamoDB para un acceso rápido y estructurado a los logs y Amazon S3 para un almacenamiento a largo plazo, ideal para el reentrenamiento.

## 1. Creación de la Tabla en Amazon DynamoDB

DynamoDB almacenará cada interacción individualmente, permitiendo búsquedas y análisis en tiempo real si fuera necesario.

1.  **Navegar a DynamoDB**: En la [Consola de AWS](https://aws.amazon.com/console/), busca y selecciona "DynamoDB".
2.  **Crear Tabla**:
    *   Haz clic en **"Create table"**.
    *   **Table name**: `chatbot_conversations`. (Asegúrate de que este nombre coincida con el que pones en las variables de entorno de la Lambda).
    *   **Partition key**: `interactionId`.
    *   **Type**: Selecciona **"String"**.
    *   **Table settings**: Deja seleccionada la opción **"Default settings"**. Esto provisionará la tabla en modo *On-demand*, que es ideal para cargas de trabajo impredecibles como las de un chatbot.
    *   Haz clic en **"Create table"**.

La tabla estará lista en unos segundos. La función Lambda utilizará el `interactionId` (un UUID generado en el código) como clave principal para garantizar que cada entrada sea única.

## 2. Creación del Bucket en Amazon S3

S3 servirá como el repositorio de datos históricos. La canalización de SageMaker leerá los logs desde aquí para el reentrenamiento.

1.  **Navegar a S3**: En la [Consola de AWS](https://aws.amazon.com/console/), busca y selecciona "S3".
2.  **Crear Bucket**:
    *   Haz clic en **"Create bucket"**.
    *   **Bucket name**: `mi-cafeteria-chatbot-logs-`. **Importante**: Los nombres de los buckets de S3 deben ser únicos a nivel mundial. Te recomiendo usar un nombre como `mi-proyecto-recurso-nombre-123456789` donde los números son tu ID de cuenta de AWS.
    *   **AWS Region**: Elige la misma región en la que estás desplegando el resto de tus recursos (ej. `us-east-1`).
    *   **Block Public Access settings for this bucket**: Deja la opción **"Block all public access"** marcada. No necesitamos que los logs sean públicos.
    *   **Bucket Versioning**: Es una buena práctica habilitarlo. Selecciona **"Enable"**.
    *   El resto de las opciones pueden dejarse con sus valores por defecto.
    *   Haz clic en **"Create bucket"**.
3.  **Crear una Carpeta (Opcional pero Recomendado)**:
    *   Una vez creado el bucket, entra en él.
    *   Haz clic en **"Create folder"**.
    *   **Folder name**: `logs`.
    *   Haz clic en **"Create folder"**.
    *   La función Lambda está configurada para escribir los objetos dentro de esta carpeta, lo que ayuda a mantener el bucket organizado.

Con DynamoDB y S3 configurados, la función Lambda podrá registrar cada conversación de manera dual: un registro estructurado para acceso rápido y un archivo JSON en S3 para el análisis de datos a gran escala y el reentrenamiento del modelo. Asegúrate de haber actualizado la política de IAM y las variables de entorno de la Lambda con los nombres exactos de estos recursos.
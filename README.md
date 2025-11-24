# 🤖 SmartCloudBot - Asistente de Soporte Cloud con IA

![AWS](https://img.shields.io/badge/AWS-Serverless-orange)
![Python](https://img.shields.io/badge/Python-3.9-blue)
![Status](https://img.shields.io/badge/Status-Completed-green)

**SmartCloudBot** es un asistente virtual inteligente desplegado en la nube de AWS. Su objetivo principal es automatizar la atención al cliente respondiendo preguntas frecuentes (FAQ) sobre servicios, precios y horarios, con capacidad de operar en múltiples idiomas.

## 📋 Características Principales

* **🧠 Inteligencia Conversacional:** Utiliza **Amazon Lex V2** para entender la intención del usuario y procesar lenguaje natural.
* **🌍 Soporte Multi-idioma:** Capacidad de atender usuarios en **Español e Inglés**, realizando traducciones automáticas en tiempo real (Backend logic).
* **☁️ Arquitectura 100% Serverless:** No requiere administración de servidores. Utiliza AWS Lambda y API Gateway.
* **💾 Base de Conocimiento Dinámica:** Las respuestas no están "quemadas" en el código, sino que se consultan dinámicamente desde una base de datos **DynamoDB**.
* **📊 Persistencia y Logs:** Guarda un historial detallado de cada conversación para auditoría y análisis.
* **🖥️ Interfaz Web Moderna:** Frontend ligero alojado en **Amazon S3**.

## 🏗️ Arquitectura del Sistema

El sistema sigue un patrón de arquitectura orientada a eventos.

![Diagrama de Arquitectura](architecture/ProyectoServidores.drawio.png)

*(Puedes ver el detalle técnico en la carpeta `/architecture`)*

## 🛠️ Tecnologías Utilizadas

| Componente | Servicio AWS | Función |
| :--- | :--- | :--- |
| **Frontend** | Amazon S3 | Alojamiento de sitio web estático (HTML/JS). |
| **API / Entrypoint** | Amazon API Gateway | API HTTP pública y segura con CORS habilitado. |
| **Orquestador** | AWS Lambda (Python) | Manejo de tráfico web, detección de idioma y traducción. |
| **NLU / Bot** | Amazon Lex V2 | Comprensión del lenguaje natural y gestión de sesiones. |
| **Lógica de Negocio** | AWS Lambda (Python) | Cumplimiento (Fulfillment), análisis de sentimiento y conexión a BD. |
| **Base de Datos** | Amazon DynamoDB | Tablas para FAQ (KnowledgeBase) y Logs de sesión. |

## 🚀 Instalación y Despliegue

Este proyecto se despliega utilizando la consola de AWS. Pasos generales:

1.  **Base de Datos:** Crear tablas en DynamoDB (`FAQKnowledgeBase` y `ChatSessionLogs`).
2.  **Lógica:** Desplegar funciones Lambda (`Orchestrator` y `Fulfillment`) con el código fuente en `/src/backend`.
3.  **Bot:** Importar y construir el bot en Amazon Lex V2 conectado a la Lambda de Fulfillment.
4.  **API:** Configurar API Gateway con integración a la Lambda Orquestadora.
5.  **Frontend:** Subir el archivo `index.html` a un bucket de S3 con permisos de lectura pública.

## 📂 Estructura del Proyecto

```text
smartcloudbot/
├── architecture/       # Diagramas de arquitectura y documentación técnica
├── src/
│   ├── backend/        # Código fuente Python de las Lambdas
│   └── frontend/       # Código HTML/JS de la interfaz web
├── docs/               # Documentación adicional
└── README.md           # Este archivo

🧪 Pruebas Realizadas
El sistema ha sido probado exitosamente con los siguientes flujos:

Consulta de precios en Español (Consulta directa a DB).

Consulta de precios en Inglés (Traducción → Consulta → Traducción).

Manejo de errores y Fallback intents.

📄 Licencia
Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE.txt para más detalles.
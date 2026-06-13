# Prototipo del Agente de Inteligencia Artificial Generativa (AIAG)

Este es el prototipo local en Streamlit diseñado para evaluar el efecto de un Coach de IA en el desarrollo de **GRIT** y **Liderazgo Positivo**, como parte del estudio doctoral de Vania Alemán (Universidad La Salle).

## Características del Prototipo

1. **Interfaz de Conversación Limpia:** Diseñada para estudiantes universitarios.
2. **System Prompt Congelado:** El núcleo metodológico de coaching (modelo de Duckworth para GRIT y Cameron para Liderazgo Positivo) está programado de forma fija en la aplicación.
3. **Filtro de Seguridad Local:** Un script detecta instantáneamente palabras clave de crisis emocional (suicidio, autolesión, etc.) y desvía la conversación hacia la **Línea de la Vida (800 911 2000)** sin llamar a la inteligencia artificial.
4. **Registro de Conversaciones (Logs):** Almacena automáticamente cada mensaje, respuesta y disparador de seguridad en un archivo local llamado `chat_logs.csv` para tu posterior análisis estadístico.
5. **Modo Dual:** Funciona en "Modo Simulación" (sin internet/sin API Key) para pruebas rápidas de interfaz y seguridad, o en "Modo Real" con la API de Gemini.

---

## Instrucciones para Ejecutar Localmente

### Prerrequisitos
Asegúrate de tener instalado Python 3.9 o superior en tu equipo.

### Paso 1: Instalar dependencias
Abre una terminal en esta carpeta y ejecuta:
```bash
pip install -r requirements.txt
```

### Paso 2: Iniciar la aplicación
Ejecuta el siguiente comando en la terminal:
```bash
streamlit run app.py
```
La aplicación se abrirá automáticamente en tu navegador web (usualmente en `http://localhost:8501`).

---

## Cómo obtener tu Gemini API Key (Gratis)
Para usar el "Modo Real":
1. Ve a [Google AI Studio](https://aistudio.google.com/).
2. Inicia sesión con tu cuenta de Google.
3. Haz clic en **"Get API key"** (Obtener clave de API).
4. Crea una clave en un proyecto nuevo o existente.
5. Copia la clave y pégala en la barra lateral de la aplicación de Streamlit.

---

## Archivo de Logs (`chat_logs.csv`)
Cada vez que interactúes con el chat, se generará o actualizará el archivo `chat_logs.csv` en esta misma carpeta. Este archivo contiene:
* **timestamp:** Fecha y hora.
* **student_id:** Identificador asignado (por ejemplo, `EST-001` o `EST-002` para el grupo de estudio).
* **mode:** Si se usó simulación o API de Gemini.
* **user_message:** Lo que escribió el estudiante.
* **ai_response:** Lo que respondió la IA o la alerta de seguridad.
* **safety_triggered:** `True` si se activó la alerta de la Línea de la Vida, `False` en caso contrario.

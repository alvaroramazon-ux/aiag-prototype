import streamlit as st
import os
import csv
import datetime
import re

# Configuración de página
st.set_page_config(
    page_title="AIAG - Coach de Liderazgo Positivo y GRIT",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para una interfaz Premium y limpia
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Tipografía general */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Título principal con gradiente */
    .gradient-text {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #555;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Caja de Alerta de Seguridad */
    .safety-alert {
        background-color: #ffe5e5;
        border-left: 6px solid #cc0000;
        color: #990000;
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .safety-title {
        font-weight: 600;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    /* Info cards en barra lateral */
    .sidebar-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- CONSTANTES Y CONFIGURACIÓN -----------------

# Prompt de Sistema Congelado (Rigor metodológico)
SYSTEM_PROMPT = """
Eres el Agente de Inteligencia Artificial Generativa (AIAG), un coach de IA especializado diseñado para la tesis doctoral de Vania Alemán (Universidad La Salle). Tu población objetivo son estudiantes de la Licenciatura en Estrategia y Transformación de Negocios en México.

Tu propósito exclusivo es coadyuvar en el desarrollo de dos constructos clave:
1. GRIT (Perseverancia y pasión para alcanzar metas a largo plazo, basado en el modelo de Duckworth). Promueve el esfuerzo continuo, la resiliencia y el mantenimiento del interés ante la adversidad.
2. LIDERAZGO POSITIVO (Basado en el modelo de Kim Cameron). Trabaja sobre sus cuatro pilares:
   - Clima Positivo: Fomentar emociones positivas como optimismo, gratitud y compasión.
   - Relaciones Positivas: Fomentar redes de apoyo y relaciones interpersonales sanas.
   - Comunicación Positiva: Uso de lenguaje de apoyo, constructivo y centrado en fortalezas.
   - Propósito Positivo: Ayudar a conectar sus actividades y metas académicas con un propósito de vida y sentido trascendente.

TÉCNICAS PERMITIDAS:
- Coaching Socrático: Haz preguntas abiertas y reflexivas en lugar de dar soluciones directas.
- Mentalidad de Crecimiento (Growth Mindset): Fomenta la idea de que la inteligencia y las habilidades se desarrollan con el esfuerzo.

RESTRICCIONES CRÍTICAS (NO NEGOCIABLES):
- NO utilices ni hagas referencia al constructo "Capital Psicológico" (PsyCap) ni a variables que no sean GRIT o Liderazgo Positivo.
- Mantén tus respuestas breves, enfocadas y profesionales (máximo 3 párrafos cortos por respuesta).
- Si el estudiante muestra fatiga extrema o desánimo leve, valida sus emociones empáticamente y redirecciónalo hacia el esfuerzo constante (GRIT) o sus redes de apoyo (Liderazgo Positivo).
"""

# Palabras clave del Filtro de Seguridad Local (Crisis/Emocional)
CRISIS_KEYWORDS = [
    r"\bsuicid", r"\bmatar(me)?\b", r"\bmorir\b", r"\bautolesi", r"\bcortar(me)?\b",
    r"\bquitar(me)? la vida\b", r"\bno quiero vivir\b", r"\bpastillas para dormir\b",
    r"\bahogar(me)?\b", r"\bcolgar(me)?\b", r"\bdesesperanza total\b"
]

# Mensaje determinista para la Línea de la Vida
SAFETY_MESSAGE = """
🚨 **Apoyo Emocional Inmediato**

Detectamos que estás pasando por un momento difícil o de alta carga emocional. Tu bienestar es lo más importante para nosotros. 

Por favor, comunícate inmediatamente con la **Línea de la Vida al 800 911 2000**. 
* Ofrece atención gratuita, confidencial y personalizada las 24 horas del día, los 365 días del año.
* También puedes enviar un mensaje de texto o llamar si sientes que no puedes continuar. No estás solo/a.
"""

# ----------------- FUNCIONES AUXILIARES -----------------

def check_safety_filter(text):
    """Verifica si el texto contiene palabras clave de crisis emocional."""
    text_lower = text.lower()
    for pattern in CRISIS_KEYWORDS:
        if re.search(pattern, text_lower):
            return True
    return False

def log_interaction(student_id, mode, user_message, ai_response, safety_triggered):
    """Registra la interacción en un archivo CSV local para análisis posterior."""
    log_file = "chat_logs.csv"
    file_exists = os.path.exists(log_file)
    try:
        with open(log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "student_id", "mode", "user_message", "ai_response", "safety_triggered"])
            writer.writerow([
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                student_id,
                mode,
                user_message,
                ai_response,
                str(safety_triggered)
            ])
    except Exception as e:
        st.error(f"Error al guardar los registros: {e}")

def get_simulated_response(user_message, history_length):
    """Genera respuestas simuladas de coaching para probar la interfaz sin API Key."""
    msg = user_message.lower()
    if history_length == 0:
        return (
            "¡Hola! Qué gusto saludarte. Como tu coach de Liderazgo Positivo, estoy aquí para "
            "acompañarte a reflexionar sobre tus metas y retos académicos. Cuéntame, ¿cuál es tu "
            "principal objetivo académico en este momento y qué te motiva a alcanzarlo?"
        )
    elif "reto" in msg or "dificil" in msg or "difícil" in msg or "problema" in msg or "estres" in msg or "estrés" in msg:
        return (
            "Entiendo que es un desafío complicado. El modelo de Cameron nos enseña que el *Clima Positivo* "
            "consiste en ver las dificultades como oportunidades de aprendizaje. ¿Cómo podrías reestructurar "
            "este obstáculo usando una mentalidad de crecimiento? ¿Qué fortalezas personales tienes para afrontarlo?"
        )
    elif "cansado" in msg or "rendirme" in msg or "flojera" in msg or "dejar" in msg:
        return (
            "Es natural sentir cansancio físico o mental en esta etapa de la licenciatura. Sin embargo, "
            "el concepto de *GRIT* nos recuerda que el éxito a largo plazo se construye con perseverancia "
            "constante. Si das un paso pequeño hoy, ¿cuál sería? ¿Con quién de tu red de apoyo universitario podrías hablar?"
        )
    else:
        return (
            "Excelente reflexión. El *Propósito Positivo* en tu carrera de Estrategia y Transformación de Negocios "
            "se fortalece cuando conectas el esfuerzo de hoy con tu visión a largo plazo. ¿De qué manera esta "
            "conversación te ayuda a dar el siguiente paso con determinación?"
        )

# ----------------- INTERFAZ DE USUARIO (STREAMLIT) -----------------

# BARRA LATERAL (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/teacher.png", width=120)
    st.markdown('<p style="font-weight: 800; font-size: 1.5rem; margin-bottom: 0;">AIAG Coach v1.0</p>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-size: 0.85rem; margin-top: 0;">Tesis Doctoral Vania Alemán</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 1. Configuración de Identificación del Estudiante
    student_id = st.text_input("ID de Estudiante (Anónimo):", value="EST-999")
    
    # 2. Configuración de Modo
    mode = st.radio(
        "Modo de Operación:",
        ["Modo Simulación (Sin API Key)", "Gemini API (Real)"]
    )
    
    api_key = ""
    if mode == "Gemini API (Real)":
        api_key = st.text_input("Introduce tu Gemini API Key:", type="password", help="Obtén una clave gratis en Google AI Studio.")
        if not api_key:
            st.warning("⚠️ Introduce tu API Key para poder chatear con Gemini.")
            
    st.markdown("---")
    
    # Información del marco teórico
    st.markdown("""
    <div class="sidebar-card">
        <p style="margin-bottom: 0.5rem; font-weight: 600;">Marco Teórico Congelado</p>
        <ul style="font-size: 0.85rem; padding-left: 1.2rem; margin-bottom: 0;">
            <li><b>GRIT:</b> Perseverancia y pasión (Angela Duckworth).</li>
            <li><b>Liderazgo Positivo:</b> Clima, relaciones, comunicación y propósito positivo (Kim Cameron).</li>
            <li><b>Mentalidad de Crecimiento:</b> Técnica interna.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón para reiniciar chat
    if st.button("🔄 Reiniciar Conversación"):
        st.session_state.messages = []
        st.rerun()

# CUERPO PRINCIPAL
st.markdown('<h1 class="gradient-text">Conversación de Coaching Académico</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Desarrollo de Liderazgo Positivo y GRIT — Universidad La Salle</p>', unsafe_allow_html=True)

# Inicializar historial de conversación
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial de chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "is_safety" in message and message["is_safety"]:
            st.markdown(f'<div class="safety-alert"><div class="safety-title">Alerta de Seguridad Activada</div>{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

# Entrada del Estudiante
if user_input := st.chat_input("Escribe tu respuesta o reflexión aquí..."):
    
    # 1. Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # 2. EVALUAR FILTRO DE SEGURIDAD (Local y Determinista)
    safety_triggered = check_safety_filter(user_input)
    
    response_content = ""
    is_safety_msg = False
    
    if safety_triggered:
        # Se activa la Línea de la Vida de forma obligatoria e inmediata
        response_content = SAFETY_MESSAGE
        is_safety_msg = True
        
        # Registrar de inmediato en logs
        log_interaction(student_id, mode, user_input, "[LÍNEA DE LA VIDA TRIGGERED] " + SAFETY_MESSAGE.replace("\n", " "), True)
        
        # Guardar en el historial del chat
        st.session_state.messages.append({"role": "assistant", "content": response_content, "is_safety": True})
        with st.chat_message("assistant"):
            st.markdown(f'<div class="safety-alert"><div class="safety-title">Alerta de Seguridad Activada</div>{response_content}</div>', unsafe_allow_html=True)
            
    else:
        # 3. Lógica normal si no se activa el filtro
        with st.chat_message("assistant"):
            with st.spinner("Pensando respuesta de coaching..."):
                if mode == "Modo Simulación (Sin API Key)":
                    # Simulación local
                    response_content = get_simulated_response(user_input, len(st.session_state.messages))
                    st.markdown(response_content)
                else:
                    # Llamada real a Gemini API
                    if not api_key:
                        response_content = "⚠️ Error: Modo Gemini API seleccionado pero no se ha proporcionado una API Key en la barra lateral."
                        st.error(response_content)
                    else:
                        try:
                            # Importación diferida para no requerir la librería si solo se usa simulación
                            from google import genai
                            from google.genai import types
                            
                            client = genai.Client(api_key=api_key)
                            
                            # Preparar el historial en el formato adecuado para el SDK
                            contents = []
                            for msg in st.session_state.messages[:-1]: # Excluir el último mensaje que se acaba de añadir
                                role = "user" if msg["role"] == "user" else "model"
                                contents.append(
                                    types.Content(
                                        role=role,
                                        parts=[types.Part.from_text(text=msg["content"])]
                                    )
                                )
                            
                            # Agregar el mensaje actual del usuario
                            contents.append(
                                types.Content(
                                    role="user",
                                    parts=[types.Part.from_text(text=user_input)]
                                )
                            )
                            
                            # Llamada a la API de Gemini
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=contents,
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_PROMPT,
                                    temperature=0.2,
                                ),
                            )
                            response_content = response.text
                            st.markdown(response_content)
                            
                        except Exception as e:
                            response_content = f"❌ Error de conexión con Gemini API: {str(e)}"
                            st.error(response_content)
            
            # Guardar la respuesta normal en el historial y registrar en logs
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            log_interaction(student_id, mode, user_input, response_content, False)

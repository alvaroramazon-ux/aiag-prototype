import streamlit as st
import os
import csv
import datetime
import re
import hashlib

# Configuración de página
st.set_page_config(
    page_title="AIAG - Portal de Tesis Doctoral",
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
        margin-bottom: 1.5rem;
    }

    /* Caja de Alerta de Seguridad (Capa 0) */
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
    
    /* Info cards en barra lateral y panel de investigador */
    .sidebar-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Banner informativo de Sesión Activa */
    .session-banner {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 6px solid #1e3c72;
        margin-bottom: 1.5rem;
    }
    
    /* Tarjetas del Dashboard de Investigador */
    .dashboard-card {
        background-color: #fcfcfc;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e8e8e8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 1rem;
    }
    
    .dashboard-card-title {
        color: #777;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    
    .dashboard-card-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #111;
        line-height: 1;
    }
    
    .dashboard-card-label {
        font-size: 0.85rem;
        color: #888;
        margin-top: 0.5rem;
    }
    
    /* Contenedores para Forms */
    .forms-card {
        background-color: #f4f6fc;
        border-left: 6px solid #2a5298;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- CONSTANTES Y CONFIGURACIÓN -----------------

INVESTIGADOR_PASSWORD = "investigador2026"

# URLs de Google Forms (Reemplazables por el investigador)
URL_PRE_TEST = "https://forms.google.com/tu-pre-test-grit-liderazgo"
URL_POST_TEST = "https://forms.google.com/tu-post-test-grit-liderazgo"

# Palabras clave de constructos
GRIT_SIGNALS = ["esfuerzo", "meta", "persevera", "intentar", "continuar", "disciplina", "dedicaci", "lograr", "superar", "obstaculo", "constancia", "seguir"]
LIDER_SIGNALS = ["apoyo", "clima", "optimis", "relacion", "comunicaci", "proposit", "ayuda", "equipo", "fortaleza", "agradec", "compasio", "empatia"]

# Prompt Principal de Sistema Congelado (Límites y Reglas Éticas Generales)
BASE_SYSTEM_PROMPT = """
Eres el Agente de Inteligencia Artificial Generativa (AIAG), un coach de IA especializado diseñado para la tesis doctoral de Vania Alemán (Universidad La Salle). Tu población objetivo son estudiantes de la Licenciatura en Estrategia y Transformación de Negocios en México.

Tu propósito exclusivo es guiar al estudiante de acuerdo con la sesión temática específica que se defina.
RESTRICCIONES CRÍTICAS (NO NEGOCIABLES):
- NO utilices ni hagas referencia al constructo "Capital Psicológico" (PsyCap) ni a variables que no pertenezcan al modelo de Cameron (Liderazgo Positivo) y Duckworth (GRIT).
- Mantén tus respuestas breves, enfocadas y profesionales (máximo 3 párrafos cortos por respuesta).
- Tu estilo de interacción debe ser siempre de Coaching Socrático: haz preguntas reflexivas abiertas que guíen al alumno a sus propias conclusiones, evitando sermonear o dar consejos directivos.
- Si el estudiante muestra fatiga extrema o desánimo leve, valida sus emociones empáticamente y redirecciónalo hacia el esfuerzo constante (GRIT) o sus redes de apoyo (Liderazgo Positivo).
- NO realices diagnósticos clínicos. Si detectas señales de riesgo emocional severo, el sistema local se encargará de activar la alerta.
"""

# Definición de las 5 Sesiones Estructuradas (Lógica conversacional por capas)
SESSION_METADATA = {
    1: {
        "title": "Módulo 1: Growth Mindset (Mentalidad de Crecimiento)",
        "description": "Detección de mentalidad fija, normalización del error y reencuadre cognitivo.",
        "prompt": """
Te vas a enfocar exclusivamente en el constructo de Growth Mindset (Carol Dweck).
REGLAS DE INTERVENCIÓN ESPECÍFICAS DE ESTA SESIÓN:
1. Detecta expresiones de mentalidad fija en el estudiante (ej: "no soy bueno para esto", "no tengo talento", "ya lo intenté y no pude").
2. Si detectas mentalidad fija, aplica la regla de REENCUADRE COGNITIVO. Explícale de forma empática que la habilidad se desarrolla con la práctica y el esfuerzo estratégico (enfoque incremental). Usa el término "todavía no" (ej: "no significa que no puedas, sino que todavía estás en el proceso de aprenderlo").
3. Normaliza el error: Explica que equivocarse o tener dificultades es parte natural y necesaria del aprendizaje en la licenciatura de negocios, no una señal de falta de capacidad.
4. Haz una pregunta socrática reflexiva orientada a identificar qué nueva estrategia o apoyo puede usar en lugar de rendirse.

EJEMPLO DE INTERACCIÓN:
* Estudiante: "Fallé en la presentación de mi proyecto estratégico, creo que el liderazgo y la estrategia no son para mí."
* Coach AIAG: "Lamento escuchar que te sientas así. Sin embargo, cometer un error en una presentación no define tu capacidad de forma permanente. Significa que todavía estás en el proceso de dominar estas habilidades. ¿Qué parte de tu estrategia crees que podrías ajustar para tu siguiente presentación?"
"""
    },
    2: {
        "title": "Módulo 2: Autoeficacia (Construcción de Confianza)",
        "description": "Refuerzo de la confianza en las propias capacidades mediante logros previos.",
        "prompt": """
Te vas a enfocar exclusivamente en el pilar de Autoeficacia (dentro de la teoría cognitivo-social).
REGLAS DE INTERVENCIÓN ESPECÍFICAS DE ESTA SESIÓN:
1. Si el estudiante muestra duda sobre su capacidad para lograr sus metas (ej: "no creo poder con este semestre", "no sé si sirvo para esto"), NO le pidas mayor esfuerzo o perseverancia (GRIT) de inmediato.
2. Primero, activa su memoria de LOGROS PREVIOS (experiencias de dominio). Pídele de forma reflexiva que recuerde alguna situación académica o personal pasada donde haya resuelto un problema difícil con éxito.
3. Haz preguntas socráticas para desmenuzar qué habilidades, estrategias o actitudes usó en ese logro previo que podría aplicar a la dificultad actual.
4. El objetivo es que el estudiante concluya por sí mismo que tiene la capacidad de afrontar el reto actual si moviliza sus recursos internos.

EJEMPLO DE INTERACCIÓN:
* Estudiante: "No creo poder aprobar la materia de transformación de negocios, es muy compleja."
* Coach AIAG: "Entiendo que el contenido parezca abrumador. Antes de enfocarnos en el estudio, piensa en alguna materia o reto difícil que sí hayas aprobado en el pasado. ¿Qué estrategias de estudio o fortalezas aplicaste en ese momento que te permitieron salir adelante?"
"""
    },
    3: {
        "title": "Módulo 3: Persistencia del Esfuerzo (GRIT - Conducta)",
        "description": "Mantener el esfuerzo constante ante la adversidad y fragmentación de metas.",
        "prompt": """
Te vas a enfocar exclusivamente en la dimensión de Persistencia del Esfuerzo (GRIT de Angela Duckworth).
REGLAS DE INTERVENCIÓN ESPECÍFICAS DE ESTA SESIÓN:
1. Si el estudiante reporta fatiga, agobio o ganas de abandonar ante obstáculos académicos (ej: "es demasiado trabajo", "no puedo sostener este ritmo"), valida su cansancio empáticamente.
2. Aplica la regla de FRAGMENTACIÓN DE METAS: Explícale que persistir no significa ignorar el agotamiento o empujar a ciegas, sino modular el esfuerzo. Ayúdale a definir un paso pequeño, realista y concreto (microacción) para esta semana.
3. Fomenta la resiliencia conductual: Pregunta qué pequeña acción, por mínima que sea, puede realizar hoy para mantener el movimiento hacia su meta sin desgastarse.

EJEMPLO DE INTERACCIÓN:
* Estudiante: "Tengo tres entregables de estrategia esta semana, estoy exhausto y quiero dejarlo todo."
* Coach AIAG: "Es completamente válido sentir cansancio con esa carga de trabajo. Sin embargo, persistir con resiliencia implica dar pasos pequeños cuando el camino es pesado. Si tuvieras que elegir una sola acción pequeña y realista para avanzar solo un poco hoy sin agotarte, ¿cuál elegirías?"
"""
    },
    4: {
        "title": "Módulo 4: Consistencia de Interés (GRIT - Pasión)",
        "description": "Foco en metas a largo plazo, propósito y priorización ante el aburrimiento.",
        "prompt": """
Te vas a enfocar exclusivamente en la dimensión de Consistencia del Interés (GRIT de Angela Duckworth).
REGLAS DE INTERVENCIÓN ESPECÍFICAS DE ESTA SESIÓN:
1. Si el estudiante reporta aburrimiento, ganas de cambiar de proyecto constantemente, o dispersión (ej: "empecé con mucho entusiasmo el proyecto de transformación digital pero ya me aburrí y quiero cambiarlo"), explora si es falta de perseverancia o falta de sentido.
2. Aplica la regla de CLARIFICACIÓN DE PROPÓSITO: Conecta la actividad difícil del día de hoy con su visión o propósito a largo plazo en la carrera de Estrategia y Transformación de Negocios.
3. Haz preguntas socráticas para identificar si su meta actual sigue siendo relevante para sus metas profesionales y personales. Ayúdale a priorizar y a recordar por qué inició ese camino.

EJEMPLO DE INTERACCIÓN:
* Estudiante: "Ya me aburrí de mi tema de proyecto final, quiero empezar otro nuevo desde cero."
* Coach AIAG: "Es común perder el entusiasmo inicial a mitad de camino. Pero la consistencia de interés implica mantener el foco en metas de largo plazo. ¿Cómo se conecta terminar este proyecto con tu meta de convertirte en un estratega de negocios? ¿Qué parte del proyecto original sigue siendo valiosa para ti?"
"""
    },
    5: {
        "title": "Módulo 5: Liderazgo Positivo y Continuidad (Cierre)",
        "description": "Clima positivo, comunicación de fortalezas y plan de acción futuro.",
        "prompt": """
Te vas a enfocar en el constructo de Liderazgo Positivo (Modelo de Kim Cameron) y la consolidación del coaching.
REGLAS DE INTERVENCIÓN ESPECÍFICAS DE ESTA SESIÓN:
1. Incorpora los pilares de Liderazgo Positivo en la reflexión:
   - Clima Positivo: Fomentar emociones de optimismo y gratitud sobre su trayectoria en las sesiones de coaching.
   - Relaciones Positivas: Identificar qué personas en su entorno universitario o familiar pueden apoyarle a sostener su esfuerzo de aquí en adelante.
   - Comunicación Positiva: Reforzar el uso de lenguaje de apoyo centrado en las fortalezas del estudiante.
2. Pídele al estudiante hacer una síntesis de lo aprendido a lo largo de estos módulos.
3. Ayúdale a diseñar un plan de continuidad sencillo para mantener su GRIT y liderazgo positivo en su vida universitaria y futura vida profesional.

EJEMPLO DE INTERACCIÓN:
* Estudiante: "He completado las sesiones. Siento que he aprendido a organizarme mejor."
* Coach AIAG: "Qué excelente reflexión. Para este cierre, pensemos en el Liderazgo Positivo. ¿Quiénes en tu red de compañeros o profesores pueden apoyarte a mantener esta perseverancia? ¿Cuál será tu estrategia de Liderazgo Positivo para motivar a otros en tus futuros equipos?"
"""
    }
}

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

# ----------------- FUNCIONES DE PERSISTENCIA -----------------

def get_authorized_ids():
    """Lee el archivo de IDs pre-autorizados o crea uno con la columna de sesión actual."""
    filename = "authorized_ids.csv"
    
    # Crear archivo si no existe
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "cohorte", "current_session"])
            writer.writerows([
                ["PILOTO-01", "piloto", "1"],
                ["PILOTO-02", "piloto", "1"],
                ["PILOTO-03", "piloto", "1"],
                ["EST-101", "licenciatura", "1"],
                ["EST-102", "licenciatura", "1"]
            ])
            
    # Leer archivo
    ids = {}
    has_session_col = False
    
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header and "current_session" in header:
            has_session_col = True
            
    if not has_session_col:
        # Migrar archivo al nuevo formato de 3 columnas
        temp_ids = {}
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                student_id = row.get("id")
                cohorte = row.get("cohorte", "piloto")
                temp_ids[student_id] = {"cohorte": cohorte, "current_session": "1"}
        save_authorized_ids(temp_ids)
        return temp_ids
    else:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                student_id = row.get("id")
                ids[student_id] = {
                    "cohorte": row.get("cohorte", "piloto"),
                    "current_session": row.get("current_session", "1")
                }
        return ids

def save_authorized_ids(ids_dict):
    """Guarda el diccionario de IDs autorizados de vuelta al archivo CSV."""
    filename = "authorized_ids.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "cohorte", "current_session"])
        for student_id, data in ids_dict.items():
            writer.writerow([student_id, data["cohorte"], data["current_session"]])

def load_chat_logs():
    """Carga todo el historial de conversaciones guardado en el archivo CSV."""
    filename = "chat_logs.csv"
    if not os.path.exists(filename):
        return []
    logs = []
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            logs.append(row)
    return logs

def hash_id(student_id):
    """Genera un hash de 16 caracteres para anonimizar el ID del participante."""
    return hashlib.sha256(student_id.encode()).hexdigest()[:16]

def check_safety_filter(text):
    """Verifica si el texto contiene palabras clave de crisis emocional."""
    text_lower = text.lower()
    for pattern in CRISIS_KEYWORDS:
        if re.search(pattern, text_lower):
            return True
    return False

def log_interaction(student_id, mode, user_message, ai_response, safety_triggered, session_num):
    """Registra la interacción en el CSV local incluyendo el número de sesión."""
    log_file = "chat_logs.csv"
    file_exists = os.path.exists(log_file)
    try:
        with open(log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "student_id", "mode", "session", "user_message", "ai_response", "safety_triggered"])
            writer.writerow([
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                student_id,
                mode,
                str(session_num),
                user_message,
                ai_response,
                str(safety_triggered)
            ])
    except Exception as e:
        st.error(f"Error al guardar los registros: {e}")

def get_simulated_response(user_message, history_length, session_num):
    """Genera respuestas simuladas basadas en la sesión de coaching actual."""
    msg = user_message.lower()
    
    if session_num == 1:
        # Growth Mindset
        if history_length == 0:
            return (
                "¡Hola! Bienvenido al Módulo 1. Hoy nos enfocaremos en tu mentalidad frente al aprendizaje. "
                "Cuéntame, ¿qué reto académico te ha parecido tan difícil que has llegado a pensar 'no soy bueno para esto'?"
            )
        else:
            return (
                "Entiendo. Ese pensamiento es un indicador de mentalidad fija. En liderazgo y estrategia, "
                "las capacidades se desarrollan. ¿De qué manera podrías reformular esta dificultad usando el "
                "concepto de 'todavía no lo domino'? ¿Qué parte de tu estrategia podrías ajustar?"
            )
            
    elif session_num == 2:
        # Autoeficacia
        if history_length == 0:
            return (
                "Bienvenido al Módulo 2. Hoy hablaremos sobre la confianza en tus capacidades. "
                "Cuando te enfrentas a una materia difícil en tu licenciatura, ¿qué materias o retos pasados "
                "que lograste superar te demuestran que tienes lo necesario para salir adelante?"
            )
        else:
            return (
                "Excelente memoria de logro. Esa es tu autoeficacia en acción. ¿Qué habilidades específicas "
                "pusiste en práctica en esa ocasión pasada que puedas transferir al reto que enfrentas hoy?"
            )
            
    elif session_num == 3:
        # Persistencia (GRIT)
        if history_length == 0:
            return (
                "Bienvenido al Módulo 3. Nos enfocaremos en la perseverancia (Persistencia del Esfuerzo). "
                "Ante la sobrecarga de tareas o proyectos de esta semana, ¿cómo modularás tu esfuerzo? "
                "¿Qué paso pequeño y realista puedes dar hoy para avanzar sin agotarte?"
            )
        else:
            return (
                "Esa microacción es perfecta y realista. Recuerda que el GRIT no se trata de empujar hasta "
                "el colapso, sino de dar pasos constantes. ¿Qué necesitas preparar para asegurar que logres "
                "dar ese pequeño paso hoy?"
            )
            
    elif session_num == 4:
        # Consistencia (GRIT)
        if history_length == 0:
            return (
                "Bienvenido al Módulo 4. Hoy trabajaremos la Consistencia de Interés (mantener la pasión). "
                "Cuando sientes ganas de dejar un proyecto académico a medias porque se volvió aburrido, "
                "¿cómo conectas ese esfuerzo con tu meta a largo plazo de convertirte en estratega de negocios?"
            )
        else:
            return (
                "Conectar tu labor diaria con tu visión futura (propósito) es el corazón de la pasión sostenida. "
                "¿Qué parte de este proyecto sigue teniendo un significado real y valioso para ti?"
            )
            
    elif session_num == 5:
        # Liderazgo Positivo (Cierre)
        if history_length == 0:
            return (
                "Bienvenido a nuestro Módulo final: Liderazgo Positivo. Hoy cerramos tu ciclo de coaching. "
                "Pensando en tu red de apoyo en la Universidad La Salle, ¿con qué compañeros o mentores puedes "
                "contar para mantener este esfuerzo? ¿Cómo planeas promover la comunicación positiva en tus equipos?"
            )
        else:
            return (
                "¡Excelente plan de continuidad! Has construido una base sólida de perseverancia y liderazgo. "
                "Te felicito por tu dedicación en estas 5 sesiones. Por favor, haz clic en el botón de la barra "
                "lateral para finalizar formalmente y pasar al cuestionario final."
            )
    else:
        return "Módulo completado."

# ----------------- INICIALIZACIÓN DE VARIABLES -----------------

authorized_ids = get_authorized_ids()

# ----------------- CONTROL DE VISTAS (INVESTIGADOR VS. ESTUDIANTE) -----------------

# Obtener la contraseña desde el estado de la sesión para evitar NameError
admin_password = st.session_state.get("admin_pwd_widget", "")
is_admin = (admin_password == INVESTIGADOR_PASSWORD)

# BARRA LATERAL (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/teacher.png", width=100)
    st.markdown('<p style="font-weight: 800; font-size: 1.4rem; margin-bottom: 0;">AIAG Portal</p>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-size: 0.85rem; margin-top: 0;">Tesis Doctoral Vania Alemán</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Campo para activar el modo Investigador
    admin_password = st.text_input("🔑 Contraseña Investigador:", type="password", key="admin_pwd_widget")
    
    is_admin = (admin_password == INVESTIGADOR_PASSWORD)
    
    if is_admin:
        st.success("Acceso de Investigador Concedido")
        # Mostrar botón de descarga rápida en la barra lateral del investigador
        logs_quick = load_chat_logs()
        if len(logs_quick) > 0:
            with open("chat_logs.csv", "r", encoding="utf-8") as f:
                st.download_button(
                    label="📥 Exportar CSV",
                    data=f.read(),
                    file_name="chat_logs_tesis.csv",
                    mime="text/csv"
                )
        
        # Botón para cerrar sesión de investigador
        if st.button("🚪 Volver al Chat (Cerrar Sesión)"):
            st.session_state["admin_pwd_widget"] = ""
            st.rerun()
    else:
        # Configuración del Estudiante
        st.markdown("### Configuración Estudiante")
        mode = st.radio(
            "Modo de Operación:",
            ["Modo Simulación (Sin API Key)", "Gemini API (Real)"]
        )
        api_key = ""
        
        # Verificar si hay una API Key guardada en Streamlit Secrets (Producción Segura)
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.info("🔒 API Key cargada de forma segura desde los secretos del servidor.")
        elif mode == "Gemini API (Real)":
            api_key = st.text_input("Gemini API Key:", type="password", help="Pega tu API Key de Google AI Studio.")
            if not api_key:
                st.warning("Introduce tu API Key para poder chatear.")
                
        st.markdown("---")
        st.markdown("""
        <div class="sidebar-card">
            <p style="margin-bottom: 0.5rem; font-weight: 600; font-size:0.9rem;">Marco Teórico Congelado</p>
            <ul style="font-size: 0.8rem; padding-left: 1.1rem; margin-bottom: 0;">
                <li><b>Módulo 1:</b> Growth Mindset</li>
                <li><b>Módulo 2:</b> Autoeficacia</li>
                <li><b>Módulo 3:</b> GRIT (Esfuerzo)</li>
                <li><b>Módulo 4:</b> GRIT (Interés/Pasión)</li>
                <li><b>Módulo 5:</b> Liderazgo Positivo</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ----------------- RUTA A: VISTA DEL INVESTIGADOR (DASHBOARD) -----------------

if is_admin:
    st.markdown('<h1 class="gradient-text">AIAG • Investigador</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Panel de análisis de tesis y gestión del experimento</p>', unsafe_allow_html=True)
    
    # Cargar logs y procesar datos
    logs = load_chat_logs()
    total_turns = len(logs)
    
    # Calcular métricas del dashboard
    unique_participants = set()
    grit_signals_count = 0
    capa0_activations = 0
    
    # Diccionario para agrupar estadísticas por estudiante
    student_stats = {}
    
    for row in logs:
        student = row.get("student_id", "DESCONOCIDO")
        unique_participants.add(student)
        
        # Detectar triggers de seguridad (Capa 0)
        safety_triggered = (row.get("safety_triggered", "False") == "True")
        if safety_triggered:
            capa0_activations += 1
            
        # Contar palabras clave en mensajes de estudiantes
        user_msg = row.get("user_message", "").lower()
        grit_hits = sum(1 for word in GRIT_SIGNALS if word in user_msg)
        lider_hits = sum(1 for word in LIDER_SIGNALS if word in user_msg)
        
        grit_signals_count += grit_hits
        
        # Agrupación por estudiante
        h_id = hash_id(student)
        if h_id not in student_stats:
            student_stats[h_id] = {
                "id_original": student,
                "cohorte": authorized_ids.get(student, {}).get("cohorte", "piloto") if student in authorized_ids else "piloto",
                "turnos": 0,
                "grit": 0,
                "liderazgo": 0,
                "capa_0": 0
            }
        
        student_stats[h_id]["turnos"] += 1
        student_stats[h_id]["grit"] += grit_hits
        student_stats[h_id]["liderazgo"] += lider_hits
        if safety_triggered:
            student_stats[h_id]["capa_0"] += 1
            
    # Mostrar tarjetas de métricas en la fila superior (igual que en el diseño de Vania)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="dashboard-card-title">👥 Participantes</div>
            <div class="dashboard-card-value">{len(unique_participants)}</div>
            <div class="dashboard-card-label">Estudiantes únicos activos</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="dashboard-card-title">💬 Turnos Totales</div>
            <div class="dashboard-card-value">{total_turns}</div>
            <div class="dashboard-card-label">Mensajes totales enviados</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="dashboard-card-title">📈 Señales GRIT</div>
            <div class="dashboard-card-value">{grit_signals_count}</div>
            <div class="dashboard-card-label">Menciones de perseverancia</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="dashboard-card-title">🚨 Capa 0</div>
            <div class="dashboard-card-value">{capa0_activations}</div>
            <div class="dashboard-card-label">Activaciones de seguridad</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Crear pestañas del panel
    tab_sesiones, tab_logs, tab_codigos = st.tabs(["Sesiones", "Logs anonimizados", "Códigos de acceso"])
    
    # Pestaña 1: Sesiones
    with tab_sesiones:
        st.markdown("### Resumen de Sesiones por Participante (Hash Anónimo)")
        if len(student_stats) == 0:
            st.info("Aún no hay datos de sesiones registradas.")
        else:
            table_data = []
            for h_id, stats in student_stats.items():
                orig_id = stats["id_original"]
                session_raw = authorized_ids.get(orig_id, {}).get("current_session", "1")
                modulos = "Completado" if session_raw == "completed" else f"{session_raw}/5"
                
                table_data.append({
                    "Participante (hash)": h_id,
                    "Cohorte": stats["cohorte"],
                    "Módulo": modulos,
                    "Turnos": stats["turnos"],
                    "GRIT": stats["grit"],
                    "Liderazgo": stats["liderazgo"],
                    "Capa 0": stats["capa_0"]
                })
            st.table(table_data)
            
    # Pestaña 2: Logs anonimizados
    with tab_logs:
        st.markdown("### Historial de Conversaciones Anonimizadas")
        if len(logs) == 0:
            st.info("Aún no hay mensajes para mostrar.")
        else:
            all_hashes = ["Todos"] + list(student_stats.keys())
            selected_hash = st.selectbox("Filtrar por participante (hash):", all_hashes)
            
            for row in logs:
                h_id = hash_id(row.get("student_id", ""))
                if selected_hash == "Todos" or selected_hash == h_id:
                    st.markdown(f"**Fecha:** `{row.get('timestamp')}` | **Participante (hash):** `{h_id}` | **Sesión:** `{row.get('session', '1')}`")
                    st.markdown(f"🙋‍♂️ **Estudiante:** {row.get('user_message')}")
                    
                    is_safety = (row.get("safety_triggered", "False") == "True")
                    if is_safety:
                        st.markdown(f'<div class="safety-alert" style="margin-top:0.5rem;"><div class="safety-title">Capa 0 Activada</div>{row.get("ai_response")}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f"🤖 **AIAG Coach:** {row.get('ai_response')}")
                    st.markdown("---")
                    
    # Pestaña 3: Códigos de acceso
    with tab_codigos:
        st.markdown("### Gestión de Códigos de Acceso")
        
        # Formulario para agregar nuevo ID
        st.markdown("#### Registrar nuevo estudiante")
        col_new_id, col_new_cohorte, col_btn = st.columns([3, 2, 1])
        with col_new_id:
            new_id = st.text_input("Código de ID único:", placeholder="Ej: EST-002", key="new_student_id_input").strip()
        with col_new_cohorte:
            new_cohort = st.selectbox("Cohorte/Grupo:", ["piloto", "experimental", "control"], key="new_cohort_select")
        with col_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("➕ Registrar", key="btn_register_student"):
                if new_id:
                    authorized_ids[new_id] = {"cohorte": new_cohort, "current_session": "1"}
                    save_authorized_ids(authorized_ids)
                    st.success(f"ID {new_id} registrado con éxito.")
                    st.rerun()
                else:
                    st.error("Introduce un ID válido.")
                    
        # Tabla de códigos existentes con opción de reinicio
        st.markdown("#### Códigos actualmente autorizados")
        
        for k, v in list(authorized_ids.items()):
            col_id, col_coh, col_sess, col_actions = st.columns([2, 2, 2, 2])
            with col_id:
                st.markdown(f"**ID:** `{k}`")
            with col_coh:
                st.markdown(f"Grupo: `{v['cohorte']}`")
            with col_sess:
                sess_label = "Completado" if v['current_session'] == "completed" else f"Sesión {v['current_session']}/5"
                st.markdown(f"Progreso: **{sess_label}**")
            with col_actions:
                col_btn_reset, col_btn_del = st.columns(2)
                with col_btn_reset:
                    if st.button("🔄 Reiniciar", key=f"reset_{k}", help="Reiniciar progreso a Sesión 1"):
                        authorized_ids[k]["current_session"] = "1"
                        save_authorized_ids(authorized_ids)
                        st.success(f"Progreso de {k} reiniciado.")
                        st.rerun()
                with col_btn_del:
                    if st.button("🗑️ Borrar", key=f"del_{k}"):
                        del authorized_ids[k]
                        save_authorized_ids(authorized_ids)
                        st.warning(f"ID {k} eliminado.")
                        st.rerun()
            st.markdown("---")

# ----------------- RUTA B: VISTA DE ESTUDIANTE -----------------

else:
    # Inicializar estados de cuestionario
    if "pre_test_done" not in st.session_state:
        st.session_state.pre_test_done = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.markdown('<h1 class="gradient-text">Conversación de Coaching Académico</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Desarrollo de Liderazgo Positivo y GRIT — Universidad La Salle</p>', unsafe_allow_html=True)
    
    # Solicitar Código de Estudiante
    st.markdown("### Acceso al Sistema")
    student_id = st.text_input("Ingresa tu código único de participante:", placeholder="Escribe tu ID asignado aquí", key="student_id_widget").strip()
    
    if not student_id:
        st.info("🔑 Por favor, escribe tu código único en la casilla para iniciar.")
        
    elif student_id not in authorized_ids:
        st.error(
            "❌ **Código no autorizado.**\n\n"
            "El ID que ingresaste no se encuentra en la lista de participantes autorizados de este estudio. "
            "Si eres estudiante de la Licenciatura en Estrategia y Transformación de Negocios, "
            "por favor contacta a la investigadora **Vania Alemán** para verificar tu ID."
        )
        
    else:
        # ID AUTORIZADO
        student_data = authorized_ids[student_id]
        current_session = student_data["current_session"]
        
        # 1. EVALUAR SI YA COMPLETÓ EL EXPERIMENTO COMPLETO
        if current_session == "completed":
            st.markdown(f"""
            <div class="forms-card" style="border-left-color: #2e7d32; background-color: #e8f5e9;">
                <p style="font-weight: 800; font-size: 1.25rem; color: #2e7d32; margin-bottom: 0.5rem;">Fase final: Cuestionario de Salida (Post-test)</p>
                <p style="font-size: 0.95rem; margin-bottom: 1rem;">
                    ¡Muchas felicidades! Has completado con éxito tus 5 sesiones de coaching de Liderazgo Positivo y GRIT. 
                    Para finalizar formalmente tu participación y registrar tus datos, por favor contesta el cuestionario de salida en Google Forms:
                </p>
                <a href="{URL_POST_TEST}" target="_blank" style="background-color: #2e7d32; color: white; padding: 0.7rem 1.4rem; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    📝 Ir al Google Form (Post-test)
                </a>
            </div>
            """, unsafe_allow_html=True)
            st.info("El chat se encuentra cerrado de manera definitiva. ¡Gracias por tu valiosa participación!")
            
        # 2. EVALUAR SI DEBE LLENAR EL PRE-TEST (Solo antes de iniciar la Sesión 1)
        elif current_session == "1" and not st.session_state.pre_test_done:
            st.markdown(f"""
            <div class="forms-card">
                <p style="font-weight: 800; font-size: 1.25rem; color: #1e3c72; margin-bottom: 0.5rem;">Fase 1: Cuestionario Inicial (Pre-test)</p>
                <p style="font-size: 0.95rem; margin-bottom: 1rem;">
                    Bienvenido/a al estudio. Antes de poder iniciar tus conversaciones con el Coach de IA, 
                    es requisito metodológico obligatorio que contestes el cuestionario de diagnóstico inicial en Google Forms:
                </p>
                <a href="{URL_PRE_TEST}" target="_blank" style="background-color: #2a5298; color: white; padding: 0.7rem 1.4rem; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    📝 Ir al Google Form (Pre-test)
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("✅ Ya completé el cuestionario, iniciar coaching", key="btn_confirm_pre_test"):
                st.session_state.pre_test_done = True
                st.success("¡Gracias! Sesión de coaching desbloqueada.")
                st.rerun()
                
        # 3. CHAT DE SESIÓN ACTIVA
        else:
            session_num = int(current_session)
            session_info = SESSION_METADATA[session_num]
            
            # Cargar prompt de sistema compuesto (Prompt Base + Prompt específico de sesión)
            active_system_prompt = BASE_SYSTEM_PROMPT + "\n" + session_info["prompt"]
            
            # Banner Informativo del Módulo Actual
            st.markdown(f"""
            <div class="session-banner">
                <p style="margin: 0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: #1e3c72; font-weight: 800;">Sesión Activa</p>
                <h3 style="margin: 0.2rem 0 0.4rem 0; font-weight: 800; color: #111;">{session_info['title']}</h3>
                <p style="margin: 0; font-size: 0.95rem; color: #444;">{session_info['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botón en la barra lateral del estudiante para finalizar y guardar la sesión
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"### Control de la Sesión {session_num}")
            if st.sidebar.button(f"💾 Guardar y Finalizar Sesión {session_num}", key=f"btn_finish_sess_{session_num}", help="Presiona aquí al terminar de chatear para guardar tu progreso."):
                
                # Avanzar sesión
                next_session = str(session_num + 1) if session_num < 5 else "completed"
                authorized_ids[student_id]["current_session"] = next_session
                save_authorized_ids(authorized_ids)
                
                # Resetear el historial de mensajes de la pantalla
                st.session_state.messages = []
                
                st.sidebar.success(f"¡Sesión {session_num} guardada con éxito!")
                st.rerun()
                
            # Mostrar historial de chat de la sesión
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if "is_safety" in message and message["is_safety"]:
                        st.markdown(f'<div class="safety-alert"><div class="safety-title">Alerta de Seguridad Activada</div>{message["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(message["content"])

            # Entrada del Estudiante
            if user_input := st.chat_input("Escribe tu respuesta o reflexión aquí..."):
                
                # Mostrar mensaje del usuario
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.markdown(user_input)
                    
                # Evaluar Filtro de Seguridad (Local y Determinista - Capa 0)
                safety_triggered = check_safety_filter(user_input)
                
                response_content = ""
                is_safety_msg = False
                
                if safety_triggered:
                    response_content = SAFETY_MESSAGE
                    is_safety_msg = True
                    
                    log_interaction(student_id, mode, user_input, "[LÍNEA DE LA VIDA TRIGGERED] " + SAFETY_MESSAGE.replace("\n", " "), True, session_num)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response_content, "is_safety": True})
                    with st.chat_message("assistant"):
                        st.markdown(f'<div class="safety-alert"><div class="safety-title">Alerta de Seguridad Activada</div>{response_content}</div>', unsafe_allow_html=True)
                else:
                    # Lógica normal si no se activa el filtro
                    with st.chat_message("assistant"):
                        with st.spinner("Pensando respuesta de coaching..."):
                            if mode == "Modo Simulación (Sin API Key)":
                                response_content = get_simulated_response(user_input, len(st.session_state.messages), session_num)
                                st.markdown(response_content)
                            else:
                                if not api_key:
                                    response_content = "⚠️ Error: Modo Gemini API seleccionado pero no se ha proporcionado una API Key en la barra lateral."
                                    st.error(response_content)
                                else:
                                    try:
                                        from google import genai
                                        from google.genai import types
                                        
                                        client = genai.Client(api_key=api_key)
                                        
                                        contents = []
                                        for msg in st.session_state.messages[:-1]:
                                            role = "user" if msg["role"] == "user" else "model"
                                            contents.append(
                                                types.Content(
                                                    role=role,
                                                    parts=[types.Part.from_text(text=msg["content"])]
                                                )
                                            )
                                        
                                        contents.append(
                                            types.Content(
                                                role="user",
                                                parts=[types.Part.from_text(text=user_input)]
                                            )
                                        )
                                        
                                        response = client.models.generate_content(
                                            model='gemini-2.5-flash',
                                            contents=contents,
                                            config=types.GenerateContentConfig(
                                                system_instruction=active_system_prompt,
                                                temperature=0.2,
                                            ),
                                        )
                                        response_content = response.text
                                        st.markdown(response_content)
                                        
                                    except Exception as e:
                                        response_content = f"❌ Error de conexión con Gemini API: {str(e)}"
                                        st.error(response_content)
                        
                        st.session_state.messages.append({"role": "assistant", "content": response_content})
                        log_interaction(student_id, mode, user_input, response_content, False, session_num)

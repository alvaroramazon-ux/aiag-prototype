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

# Estilos CSS personalizados para una interfaz Premium y limpia (incluyendo los elementos del investigador)
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

# ----------------- FUNCIONES DE PERSISTENCIA -----------------

def get_authorized_ids():
    """Lee el archivo de IDs pre-autorizados o crea uno por defecto si no existe."""
    filename = "authorized_ids.csv"
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "cohorte"])
            writer.writerows([
                ["PILOTO-01", "piloto"],
                ["PILOTO-02", "piloto"],
                ["PILOTO-03", "piloto"],
                ["EST-101", "licenciatura"],
                ["EST-102", "licenciatura"]
            ])
    ids = {}
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids[row["id"]] = row["cohorte"]
    return ids

def save_authorized_ids(ids_dict):
    """Guarda el diccionario de IDs autorizados de vuelta al archivo CSV."""
    filename = "authorized_ids.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "cohorte"])
        for student_id, cohorte in ids_dict.items():
            writer.writerow([student_id, cohorte])

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

def log_interaction(student_id, mode, user_message, ai_response, safety_triggered):
    """Registra la interacción en el CSV local."""
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
    """Genera respuestas simuladas de coaching para probar la interfaz."""
    msg = user_message.lower()
    if history_length == 0:
        return (
            "¡Hola! Qué gusto saludarte. Como tu coach de Liderazgo Positivo, estoy aquí para "
            "acompañarte a reflexionar sobre tus metas y retos académicos. Cuéntame, ¿cuál es tu "
            "principal objetivo académico en este momento y qué te motiva a alcanzarlo?"
        )
    elif any(word in msg for word in ["reto", "dificil", "dificultad", "problema", "estres"]):
        return (
            "Entiendo que es un desafío complicado. El modelo de Cameron nos enseña que el *Clima Positivo* "
            "consiste en ver las dificultades como oportunidades de aprendizaje. ¿Cómo podrías reestructurar "
            "este obstáculo usando una mentalidad de crecimiento? ¿Qué fortalezas personales tienes para afrontarlo?"
        )
    elif any(word in msg for word in ["cansado", "rendirme", "flojera", "dejar"]):
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

# ----------------- INICIALIZACIÓN DE VARIABLES -----------------

authorized_ids = get_authorized_ids()

# ----------------- DISEÑO DE LA BARRA LATERAL (Sidebar) -----------------

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/teacher.png", width=100)
    st.markdown('<p style="font-weight: 800; font-size: 1.4rem; margin-bottom: 0;">AIAG Portal</p>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-size: 0.85rem; margin-top: 0;">Tesis Doctoral Vania Alemán</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Campo para activar el modo Investigador
    admin_password = st.text_input("🔑 Contraseña Investigador:", type="password")
    
    # Evaluar si es investigador o estudiante
    is_admin = (admin_password == INVESTIGADOR_PASSWORD)
    
    if is_admin:
        st.success("Acceso de Investigador Concedido")
    else:
        # Selección de Modo y API Key para Estudiantes
        st.markdown("### Configuración Estudiante")
        mode = st.radio(
            "Modo de Operación:",
            ["Modo Simulación (Sin API Key)", "Gemini API (Real)"]
        )
        api_key = ""
        if mode == "Gemini API (Real)":
            api_key = st.text_input("Gemini API Key:", type="password")
            if not api_key:
                st.warning("Introduce tu API Key para poder chatear.")
                
        st.markdown("---")
        st.markdown("""
        <div class="sidebar-card">
            <p style="margin-bottom: 0.5rem; font-weight: 600; font-size:0.9rem;">Marco Teórico Congelado</p>
            <ul style="font-size: 0.8rem; padding-left: 1.1rem; margin-bottom: 0;">
                <li><b>GRIT:</b> Perseverancia y pasión.</li>
                <li><b>Liderazgo Positivo:</b> Clima, relaciones, comunicación y propósito positivo.</li>
                <li><b>Growth Mindset:</b> Técnica interna.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón para reiniciar conversación
        if st.button("🔄 Reiniciar Conversación"):
            st.session_state.messages = []
            st.session_state.pre_test_done = False
            st.session_state.post_test_done = False
            st.rerun()

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
                "cohorte": authorized_ids.get(student, "piloto"),
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
            
    # Mostrar tarjetas de métricas en la fila superior (igual que en el diseño del usuario)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="dashboard-card-title">👥 Participantes</div>
            <div class="dashboard-card-value">{len(unique_participants)}</div>
            <div class="dashboard-card-label">Estudiantes únicos registrados</div>
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
            <div class="dashboard-card-label">Palabras clave de resiliencia</div>
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
        
    # Botón para descargar el archivo CSV
    if total_turns > 0:
        with open("chat_logs.csv", "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Exportar CSV (Historial Completo)",
                data=f.read(),
                file_name="chat_logs_tesis.csv",
                mime="text/csv"
            )
            
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
                # Simular número de módulos completados en base a turnos (ej. 1/5)
                modulos = "1/5" if stats["turnos"] < 6 else f"{min(5, stats['turnos'] // 5)}/5"
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
            # Filtro por estudiante
            all_hashes = ["Todos"] + list(student_stats.keys())
            selected_hash = st.selectbox("Filtrar por participante (hash):", all_hashes)
            
            for row in logs:
                h_id = hash_id(row.get("student_id", ""))
                if selected_hash == "Todos" or selected_hash == h_id:
                    st.markdown(f"**Fecha:** `{row.get('timestamp')}` | **Participante (hash):** `{h_id}`")
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
            new_id = st.text_input("Código de ID único:", placeholder="Ej: EST-501").strip()
        with col_new_cohorte:
            new_cohort = st.selectbox("Cohorte/Grupo:", ["piloto", "experimental", "control"])
        with col_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("➕ Registrar"):
                if new_id:
                    authorized_ids[new_id] = new_cohort
                    save_authorized_ids(authorized_ids)
                    st.success(f"ID {new_id} registrado con éxito.")
                    st.rerun()
                else:
                    st.error("Introduce un ID válido.")
                    
        # Tabla de códigos existentes
        st.markdown("#### Códigos actualmente autorizados")
        auth_list = [{"ID Estudiante": k, "Cohorte/Grupo": v, "Hash de Seguridad": hash_id(k)} for k, v in authorized_ids.items()]
        st.table(auth_list)

# ----------------- RUTA B: VISTA DE ESTUDIANTE -----------------

else:
    # Inicializar estados de cuestionario
    if "pre_test_done" not in st.session_state:
        st.session_state.pre_test_done = False
    if "post_test_done" not in st.session_state:
        st.session_state.post_test_done = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.markdown('<h1 class="gradient-text">Conversación de Coaching Académico</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Desarrollo de Liderazgo Positivo y GRIT — Universidad La Salle</p>', unsafe_allow_html=True)
    
    # 1. SOLICITAR CÓDIGO DE ACCESO
    st.markdown("### Acceso al Sistema")
    student_id = st.text_input("Ingresa tu código único de participante:", placeholder="Escribe tu ID asignado aquí").strip()
    
    if not student_id:
        st.info("🔑 Por favor, escribe tu código único en la casilla para iniciar.")
        
    elif student_id not in authorized_ids:
        st.error(
            "❌ **Código no autorizado.**\n\n"
            "El ID que ingresaste no se encuentra en la lista de participantes autorizados de este estudio. "
            "Si eres estudiante de la Licenciatura en Estrategia y Transformación de Negocios y formas parte de la muestra, "
            "por favor contacta a la investigadora **Vania Alemán** para verificar tu ID."
        )
        
    else:
        # ID AUTORIZADO
        cohorte = authorized_ids[student_id]
        
        # 2. EVALUAR SI DEBE LLENAR EL PRE-TEST
        if not st.session_state.pre_test_done:
            st.markdown(f"""
            <div class="forms-card">
                <p style="font-weight: 800; font-size: 1.2rem; color: #1e3c72; margin-bottom: 0.5rem;">Fase 1: Cuestionario Inicial (Pre-test)</p>
                <p style="font-size: 0.95rem; margin-bottom: 1rem;">
                    Bienvenido/a al estudio. Antes de poder iniciar tus conversaciones con el Coach de IA, 
                    es requisito metodológico obligatorio que contestes el cuestionario de diagnóstico inicial en Google Forms.
                </p>
                <a href="{URL_PRE_TEST}" target="_blank" style="background-color: #2a5298; color: white; padding: 0.6rem 1.2rem; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block; margin-bottom: 1rem;">
                    📝 Ir al Google Form (Pre-test)
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("✅ Ya completé el cuestionario, iniciar coaching"):
                st.session_state.pre_test_done = True
                st.success("¡Gracias! Sesión de coaching desbloqueada.")
                st.rerun()
                
        # 3. EVALUAR SI YA COMPLETÓ EL POST-TEST
        elif st.session_state.post_test_done:
            st.markdown(f"""
            <div class="forms-card" style="border-left-color: #2e7d32;">
                <p style="font-weight: 800; font-size: 1.2rem; color: #2e7d32; margin-bottom: 0.5rem;">Fase final: Cuestionario de Salida (Post-test)</p>
                <p style="font-size: 0.95rem; margin-bottom: 1rem;">
                    Has completado tus sesiones de coaching. Para finalizar formalmente tu participación y registrar tus datos, 
                    por favor llena el cuestionario de salida en Google Forms.
                </p>
                <a href="{URL_POST_TEST}" target="_blank" style="background-color: #2e7d32; color: white; padding: 0.6rem 1.2rem; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block; margin-bottom: 1rem;">
                    📝 Ir al Google Form (Post-test)
                </a>
            </div>
            """, unsafe_allow_html=True)
            st.info("El chat se encuentra cerrado debido a que se ha completado el módulo de coaching.")
            
        else:
            # 4. CHAT ACTIVO
            # Mostrar botón en barra lateral para terminar el proceso (Cuestionario Post-test)
            st.sidebar.markdown("---")
            st.sidebar.markdown("### Finalizar Experimento")
            if st.sidebar.button("🔴 Terminar Coaching"):
                st.session_state.post_test_done = True
                st.rerun()
                
            # Mostrar historial de chat
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
                    
                # Evaluar Filtro de Seguridad (Local y Determinista)
                safety_triggered = check_safety_filter(user_input)
                
                response_content = ""
                is_safety_msg = False
                
                if safety_triggered:
                    response_content = SAFETY_MESSAGE
                    is_safety_msg = True
                    
                    log_interaction(student_id, mode, user_input, "[LÍNEA DE LA VIDA TRIGGERED] " + SAFETY_MESSAGE.replace("\n", " "), True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response_content, "is_safety": True})
                    with st.chat_message("assistant"):
                        st.markdown(f'<div class="safety-alert"><div class="safety-title">Alerta de Seguridad Activada</div>{response_content}</div>', unsafe_allow_html=True)
                else:
                    # Lógica normal si no se activa el filtro
                    with st.chat_message("assistant"):
                        with st.spinner("Pensando respuesta de coaching..."):
                            if mode == "Modo Simulación (Sin API Key)":
                                response_content = get_simulated_response(user_input, len(st.session_state.messages))
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
                                                system_instruction=SYSTEM_PROMPT,
                                                temperature=0.2,
                                            ),
                                        )
                                        response_content = response.text
                                        st.markdown(response_content)
                                        
                                    except Exception as e:
                                        response_content = f"❌ Error de conexión con Gemini API: {str(e)}"
                                        st.error(response_content)
                        
                        st.session_state.messages.append({"role": "assistant", "content": response_content})
                        log_interaction(student_id, mode, user_input, response_content, False)

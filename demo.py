import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
import time

# --- Intento de importar la librería de calendario ---
try:
    from streamlit_calendar import calendar
    CALENDAR_ENABLED = True
except ImportError:
    CALENDAR_ENABLED = False
    # El error se mostrará solo si se entra a la página de Agenda

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="SGC Integral360 (Demo Cliente)",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNCIONES DE UTILIDAD (Reutilizadas) ---
@st.cache_data
def convertir_a_csv(df):
    """Convierte un DataFrame de Pandas a CSV para descarga."""
    return df.to_csv(index=False).encode('utf-8')

def color_prediccion(val):
    """Aplica color a la celda de predicción de inventario."""
    color = 'white' # default text color
    bgcolor = 'transparent' # default bg
    if 'URGENTE' in str(val):
        bgcolor = '#FF4B4B' # red
        color = 'white'
    elif 'Pedir' in str(val):
        bgcolor = '#FFB84B' # orange
        color = 'black'
    elif 'OK' in str(val):
        bgcolor = '#4BBF73' # green
        color = 'white'
    return f'background-color: {bgcolor}; color: {color}'

# ====================================================================================
# --- DATOS DE SIMULACIÓN (ESTADO DE SESIÓN) ---
# ====================================================================================
def inicializar_datos():
    """Carga los datos iniciales en la sesión."""
    if 'pacientes' not in st.session_state:
        st.session_state.pacientes = [
            {'ID': 'P001', 'Nombre': 'Ana García', 'Historial': 'Hipertensión', 'Riesgo IA': 'Alto', 'Telefono': '5512345678', 'Servicio': 'Endodoncia', 'Costo': 4500, 'Fecha_Registro': datetime.date(2024, 1, 15), 'Tratamientos_Pasados': 5, 'Fuente': 'Recomendación', 'Aviso_Privacidad': 'Firmado'},
            {'ID': 'P002', 'Nombre': 'Luis Martínez', 'Historial': 'Ninguno', 'Riesgo IA': 'Bajo', 'Telefono': '5598765432', 'Servicio': 'Limpieza', 'Costo': 800, 'Fecha_Registro': datetime.date(2024, 5, 10), 'Tratamientos_Pasados': 1, 'Fuente': 'Web', 'Aviso_Privacidad': 'Firmado'},
            {'ID': 'P003', 'Nombre': 'Sofía Hernández', 'Historial': 'Diabetes Tipo 2', 'Riesgo IA': 'Alto', 'Telefono': '5555667788', 'Servicio': 'Ortodoncia', 'Costo': 28000, 'Fecha_Registro': datetime.date(2023, 11, 20), 'Tratamientos_Pasados': 8, 'Fuente': 'Recomendación', 'Aviso_Privacidad': 'Pendiente'},
            {'ID': 'P004', 'Nombre': 'Carlos Vera', 'Historial': 'Ninguno', 'Riesgo IA': 'Bajo', 'Telefono': '5511223344', 'Servicio': 'Limpieza', 'Costo': 800, 'Fecha_Registro': datetime.date(2024, 10, 1), 'Tratamientos_Pasados': 2, 'Fuente': 'Web', 'Aviso_Privacidad': 'Firmado'},
            {'ID': 'P005', 'Nombre': 'María López', 'Historial': 'Alergia Penicilina', 'Riesgo IA': 'Medio', 'Telefono': '5544332211', 'Servicio': 'Resina (x2)', 'Costo': 1800, 'Fecha_Registro': datetime.date(2024, 10, 5), 'Tratamientos_Pasados': 1, 'Fuente': 'Chatbot', 'Aviso_Privacidad': 'Firmado'}
        ]
    if 'citas' not in st.session_state:
        today = datetime.date.today()
        st.session_state.citas = [
            # Citas de hoy
            {'ID Paciente': 'P001', 'Doctor': 'Dr. Salas', 'Fecha': today, 'Hora': '10:00', 'Estado': 'Confirmada', 'Servicio': 'Endodoncia', 'Costo_Cita': 4500},
            {'ID Paciente': 'P002', 'Doctor': 'Dra. Vega', 'Fecha': today, 'Hora': '12:00', 'Estado': 'Confirmada', 'Servicio': 'Limpieza', 'Costo_Cita': 800},
            # Citas futuras
            {'ID Paciente': 'P003', 'Doctor': 'Dr. Salas', 'Fecha': today + datetime.timedelta(days=1), 'Hora': '16:00', 'Estado': 'Pendiente', 'Servicio': 'Ortodoncia (Ajuste)', 'Costo_Cita': 1500},
            {'ID Paciente': 'P005', 'Doctor': 'Dra. Vega', 'Fecha': today + datetime.timedelta(days=2), 'Hora': '11:00', 'Estado': 'Confirmada', 'Servicio': 'Resina (Revisión)', 'Costo_Cita': 0},
            # Citas pasadas (para KPIs)
            {'ID Paciente': 'P001', 'Doctor': 'Dr. Salas', 'Fecha': today - datetime.timedelta(days=7), 'Hora': '10:00', 'Estado': 'Completada', 'Servicio': 'Valoración', 'Costo_Cita': 800},
            {'ID Paciente': 'P004', 'Doctor': 'Dra. Vega', 'Fecha': today - datetime.timedelta(days=10), 'Hora': '14:00', 'Estado': 'Cancelada', 'Servicio': 'Limpieza', 'Costo_Cita': 800}
        ]
    if 'inventario' not in st.session_state:
        st.session_state.inventario = {
            'Guantes (Caja)': {'Stock': 15, 'Uso Mensual': 50, 'Predicción IA': 'Pedir 5 cajas', 'Costo_Unitario': 180, 'Proveedor': 'DentalPro'},
            'Anestesia (ml)': {'Stock': 250, 'Uso Mensual': 400, 'Predicción IA': 'Pedir 200ml', 'Costo_Unitario': 15, 'Proveedor': 'MedSupply'},
            'Resina A2 (Jeringa)': {'Stock': 5, 'Uso Mensual': 15, 'Predicción IA': '¡PEDIDO URGENTE!', 'Costo_Unitario': 950, 'Proveedor': '3M Dental'}
        }
    
    # --- Simulación de Ingresos Acumulados ---
    if 'grafico_pronostico_base' not in st.session_state:
        dias = np.arange(1, 31)
        ingresos_diarios = np.random.randint(10000, 25000, 30)
        tendencia = np.linspace(1.0, 1.3, 30)
        ingresos_diarios = ingresos_diarios * tendencia
        ingresos_acumulados = ingresos_diarios.cumsum()
        st.session_state.grafico_pronostico_base = {"dias": dias, "ingresos": ingresos_acumulados}

    # --- Cachear gráficos estáticos ---
    if 'pie_fig' not in st.session_state:
        if 'pacientes' in st.session_state and len(st.session_state.pacientes) > 0:
            df_pacientes = pd.DataFrame(st.session_state.pacientes)
            servicios_conteo = df_pacientes['Servicio'].value_counts()
            
            pie_fig = go.Figure(data=[go.Pie(
                labels=servicios_conteo.index, 
                values=servicios_conteo.values, 
                hole=.3,
                pull=[0.1 if i == 0 else 0 for i in range(len(servicios_conteo))] # Destacar el más común
            )])
            pie_fig.update_layout(
                title_text="Pacientes por Tipo de Servicio Principal", 
                margin=dict(t=50, b=10, l=10, r=10)
            )
            st.session_state.pie_fig = pie_fig
        else:
            st.session_state.pie_fig = go.Figure() # Figura vacía si no hay datos
        
    # Inicializar el estado del chatbot externo
    if 'chat_externo_messages' not in st.session_state:
        st.session_state.chat_externo_messages = [{"role": "assistant", "content": "¡Hola! Soy el asistente virtual de la Clínica Dental. ¿En qué puedo ayudarte hoy?"}]
    if 'chat_externo_state' not in st.session_state:
        st.session_state.chat_externo_state = "INIT"
    
    # --- KPIs del Chatbot ---
    if 'kpi_chat_consultas' not in st.session_state:
        st.session_state.kpi_chat_consultas = 0
    if 'kpi_chat_citas_ia' not in st.session_state:
        st.session_state.kpi_chat_citas_ia = 0
    if 'kpi_chat_urgencias' not in st.session_state:
        st.session_state.kpi_chat_urgencias = 0

    # --- KPIs de Facturación Aspel ---
    if 'kpi_aspel_sincronizado' not in st.session_state: st.session_state.kpi_aspel_sincronizado = 12500.50
    if 'kpi_aspel_pendiente' not in st.session_state: st.session_state.kpi_aspel_pendiente = 4500.00


# ====================================================================================
# --- PÁGINA 1: PANEL DE CONTROL (REQUERIMIENTO: KPI MAESTRO) ---
# ====================================================================================
def render_panel_control():
    st.title("📈 Panel de Control (KPIs Globales y de Módulos)")
    st.info("""
    **Propósito del Módulo:** Este es el **Panel de Control Maestro**. 
    Responde a su solicitud de consolidar los KPIs más importantes de **todos los módulos** en una sola vista para una toma de decisiones 360°.
    """)
    
    # --- CÁLCULO DE TODOS LOS KPIs ---
    df_pacientes = pd.DataFrame(st.session_state.pacientes)
    df_citas = pd.DataFrame(st.session_state.citas)
    df_inventario = pd.DataFrame.from_dict(st.session_state.inventario, orient='index')
    today = datetime.date.today()
    
    # --- KPIs Financieros (Pág 1) ---
    total_pacientes = len(df_pacientes)
    consulta_promedio = 800
    ingreso_real_total = df_pacientes['Costo'].sum()
    ticket_promedio_real = ingreso_real_total / total_pacientes if total_pacientes > 0 else 0
    citas_hoy = df_citas[df_citas['Fecha'] == today]
    ingreso_citas_hoy = citas_hoy['Costo_Cita'].sum()

    # --- KPIs Operativos (Pág 1 y 3) ---
    citas_completadas_mes = len(df_citas[
        (pd.to_datetime(df_citas['Fecha']).dt.date > today - datetime.timedelta(days=30)) & 
        (df_citas['Estado'] == 'Completada')
    ])
    citas_canceladas_mes = len(df_citas[
        (pd.to_datetime(df_citas['Fecha']).dt.date > today - datetime.timedelta(days=30)) & 
        (df_citas['Estado'] == 'Cancelada')
    ])
    tasa_no_show = (citas_canceladas_mes / (citas_completadas_mes + citas_canceladas_mes + 1)) * 100
    citas_prox_7d = len(df_citas[
        (pd.to_datetime(df_citas['Fecha']).dt.date >= today) &
        (pd.to_datetime(df_citas['Fecha']).dt.date < today + datetime.timedelta(days=7))
    ])

    # --- KPIs de Cartera y Cumplimiento (Pág 2 y 8) ---
    pacientes_alto_riesgo = len(df_pacientes[df_pacientes['Riesgo IA'] == 'Alto'])
    pacientes_nuevos_mes = len(df_pacientes[pd.to_datetime(df_pacientes['Fecha_Registro']).dt.date > today - datetime.timedelta(days=30)])
    consentimiento_pendiente = len(df_pacientes[df_pacientes['Aviso_Privacidad'] == 'Pendiente'])
    tasa_consentimiento = ((total_pacientes - consentimiento_pendiente) / total_pacientes) * 100 if total_pacientes > 0 else 100

    # --- KPIs del Chatbot (Pág 4) ---
    total_consultas_chat = st.session_state.kpi_chat_consultas
    citas_ia_chat = st.session_state.kpi_chat_citas_ia
    urgencias_chat = st.session_state.kpi_chat_urgencias
    tasa_conversion_chat = (citas_ia_chat / (total_consultas_chat + 1)) * 100

    # --- KPIs de Inventario y Facturación (Pág 6) ---
    valor_total_stock = (df_inventario['Stock'] * df_inventario['Costo_Unitario']).sum()
    items_urgentes = len(df_inventario[df_inventario['Predicción IA'].str.contains('URGENTE')])
    monto_sincronizado_aspel = st.session_state.kpi_aspel_sincronizado
    monto_pendiente_aspel = st.session_state.kpi_aspel_pendiente

    # --- RENDERIZADO DEL DASHBOARD MAESTRO ---
    
    st.subheader("Resumen Ejecutivo (Finanzas y Operaciones)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Valor Real de Cartera", f"${ingreso_real_total:,.2f} MXN", 
                help="Suma de los costos de los tratamientos principales de todos los pacientes.")
    col2.metric("Ticket Promedio Real", f"${ticket_promedio_real:,.2f} MXN",
                f"{((ticket_promedio_real / consulta_promedio) - 1) * 100:.0f}% vs. Consulta Base")
    col3.metric("Valor en Citas (Hoy)", f"${ingreso_citas_hoy:,.2f} MXN",
                help="Suma del valor de las citas programadas para hoy.")
    col4.metric("Tasa de No-Show (Últ. 30d)", f"{tasa_no_show:.1f}%",
                f"{citas_canceladas_mes} canceladas", "inverse")
    
    st.markdown("---")
    st.subheader("Resumen de Módulos (KPIs Específicos)")
    
    # --- Fila de Cartera y Agenda ---
    st.markdown("##### Cartera, Agenda y Cumplimiento")
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Pacientes Activos", f"{total_pacientes} Pacientes")
    col6.metric("Pacientes Nuevos (Últ. 30d)", f"{pacientes_nuevos_mes} Pacientes")
    col7.metric("Citas Próximos 7 Días", f"{citas_prox_7d} Citas")
    col8.metric("Tasa de Consentimiento (LFPDPPP)", f"{tasa_consentimiento:.0f}%",
                f"{consentimiento_pendiente} pendientes", "inverse" if consentimiento_pendiente > 0 else "normal")

    # --- Fila de Chatbot y Finanzas Internas ---
    st.markdown("##### Automatización (Chatbot y Aspel)")
    col9, col10, col11, col12 = st.columns(4)
    col9.metric("Consultas Chatbot (Hoy)", f"{total_consultas_chat}")
    col10.metric("Citas por Chatbot (Hoy)", f"{citas_ia_chat}",
                 f"{tasa_conversion_chat:.0f}% conversión")
    col11.metric("Monto Sincronizado (Aspel)", f"${monto_sincronizado_aspel:,.2f} MXN")
    col12.metric("Monto Pendiente (Aspel)", f"${monto_pendiente_aspel:,.2f} MXN",
                 "inverse" if monto_pendiente_aspel > 0 else "normal")

    # --- Fila de IA e Inventario ---
    st.markdown("##### Riesgo (IA e Inventario)")
    col13, col14, col15 = st.columns(3)
    col13.metric("Pacientes 'Alto Riesgo' (IA)", f"{pacientes_alto_riesgo} Pacientes",
                 "inverse" if pacientes_alto_riesgo > 0 else "normal")
    col14.metric("Valor Total del Inventario", f"${valor_total_stock:,.2f} MXN")
    col15.metric("Ítems Críticos (Inventario)", f"{items_urgentes} ítems",
                 "inverse" if items_urgentes > 0 else "normal")

    st.divider()
    
    # --- GRÁFICAS DE DESEMPEÑO ---
    st.subheader("Análisis Gráfico de Desempeño")
    c1_graf, c2_graf = st.columns(2)
    with c1_graf:
        st.plotly_chart(st.session_state.pie_fig, use_container_width=True)
    with c2_graf:
        st.markdown("**Costos de Servicios por Paciente**")
        st.dataframe(df_pacientes[['Nombre', 'Servicio', 'Costo']].style.format({"Costo": "S{:,.2f} MXN"}), use_container_width=True, height=300)


# ====================================================================================
# --- PÁGINA 2: GESTIÓN DE PACIENTES (CRM Base) ---
# ====================================================================================
def render_gestion_pacientes():
    st.title("👥 Gestión de Pacientes (CRM)")
    st.info("""
    **Propósito del Módulo:** Este es el núcleo del CRM. 
    Aquí se almacenan los datos de contacto y la IA los enriquece 
    clasificando a los pacientes por su nivel de riesgo y origen.
    """)
    
    # --- KPIs del Módulo ---
    st.subheader("KPIs de Cartera de Pacientes")
    df_pacientes = pd.DataFrame(st.session_state.pacientes)
    fuente_principal = df_pacientes['Fuente'].mode()[0] if not df_pacientes.empty else "N/A"
    
    # KPI de Cumplimiento LFPDPPP
    consentimiento_pendiente = len(df_pacientes[df_pacientes['Aviso_Privacidad'] == 'Pendiente'])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Pacientes", len(df_pacientes))
    col2.metric("Pacientes de Alto Riesgo (IA)", len(df_pacientes[df_pacientes['Riesgo IA'] == 'Alto']))
    col3.metric("Consentimientos Pendientes", f"{consentimiento_pendiente} Pacientes", 
                "inverse" if consentimiento_pendiente > 0 else "normal",
                help="Pacientes que no han firmado el Aviso de Privacidad de Datos Sensibles (LFPDPPP).")
    st.divider()

    st.subheader("Pacientes Registrados (Base de Datos Central)")
    # Mostrar la columna de cumplimiento
    st.dataframe(df_pacientes[['ID', 'Nombre', 'Telefono', 'Servicio', 'Costo', 'Riesgo IA', 'Aviso_Privacidad']], use_container_width=True)

    with st.expander("➕ Registrar Nuevo Paciente"):
        with st.form("form_nuevo_paciente"):
            id_nuevo = f"P{len(st.session_state.pacientes)+1:03d}"
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre Completo")
            telefono = c2.text_input("Teléfono")
            historial = st.text_area("Historial Médico (e.g., Hipertensión, Diabetes)")
            alergias = st.text_input("Alergias (e.g., Penicilina, Aspirina)")
            c3, c4 = st.columns(2)
            servicio = c3.text_input("Servicio Principal", "Limpieza")
            costo = c4.number_input("Costo del Servicio", min_value=0, value=800)
            
            # Check de Cumplimiento al registrar
            consentimiento = st.checkbox("El paciente firmó el Aviso de Privacidad y Consentimiento de Datos Sensibles (LFPDPPP).", value=False)
            
            submit_paciente = st.form_submit_button("Registrar Paciente")
            if submit_paciente:
                riesgo = 'Bajo'
                if 'hipertensión' in historial.lower() or 'diabetes' in historial.lower() or 'penicilina' in alergias.lower():
                    riesgo = 'Alto'
                
                nuevo_paciente = {
                    'ID': id_nuevo, 'Nombre': nombre, 'Historial': historial, 'Riesgo IA': riesgo, 
                    'Telefono': telefono, 'Servicio': servicio, 'Costo': costo, 
                    'Fecha_Registro': datetime.date.today(), 'Tratamientos_Pasados': 0, 'Fuente': 'Manual',
                    'Aviso_Privacidad': 'Firmado' if consentimiento else 'Pendiente'
                }
                st.session_state.pacientes.append(nuevo_paciente)
                st.success(f"Paciente {nombre} registrado. Riesgo IA detectado: {riesgo}")
                
                if not consentimiento:
                    st.warning("¡Alerta de Cumplimiento! El paciente fue registrado sin firmar el Aviso de Privacidad.")
                
                # --- CORRECCIÓN ERROR 'removeChild' ---
                st.session_state.pop('pie_fig', None)
                st.info("Paciente añadido. Los KPIs en el 'Panel de Control' se actualizarán al visitar esa pestaña.")


# ====================================================================================
# --- PÁGINA 3: AGENDA (CALENDARIO + WHATSAPP) ---
# ====================================================================================
def render_agenda_citas():
    st.title("🗓️ Agenda y Calendario Interactivo")
    st.info("""
    **Propósito del Módulo (Su Requerimiento):**
    Visualiza la agenda real de la clínica. Aquí validamos el proceso de agendar 
    una cita local (Asistente/Doctor) y cómo esto **dispara la notificación 
    simulada a WhatsApp**.
    """)
    
    if not CALENDAR_ENABLED:
        st.error("Módulo de Calendario deshabilitado. No se pudo importar 'streamlit-calendar'.")
        st.code("Instale esta librería en su venv: pip install streamlit-calendar")
        st.subheader("Vista de Tabla (Alternativa)")
        st.dataframe(pd.DataFrame(st.session_state.citas), use_container_width=True)
        return

    # --- KPIs del Módulo ---
    st.subheader("KPIs de Ocupación de Agenda")
    df_citas = pd.DataFrame(st.session_state.citas)
    today = datetime.date.today()
    citas_prox_7d = len(df_citas[
        (pd.to_datetime(df_citas['Fecha']).dt.date >= today) &
        (pd.to_datetime(df_citas['Fecha']).dt.date < today + datetime.timedelta(days=7))
    ])
    try:
        doctor_mas_ocupado = df_citas['Doctor'].mode()[0]
    except KeyError:
        doctor_mas_ocupado = "N/A" # Manejo de error si no hay citas
        
    citas_pendientes = len(df_citas[df_citas['Estado'] == 'Pendiente'])

    col1, col2, col3 = st.columns(3)
    col1.metric("Citas Próximos 7 Días", citas_prox_7d)
    col2.metric("Citas Pendientes de Confirmar", citas_pendientes)
    col3.metric("Doctor Más Ocupado", doctor_mas_ocupado)
    st.divider()

    tab1, tab2 = st.tabs(["🗓️ Vista de Calendario (Interactivo)", "➕ Agendar Cita (con Notificación WhatsApp)"])

    with tab1:
        st.subheader("Calendario de Citas")
        st.markdown("Haga clic en las citas o arrástrelas (simulación de reagendamiento).")
        
        events = []
        for cita in st.session_state.citas:
            try:
                start_datetime = datetime.datetime.combine(cita['Fecha'], datetime.datetime.strptime(cita['Hora'], '%H:%M').time())
                end_datetime = start_datetime + datetime.timedelta(hours=1)
                color = 'green' if cita['Estado'] == 'Confirmada' else 'orange' if cita['Estado'] == 'Pendiente' else 'red'
                paciente_nombre = next((p['Nombre'] for p in st.session_state.pacientes if p['ID'] == cita['ID Paciente']), "Paciente Chatbot")
                events.append({
                    "title": f"Cita: {paciente_nombre} ({cita['Servicio']})", 
                    "start": start_datetime.isoformat(), 
                    "end": end_datetime.isoformat(), 
                    "color": color, 
                    "resourceId": cita['Doctor']
                })
            except Exception as e:
                st.warning(f"No se pudo procesar la cita {cita['ID Paciente']}: {e}")
        
        calendar_options = {
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek,timeGridDay"},
            "initialView": "timeGridWeek", "slotMinTime": "08:00:00", "slotMaxTime": "20:00:00",
            "editable": True, "selectable": True, "allDaySlot": False,
            "resources": [
                {"id": "Dr. Salas", "title": "Dr. Salas"},
                {"id": "Dra. Vega", "title": "Dra. Vega"},
            ],
            "resourceAreaHeaderContent": "Doctores",
        }
        
        calendar(events=events, options=calendar_options)

    with tab2:
        st.subheader("Agendar Nueva Cita (Uso Interno)")
        st.markdown("Simulación del formulario que usaría su asistente.")
        
        with st.form("form_nueva_cita"):
            pacientes_nombres = [p['Nombre'] for p in st.session_state.pacientes]
            if not pacientes_nombres:
                st.error("No hay pacientes registrados.")
                paciente_sel = ""
            else:
                paciente_sel = st.selectbox("Paciente", pacientes_nombres)
                
            doctor_sel = st.selectbox("Doctor", ["Dr. Salas", "Dra. Vega"])
            fecha_cita = st.date_input("Fecha", min_value=datetime.date.today())
            hora_sel = st.time_input("Hora", datetime.time(14, 0))
            servicio = st.text_input("Servicio/Motivo", "Valoración")
            costo_cita = st.number_input("Costo de esta Cita", value=800)
            
            st.divider()
            st.markdown("**Confirmación al Paciente**")
            notificar_wa = st.checkbox("✅ Enviar confirmación por WhatsApp al paciente (Simulación)", value=True)
            
            submit_cita = st.form_submit_button("Agendar Cita y Notificar")
            
            if submit_cita and paciente_sel:
                paciente_obj = next(p for p in st.session_state.pacientes if p['Nombre'] == paciente_sel)
                paciente_id = paciente_obj['ID']
                paciente_telefono = paciente_obj['Telefono']
                
                nueva_cita = {
                    'ID Paciente': paciente_id, 'Doctor': doctor_sel, 'Fecha': fecha_cita, 
                    'Hora': hora_sel.strftime("%H:%M"), 'Estado': 'Confirmada', 'Servicio': servicio, 'Costo_Cita': costo_cita
                }
                st.session_state.citas.append(nueva_cita)
                st.success(f"Cita agendada para {paciente_sel} el {fecha_cita} a las {hora_sel}.")
                
                if notificar_wa:
                    with st.spinner(f"Enviando confirmación al WhatsApp {paciente_telefono} (Simulación)..."):
                        time.sleep(2)
                    st.success(f"¡Confirmación enviada por WhatsApp al teléfono de {paciente_sel}!")


# ====================================================================================
# --- PÁGINA 4: CHATBOT EXTERNO (TRIAGE Y AGENDAMIENTO) ---
# ====================================================================================
def render_chatbot_paciente():
    st.title("🤖 Chatbot de Pacientes (Triage y Agendamiento)")
    st.info("""
    **Propósito del Módulo (Su Requerimiento):**
    Este es el **Asistente Virtual 24/7** para sus pacientes. 
    Responde a su solicitud de un chatbot que pueda **calificar la urgencia (triage)** de un síntoma y **agendar citas** automáticamente.
    """)
    
    # --- KPIs del Módulo ---
    st.subheader("KPIs de Rendimiento del Chatbot (Simulados)")
    total_consultas = st.session_state.kpi_chat_consultas
    citas_ia = st.session_state.kpi_chat_citas_ia
    urgencias = st.session_state.kpi_chat_urgencias
    tasa_conversion = (citas_ia / (total_consultas + 1)) * 100 # +1 para evitar división por cero
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Consultas Atendidas (Hoy)", total_consultas, help="Número total de interacciones iniciadas por pacientes.")
    col2.metric("Citas Agendadas por IA (Hoy)", citas_ia, help="Pacientes que completaron el flujo de agendamiento.")
    col3.metric("Alertas de Urgencia (Hoy)", urgencias, "inverse", help="Pacientes que reportaron síntomas graves y fueron escalados.")
    col4.metric("Tasa de Conversión a Cita", f"{tasa_conversion:.1f}%", help="Porcentaje de consultas que terminan en una cita agendada.")
    st.divider()

    st.markdown("Pruebe el flujo de agendamiento. Escriba **'me duele una muela'**.")

    # Simulación de un teléfono
    with st.container(border=True):
        st.markdown("""
        <div style="background-color: #075E54; color: white; padding: 10px 15px; border-radius: 8px 8px 0 0; display: flex; align-items: center;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/7/7e/Circle-icons-profile.svg" style="height: 40px; width: 40px; border-radius: 50%; margin-right: 10px;">
            <b style="font-size: 1.1em;">Asistente Clínica Dental (En línea)</b>
        </div>
        """, unsafe_allow_html=True)

        chat_container = st.container(height=400)
        
        for message in st.session_state.chat_externo_messages:
            with chat_container.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Escribe tu consulta..."):
            st.session_state.chat_externo_messages.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user"):
                st.markdown(prompt)
            
            st.session_state.kpi_chat_consultas += 1 # KPI
            
            with chat_container.chat_message("assistant"):
                with st.spinner("IA procesando..."):
                    time.sleep(1.5)
                response = ""
                prompt_lower = prompt.lower()
                
                # --- Lógica de IA (Triage y Agendamiento) ---
                current_state = st.session_state.get('chat_externo_state', 'INIT')
                
                # ESTADO 1: Triage de Urgencia
                if 'emergencia' in prompt_lower or 'insoportable' in prompt_lower or 'sangrado' in prompt_lower:
                    response = "**Eso suena como una urgencia.** Por favor, llame de inmediato al **442-123-4567** para atención prioritaria. Estoy alertando al personal en este momento."
                    st.session_state.chat_externo_state = "URGENCIA"
                    st.session_state.kpi_chat_urgencias += 1 # KPI
                
                # ESTADO 2: Triage de Síntoma (Dolor de muela)
                elif 'dolor' in prompt_lower or 'muela' in prompt_lower or 'molestia' in prompt_lower and current_state == 'INIT':
                    response = "Lamento escuchar eso. Para ayudarte mejor, ¿el dolor es **1) Leve y ocasional** o **2) Constante y agudo**?"
                    st.session_state.chat_externo_state = "TRIAGE_DOLOR"
                
                # ESTADO 3: Ofrecer Cita (Respuesta al Triage)
                elif (prompt_lower in ['1', 'leve', 'ocasional', '2', 'constante', 'agudo']) and current_state == 'TRIAGE_DOLOR':
                    response = "Entendido. Lo mejor es una valoración. Déjame verificar la disponibilidad... \n\n¡Listo! Tengo 3 opciones disponibles:\n**1. Martes 17:00 (Dra. Vega)**\n**2. Miércoles 13:00 (Dr. Salas)**\n**3. Viernes 18:00 (Dra. Vega)**\n\n¿Alguna de estas opciones te funciona? (Solo escribe 1, 2 o 3)"
                    st.session_state.chat_externo_state = "OFERTA_CITA"
                
                # ESTADO 4: Confirmar Cita
                elif (prompt_lower in ['1', 'martes', '2', 'miércoles', '3', 'viernes']) and current_state == 'OFERTA_CITA':
                    opciones = {'1': 'Martes 17:00 (Dra. Vega)', '2': 'Miércoles 13:00 (Dr. Salas)', '3': 'Viernes 18:00 (Dra. Vega)'}
                    opcion_elegida = '1' if '1' in prompt_lower or 'martes' in prompt_lower else \
                                    '2' if '2' in prompt_lower or 'miércoles' in prompt_lower else '3'
                    cita_confirmada = opciones[opcion_elegida]

                    response = f"¡Perfecto! Tu cita está **CONFIRMADA** para el **{cita_confirmada}**. \n\nRecibirás un mensaje de **WhatsApp** en los próximos 2 minutos con la confirmación oficial y la dirección. \n\n¿Hay algo más en lo que pueda ayudarte?"
                    
                    # Añadir la cita al calendario real
                    nueva_cita = {
                        'ID Paciente': 'P_EXTERNO', 'Doctor': 'Dra. Vega' if 'Vega' in cita_confirmada else 'Dr. Salas', 
                        'Fecha': datetime.date.today() + datetime.timedelta(days=2) if 'Martes' in cita_confirmada else datetime.date.today() + datetime.timedelta(days=3), # Simulación de fecha
                        'Hora': '17:00' if '17:00' in cita_confirmada else '13:00' if '13:00' in cita_confirmada else '18:00', 
                        'Estado': 'Confirmada', 'Servicio': 'Valoración por Dolor (Chatbot)', 'Costo_Cita': 800
                    }
                    st.session_state.citas.append(nueva_cita)
                    st.session_state.chat_externo_state = "INIT" # Resetear estado
                    st.session_state.kpi_chat_citas_ia += 1 # KPI
                
                # Estado General
                elif 'horario' in prompt_lower or 'abren' in prompt_lower:
                    response = "Nuestros horarios de atención son de Lunes a Viernes de 9:00 AM a 7:00 PM."
                    st.session_state.chat_externo_state = "INIT"
                elif 'gracias' in prompt_lower:
                    response = "¡Un placer ayudarte! Estamos para servirte."
                    st.session_state.chat_externo_state = "INIT"
                else:
                    response = "No entendí tu consulta. Puedo ayudarte a agendar una cita por dolor de muela o a responder preguntas sobre nuestros horarios."
                    st.session_state.chat_externo_state = "INIT"
                
                st.markdown(response)
            st.session_state.chat_externo_messages.append({"role": "assistant", "content": response})


# ====================================================================================
# --- PÁGINA 5: REGISTROS CLÍNICOS (IA Rayos X) ---
# ====================================================================================
def render_registros_clinicos():
    st.title("🔬 Registros Clínicos (IA de Visión por Computadora)")
    st.info("""
    **Propósito del Módulo (Su Requerimiento):**
    Este es el expediente digital (EHR). Responde a su interés en usar 
    **IA de Visión por Computadora** como un "segundo par de ojos" para el diagnóstico.
    Es un módulo de alta seguridad que cumple con la **NOM-004** (Expediente Clínico).
    """)
    
    if not st.session_state.get('pacientes'):
        st.warning("No hay pacientes registrados.")
    else:
        paciente_options = [f"{p.get('ID', 'N/A')}: {p.get('Nombre', 'Paciente Desconocido')}" for p in st.session_state.pacientes]
        paciente_id_str = st.selectbox("Seleccionar Paciente", paciente_options)
        
        # --- KPIs del Módulo (Paciente Específico) ---
        st.subheader("KPIs del Paciente Seleccionado")
        paciente_obj = next((p for p in st.session_state.pacientes if p['ID'] == paciente_id_str.split(':')[0]), None)
        
        if paciente_obj:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Paciente", paciente_obj['Nombre'])
            col2.metric("Riesgo IA Detectado", paciente_obj['Riesgo IA'],
                        "Alto" if paciente_obj['Riesgo IA'] == 'Alto' else "normal")
            col3.metric("Tratamientos Históricos", paciente_obj['Tratamientos_Pasados'])
            col4.metric("Valor Histórico (Cartera)", f"${paciente_obj['Costo']:,.2f} MXN")
        st.divider()

        st.subheader("Odontograma (Simulación)")
        st.markdown("""
            <div style='border: 2px solid #005A9C; padding: 20px; text-align: center; background-color: #F0F2F6; height: 150px; display: flex; align-items: center; justify-content: center; font-size: 1.1em; font-weight: bold; color: #005A9C; border-radius: 8px;'>
                SIMULACIÓN DE ODONTOGRAMA INTERACTIVO (NOM-004)
            </div>
            """, unsafe_allow_html=True)
        st.caption("Aquí iría un odontograma interactivo para el registro de tratamientos por pieza.")
        st.divider()
        
        # --- MÓDULO DE IA DE RAYOS X (EL REQUERIMIENTO) ---
        st.subheader("Análisis de Rayos X con IA (Deep Learning)")
        st.markdown("Simulación de la funcionalidad de IA más avanzada.")
        
        uploaded_file = st.file_uploader("Cargar imagen de Rayos X (Simulación)", type=["jpg", "png"])
        
        if uploaded_file is not None:
            col_img, col_diag = st.columns(2)
            with col_img:
                st.image(uploaded_file, caption="Imagen de Rayos X cargada.", use_container_width=True)
            with col_diag:
                if st.button("Analizar Imagen (Simulación IA)"):
                    with st.spinner("La IA (modelo de Visión por Computadora) está analizando..."):
                        time.sleep(3)
                    st.success("Análisis IA Completado.")
                    st.warning("**Hallazgos de IA (Simulación):**\n- Detección de posible caries interproximal en pieza 3.6 (Confianza: 92%).\n- Sugerencia de revisión en pieza 4.5 por posible reabsorción ósea leve.")

# ====================================================================================
# --- PÁGINA 6: GESTIÓN INTERNA (ASPEL E INVENTARIO) ---
# ====================================================================================
def render_gestion_interna():
    st.title("📦 Gestión Interna (Inventario y Aspel)")
    st.info("""
    **Propósito del Módulo (Su Requerimiento):**
    Este módulo protege los ingresos y optimiza el flujo de caja. 
    Responde a su necesidad de **conectar la operación clínica con la facturación (Aspel)** y de predecir las necesidades de inventario.
    """)
    
    tab1, tab2 = st.tabs(["Inventario (Predicciones IA)", "Sincronización con Aspel"])
    
    with tab1:
        st.subheader("KPIs de Gestión de Inventario")
        df_inventario = pd.DataFrame.from_dict(st.session_state.inventario, orient='index')
        valor_total_stock = (df_inventario['Stock'] * df_inventario['Costo_Unitario']).sum()
        items_urgentes = len(df_inventario[df_inventario['Predicción IA'].str.contains('URGENTE')])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Valor Total del Inventario", f"${valor_total_stock:,.2f} MXN")
        col2.metric("Ítems en Nivel Crítico (IA)", f"{items_urgentes} ítems", "inverse" if items_urgentes > 0 else "normal")
        col3.metric("Proveedor Principal", df_inventario['Proveedor'].mode()[0])
        st.divider()

        st.subheader("Control de Inventario (Forecasting IA)")
        st.dataframe(
            df_inventario.style
            .format({"Costo_Unitario": "S{:,.2f} MXN"})
            .map(color_prediccion, subset=['Predicción IA']),
            use_container_width=True
        )
        
    with tab2:
        st.subheader("KPIs de Sincronización de Facturación")
        col1, col2 = st.columns(2)
        col1.metric("Monto Sincronizado (Hoy)", f"${st.session_state.kpi_aspel_sincronizado:,.2f} MXN")
        col2.metric("Monto Pendiente de Sincronizar", f"${st.session_state.kpi_aspel_pendiente:,.2f} MXN", "inverse")
        st.divider()

        st.subheader("Sincronizar Cobro con Aspel (Simulación)")
        st.markdown("Simulación de cómo, tras registrar un cobro, el SGC envía la información a Aspel para generar la factura.")
        
        if not st.session_state.pacientes:
            st.warning("No hay pacientes registrados.")
        else:
            paciente_cobro = st.selectbox("Paciente a cobrar", [p['Nombre'] for p in st.session_state.pacientes])
            paciente_obj = next(p for p in st.session_state.pacientes if p['Nombre'] == paciente_cobro)
            monto = st.number_input("Monto (MXN)", min_value=100.0, value=float(paciente_obj['Costo']), step=100.0)
            concepto = st.text_input("Concepto", paciente_obj['Servicio'])
            
            if st.button("Enviar Factura a ASPEL (API)"):
                with st.spinner("Conectando con API de Aspel... Enviando datos..."):
                    time.sleep(3)
                st.success(f"¡Sincronización Exitosa! Factura F-1236 para {paciente_cobro} (${monto:,.2f}) registrada en Aspel.")
                
                # --- INICIO DE LA CORRECCIÓN 'removeChild' ---
                # Actualizar KPIs
                st.session_state.kpi_aspel_sincronizado += monto
                if (st.session_state.kpi_aspel_pendiente - monto) < 0:
                    st.session_state.kpi_aspel_pendiente = 0.0
                else:
                    st.session_state.kpi_aspel_pendiente -= monto
                
                # Eliminamos 'st.rerun()' y lo reemplazamos por un mensaje
                st.info("Sincronización completada. El KPI 'Monto Pendiente' ha sido actualizado.")
                # st.rerun() # <--- ELIMINADO
                # --- FIN DE LA CORRECCIÓN ---


# ====================================================================================
# --- PÁGINA 7: PORTAL DEL PACIENTE (REQUERIMIENTO 2: FACTURACIÓN CLIENTE) ---
# ====================================================================================
def render_portal_paciente():
    st.title("👤 Portal del Paciente (Facturación y Citas)")
    st.warning("**VISIÓN DEL CLIENTE:** Este módulo simula la **única vista** que vería su paciente si entra a su página web para consultar su información.")
    st.info("""
    **Propósito del Módulo (Su Requerimiento):**
    Responde a su solicitud de tener un módulo de facturación separado para el cliente.
    Esto es un "Portal de Paciente" donde pueden auto-gestionarse, 
    ver su historial de pagos, sus próximas citas y **gestionar su privacidad**.
    """)

    st.subheader("Simulación de Inicio de Sesión del Paciente")
    
    # Simulación de Login
    paciente_options = {f"{p['ID']} - {p['Nombre']}": p for p in st.session_state.pacientes}
    paciente_login = st.selectbox("Seleccione un paciente para simular su vista:", paciente_options.keys())
    
    if paciente_login:
        paciente = paciente_options[paciente_login]
        st.divider()
        st.header(f"Bienvenido, {paciente['Nombre']}")
        
        # --- KPIs del Módulo (Vista de Paciente) ---
        citas_paciente = [c for c in st.session_state.citas if c['ID Paciente'] == paciente['ID'] and c['Fecha'] >= datetime.date.today()]
        facturas_pendientes = 0 # Simulado
        total_historico = paciente['Costo'] + 800 # Simulado
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Próximas Citas", len(citas_paciente))
        col2.metric("Facturas Pendientes", facturas_pendientes)
        col3.metric("Total Pagado (Histórico)", f"${total_historico:,.2f} MXN")
        
        # --- Pestañas del Portal ---
        tab_citas, tab_facturas, tab_privacidad = st.tabs(["Mis Próximas Citas", "Mi Historial de Facturación", "🔐 Mis Datos y Privacidad (ARCO)"])
        
        with tab_citas:
            if not citas_paciente:
                st.info("No tiene próximas citas agendadas.")
                st.button("Agendar Nueva Cita (Ir a WhatsApp)")
            else:
                for cita in citas_paciente:
                    st.success(f"**{cita['Servicio']}** con **{cita['Doctor']}**\n- **Fecha:** {cita['Fecha']}\n- **Hora:** {cita['Hora']}\n- **Estado:** {cita['Estado']}")
        
        with tab_facturas:
            st.markdown(f"Simulación del historial de pagos y facturas de {paciente['Nombre']}.")
            # Simulación de facturas
            facturas_data = [
                {"Fecha": "2025-10-15", "Concepto": paciente['Servicio'], "Monto": paciente['Costo'], "Estado": "Pagada", "CFDI": "Descargar"},
                {"Fecha": "2025-09-01", "Concepto": "Valoración", "Monto": 800, "Estado": "Pagada", "CFDI": "Descargar"}
            ]
            st.dataframe(facturas_data, use_container_width=True)

        # --- Pestaña de Cumplimiento LFPDPPP ---
        with tab_privacidad:
            st.subheader("Gestión de Datos Personales (Derechos ARCO)")
            st.markdown("En cumplimiento con la Ley de Protección de Datos Personales (LFPDPPP), usted tiene control sobre su información.")
            
            st.markdown("---")
            st.markdown("#### Derecho de Acceso y Rectificación")
            st.info(f"**Estado de Consentimiento:** {paciente['Aviso_Privacidad']}")
            if paciente['Aviso_Privacidad'] == 'Pendiente':
                st.warning("Aún no ha firmado nuestro aviso de privacidad para el manejo de sus datos sensibles de salud. Por favor, fírmelo en su próxima visita.")
            
            with st.expander("Ver Mis Datos Registrados (Acceso)"):
                st.json({
                    "Nombre": paciente['Nombre'],
                    "Teléfono": paciente['Telefono'],
                    "Historial Médico (Sensible)": paciente['Historial'],
                    "Servicio Principal": paciente['Servicio']
                })
            
            if st.button("Solicitar Corrección de Datos (Rectificación)"):
                st.success("Su solicitud de rectificación ha sido enviada. Nuestro personal se pondrá en contacto con usted para validarla.")

            st.markdown("---")
            st.markdown("#### Derecho de Cancelación y Oposición")
            if st.button("Solicitar Eliminación de mi Expediente (Cancelación)"):
                st.info("Su solicitud de cancelación será procesada. (Nota: Por la NOM-004, los expedientes clínicos deben conservarse 5 años. Pasado ese tiempo, se eliminarán).")

# ====================================================================================
# --- PÁGINA 8: CUMPLIMIENTO NORMATIVO (LFPDPPP Y NOM-004) --- (NUEVA PÁGINA)
# ====================================================================================
def render_cumplimiento_normativo():
    st.title("🛡️ Cumplimiento Normativo (LFPDPPP & NOM-004)")
    st.warning("Este módulo es uno de los **activos más valiosos** del sistema. Protege su clínica contra multas millonarias por mal manejo de datos sensibles.")
    st.info("""
    **Propósito del Módulo (Su Requerimiento):**
    Responde a su preocupación sobre el cumplimiento de las **leyes mexicanas de datos personales y expedientes clínicos**. 
    Demostramos cómo la arquitectura del SGC-IA está diseñada para cumplir con estas normas.
    """)

    # --- KPIs del Módulo ---
    st.subheader("KPIs de Cumplimiento y Auditoría")
    df_pacientes = pd.DataFrame(st.session_state.pacientes)
    total_pacientes = len(df_pacientes)
    consentimientos_firmados = len(df_pacientes[df_pacientes['Aviso_Privacidad'] == 'Firmado'])
    tasa_consentimiento = (consentimientos_firmados / total_pacientes) * 100 if total_pacientes > 0 else 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tasa de Consentimiento (LFPDPPP)", f"{tasa_consentimiento:.0f}%",
                help="Porcentaje de pacientes que han firmado el consentimiento de datos sensibles.")
    col2.metric("Pista de Auditoría (NOM-004)", "✅ Activa",
                help="El sistema registra CADA cambio en los expedientes clínicos.")
    col3.metric("Accesos No Autorizados (Hoy)", "0",
                help="Intentos de acceso bloqueados a datos sensibles.")
    col4.metric("Solicitudes ARCO Pendientes", "1", "inverse",
                help="Solicitudes de pacientes para rectificar o cancelar sus datos.")
    st.divider()

    tab_lfpdppp, tab_nom004 = st.tabs(["🔒 Ley de Protección de Datos (LFPDPPP)", "📋 Norma del Expediente Clínico (NOM-004)"])

    with tab_lfpdppp:
        st.subheader("Cumplimiento de la LFPDPPP (Datos Personales Sensibles)")
        st.markdown("""
        La LFPDPPP exige un manejo estricto de los "Datos Sensibles" (estado de salud). Un Excel o una libreta no cumplen con esto.
        
        **Nuestra Solución (SGC-IA):**
        
        1.  **Consentimiento Explícito:**
            - El SGC-IA fuerza la captura del consentimiento.
            - El `Portal del Paciente` permite la firma digital del Aviso de Privacidad.
            - El `Panel de Pacientes` (Pág 2) le alerta qué pacientes tienen el consentimiento **pendiente**.
        
        2.  **Seguridad (Arquitectura Cloud):**
            - Como se ve en la `Página 9 (Arquitectura)`, toda la base de datos está en la nube, no en computadoras locales vulnerables a robo o pérdida.
            - Toda la información viaja **encriptada (HTTPS)**.
            - La base de datos (PostgreSQL) está **encriptada en reposo (AES-256)**.
        
        3.  **Derechos ARCO (Acceso, Rectificación, Cancelación, Oposición):**
            - El `Portal del Paciente` (Pág 7) es la herramienta para que sus pacientes ejerzan sus derechos ARCO de forma digital y auditable.
        """)

    with tab_nom004:
        st.subheader("Cumplimiento de la NOM-004-SSA3-2012 (Expediente Clínico)")
        st.markdown("""
        La NOM-004 exige la Integridad, Confidencialidad y Conservación del expediente clínico.
        
        **Nuestra Solución (SGC-IA):**
        
        1.  **Confidencialidad (Gestión de Roles):**
            - El sistema implementa **roles y permisos**.
            - El personal de recepción **(Rol: Asistente)** puede ver la `Agenda` (Pág 3) y el `Chatbot` (Pág 4), pero **NO PUEDE** ver los `Registros Clínicos` (Pág 5).
            - Solo el personal médico **(Rol: Doctor)** puede acceder al historial clínico sensible.
        
        2.  **Integridad (Pista de Auditoría):**
            - Un expediente en papel o Excel se puede alterar. La NOM-004 lo prohíbe.
            - Nuestra base de datos (PostgreSQL) crea una **Pista de Auditoría (Audit Log)**.
            - **Simulación:** *Cada vez que usted guarda una nota en el odontograma, el sistema guarda un registro inalterable: `[Doctor: Dr. Salas] | [Fecha: 10-Nov-2025 10:15] | [Acción: MODIFICÓ] | [Paciente: P001] | [Campo: Nota Pieza 1.6]`.*
        
        3.  **Conservación (Backups Automatizados):**
            - La NOM-004 exige conservar los expedientes por **5 años** después del último acto médico.
            - La `Arquitectura Cloud` incluye **respaldos automáticos diarios** y una política de retención de 5 años, protegiéndola contra incendios, inundaciones o robo de equipo.
        """)

# ====================================================================================
# --- PÁGINA 9: ARQUITECTURA CLOUD (Acceso Múltiple) ---
# ====================================================================================
def render_arquitectura_cloud():
    st.title("☁️ Arquitectura Cloud (Acceso Múlti-Consultorio)")
    st.info("""
    **Propósito del Módulo (Su Requerimiento):**
    Este módulo responde a su necesidad crítica de **acceso 100% en la Nube**. 
    El sistema no será un software local, sino una plataforma web que 
    permite el acceso seguro desde sus múltiples consultorios y su domicilio.
    """)

    # --- KPIs del Módulo ---
    st.subheader("KPIs de Salud del Sistema (Simulados)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Estado del Sistema", "✅ Operacional")
    col2.metric("Tiempo de Actividad (Uptime)", "99.98%")
    col3.metric("Conexión API (WhatsApp)", "Activa", help="Conexión con Meta/Twilio.")
    col4.metric("Conexión API (Aspel)", "Activa", help="Conexión con sistema de facturación.")
    st.divider()

    st.subheader("Arquitectura de Sistema Propuesta (Enfocada en Seguridad)")
    st.graphviz_chart("""
    digraph SGC_IA_Cloud {
        rankdir="TB";
        bgcolor="transparent";
        node [shape=record, style="filled", fillcolor="#F0F2F6", color="#005A9C", fontname="Arial"];
        edge [color="#444444"];

        subgraph cluster_pacientes {
            label = "Pacientes (Usuarios Externos)";
            style="filled";
            fillcolor="#F9F9F9";
            color="#CCCCCC";
            paciente_wa [label="Paciente (WhatsApp)", shape=rect, fillcolor="#DCF8C6"];
            paciente_web [label="Paciente (Portal Web)", shape=rect, fillcolor="#E6F3FF"];
        }

        subgraph cluster_consultorios {
            label = "Personal de Clínica (Usuarios Internos)";
            style="filled";
            fillcolor="#F9F9F9";
            color="#CCCCCC";
            consultorio1 [label="Consultorio 1 (Recepción)\nRol: Asistente", shape=rect, fillcolor="#E6F3FF"];
            consultorio2 [label="Consultorio 2 (Doctor)\nRol: Médico", shape=rect, fillcolor="#E6F3FF"];
            domicilio [label="Admin (Domicilio)\nRol: Admin", shape=rect, fillcolor="#E6F3FF"];
        }

        subgraph cluster_cloud {
            label = "Plataforma en la Nube (AWS / Google Cloud) - Cumple LFPDPPP";
            style="filled";
            fillcolor="#F0F8FF";
            color="#007BFF";
            
            api_gateway [label="<f0> API Gateway | (Firewall y Control de Acceso)"];
            
            subgraph cluster_backend {
                label = "Backend (FastAPI)";
                api_backend [label="<f0> SGC-IA Backend |<f1> Lógica de Roles (Confidencialidad) |<f2> Conexión a IA"];
            }
            
            database [label="<f0> Base de Datos PostgreSQL |<f1> Datos Encriptados (AES-256) |<f2> Pista de Auditoría (NOM-004) |<f3> Respaldos 5 Años", shape=record];
            
            frontend [label="<f0> Frontend (Streamlit) |<f1> Dashboard |<f2> Paneles de Gestión", shape=record];
        }
        
        subgraph cluster_apis_externas {
            label = "APIs Externas";
            style="filled";
            fillcolor="#FFF9F0";
            color="#CCCCCC";
            api_wa [label="API WhatsApp (Twilio/Meta)", shape=rect, fillcolor="#FFF0E0"];
            api_aspel [label="API Aspel", shape=rect, fillcolor="#FFF0E0"];
            api_openai [label="API OpenAI (GPT-4)", shape=rect, fillcolor="#FFF0E0"];
        }

        // Conexiones
        {consultorio1, consultorio2, domicilio} -> api_gateway [label="Acceso Web (HTTPS Encriptado)"];
        paciente_wa -> api_wa [label="Mensaje"];
        paciente_web -> frontend [label="Visita Portal"];
        
        api_gateway -> frontend;
        api_gateway -> api_backend;
        
        frontend -> api_backend [label="Pide datos (Validado por Rol)"];
        api_backend -> database [label="Lee/Escribe (Genera Auditoría)"];
        
        api_backend -> api_wa [label="Responde WhatsApp"];
        api_backend -> api_aspel [label="Genera Factura"];
        api_backend -> api_openai [label="Procesa Chatbot"];
    }
    """)

# ====================================================================================
# --- EJECUCIÓN PRINCIPAL Y ENRUTADOR ---
# ====================================================================================

# --- Diccionario de Páginas (El "Enrutador" alineado a los requerimientos) ---
PAGES = {
    "📈 Panel de Control (KPIs Globales)": render_panel_control,
    "👥 Gestión de Pacientes (KPIs Cartera)": render_gestion_pacientes,
    "🗓️ Agenda y Calendario (KPIs Ocupación)": render_agenda_citas,
    "🤖 Chatbot de Pacientes (KPIs Conversión)": render_chatbot_paciente,
    "🔬 Registros Clínicos (KPIs Paciente)": render_registros_clinicos,
    "📦 Gestión Interna (KPIs Financieros)": render_gestion_interna,
    "👤 Portal del Paciente (KPIs Cliente)": render_portal_paciente,
    "🛡️ Cumplimiento Normativo (LFPDPPP & NOM-004)": render_cumplimiento_normativo,
    "☁️ Arquitectura Cloud (KPIs Sistema)": render_arquitectura_cloud
}

# --- Lógica de la Barra Lateral ---
logo_url = "https://media.licdn.com/dms/image/D4E0BAQG4V3f-9j-f9w/company-logo_200_200/0/1691361099195/integral360_logo?e=1736515200&v=beta&t=M8-jL41-XG9GIfd-s22FvBljPq2bVwW-fexqLqN0Gok"
try:
    st.sidebar.image(logo_url, use_container_width=True) 
except Exception as e:
    st.sidebar.error("Logo no encontrado.")

st.sidebar.title("🦷 SGC Odontológico (Demo)")
st.sidebar.markdown("**Plataforma de Validación de Valor (KPIs)**")

# --- Menú de Navegación ---
pagina_seleccionada = st.sidebar.radio("Módulos del Sistema:", list(PAGES.keys()))

st.sidebar.divider()
st.sidebar.caption(f"© {datetime.date.today().year} Integral360.")
st.sidebar.caption("Demo v5.1 (Maestro + Fix 'removeChild')") # Actualizado

# --- Inicializar Datos ---
inicializar_datos()

# --- Verificar Librería de Calendario ---
if not CALENDAR_ENABLED and pagina_seleccionada == "🗓️ Agenda y Calendario (KPIs Ocupación)":
    st.error("Módulo de Calendario deshabilitado. No se pudo importar 'streamlit-calendar'.")
    st.code("Instale esta librería en su venv: pip install streamlit-calendar")
else:
    # --- Ejecutar la función de la página seleccionada ---
    page_function = PAGES[pagina_seleccionada]
    page_function()

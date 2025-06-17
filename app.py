import streamlit as st
import json
from datetime import datetime
from fpdf import FPDF
from pathlib import Path
import re
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Generador de Presupuestos",
    page_icon="💼",
    layout="centered"
)

# --- CONSTANTES Y RUTAS ---
IVA_RATE = 0.21
FONT_FAMILY = "DejaVu"
# NOTA: Asegúrate de que estos archivos .ttf están en la misma carpeta que app.py
FONT_REGULAR_PATH = str(Path(__file__).parent / "DejaVuSansCondensed.ttf")
FONT_BOLD_PATH = str(Path(__file__).parent / "DejaVuSansCondensed-Bold.ttf")

# --- CLASE PARA LA GENERACIÓN DEL PDF con FPDF2 ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datos_empresa = {}
        self.datos_cliente = {}
        self.detalles_presupuesto = {}
        self.logo_path = ""

    def add_fonts(self):
        """Añade las fuentes Unicode necesarias para el PDF."""
        try:
            self.add_font(FONT_FAMILY, '', FONT_REGULAR_PATH)
            self.add_font(FONT_FAMILY, 'B', FONT_BOLD_PATH)
        except Exception as e:
            st.error(f"Error al cargar las fuentes: {e}")
            st.warning("Asegúrate de que los archivos 'DejaVuSansCondensed.ttf' y 'DejaVuSansCondensed-Bold.ttf' están en la misma carpeta que la aplicación.")

    def header(self):
        """Define el encabezado del documento PDF."""
        if not self.datos_empresa:
            return

        # --- Logo ---
        if self.logo_path and Path(self.logo_path).exists():
            try:
                # Obtenemos el tamaño de la imagen para centrarla correctamente
                with Image.open(self.logo_path) as img:
                    img_w, img_h = img.size
                
                # Proporción para que no supere un ancho máximo
                max_w = 80
                ratio = max_w / img_w
                new_w, new_h = max_w, img_h * ratio
                
                # Centrar imagen
                self.image(self.logo_path, x=(210 - new_w) / 2, y=10, w=new_w)
                self.ln(new_h / 2) # Espacio después del logo
            except Exception as e:
                self.set_font(FONT_FAMILY, 'B', 10)
                self.cell(0, 10, f"Error al cargar logo: {e}", 0, 1, 'C')
        
        self.ln(10)

        # --- Datos de la Empresa y Cliente ---
        self.set_font(FONT_FAMILY, 'B', 9)
        col_width = 95  # Ancho de cada columna (total 190 para A4)

        # Datos Empresa (Izquierda)
        y_before = self.get_y()
        self.cell(col_width, 5, "DATOS DE LA EMPRESA", 0, 0, 'L')
        self.cell(col_width, 5, "DATOS DEL CLIENTE", 0, 1, 'L')
        self.set_font(FONT_FAMILY, '', 9)
        
        y_after_header = self.get_y()
        
        # Columna Empresa
        self.multi_cell(col_width, 5, f"{self.datos_empresa.get('nombre', '')}\n"
                                     f"NIF/CIF: {self.datos_empresa.get('nif', '')}\n"
                                     f"{self.datos_empresa.get('direccion', '')}\n"
                                     f"Tel: {self.datos_empresa.get('telefono', '')}\n"
                                     f"Email: {self.datos_empresa.get('email', '')}", 0, 'L')
        
        y_empresa = self.get_y()
        self.set_y(y_after_header) # Volver al inicio de las celdas de datos

        # Columna Cliente (Derecha)
        self.set_x(10 + col_width) # Mover a la segunda columna
        self.multi_cell(col_width, 5, f"{self.datos_cliente.get('nombre', '')}\n"
                                     f"DNI/NIF: {self.datos_cliente.get('nif', '')}\n"
                                     f"{self.datos_cliente.get('direccion', '')}", 0, 'L')

        # Asegurarse de que el cursor Y esté después de la celda más larga
        self.set_y(max(y_empresa, self.get_y()) + 5)


    def footer(self):
        """Define el pie de página del documento."""
        self.set_y(-20)
        self.set_font(FONT_FAMILY, '', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Gracias por su confianza.', 0, 0, 'C')
    
    def create_body(self, conceptos, base_imponible, iva, total, aplicar_iva, notas):
        """Crea el cuerpo principal del presupuesto."""
        
        # --- Título y Detalles del Presupuesto ---
        self.ln(10)
        self.set_font(FONT_FAMILY, 'B', 14)
        self.cell(0, 10, 'PRESUPUESTO', 0, 1, 'R')
        self.set_font(FONT_FAMILY, '', 10)
        self.cell(0, 5, f"Nº Presupuesto: {self.detalles_presupuesto.get('numero', '')}", 0, 1, 'R')
        self.cell(0, 5, f"Fecha: {self.detalles_presupuesto.get('fecha', '')}", 0, 1, 'R')
        self.ln(10)

        # --- Tabla de Conceptos ---
        self.set_font(FONT_FAMILY, 'B', 9)
        self.set_fill_color(220, 220, 220) # Gris claro para la cabecera
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.3)

        # Cabeceras de la tabla
        w_desc = 110
        w_cant = 20
        w_precio = 30
        w_total = 30
        self.cell(w_desc, 7, "Descripción", 1, 0, 'C', 1)
        self.cell(w_cant, 7, "Cantidad", 1, 0, 'C', 1)
        self.cell(w_precio, 7, "P. Unitario (€)", 1, 0, 'C', 1)
        self.cell(w_total, 7, "Total (€)", 1, 1, 'C', 1)

        # Filas de la tabla
        self.set_font(FONT_FAMILY, '', 9)
        fill = False # Para alternar colores de fondo
        for item in conceptos:
            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)
            
            # Guardar Y actual para manejar multilínea
            y_start = self.get_y()
            
            # La celda de descripción puede ser multilínea
            self.multi_cell(w_desc, 6, item['descripcion'], border='LR', align='L', fill=fill)
            
            y_end_desc = self.get_y()
            height = y_end_desc - y_start
            
            # Restaurar Y y mover X para las otras celdas
            self.set_y(y_start)
            self.set_x(self.get_x() + w_desc)

            self.cell(w_cant, height, str(item['cantidad']), 'LR', 0, 'C', fill)
            self.cell(w_precio, height, f"{item['precio']:.2f}", 'LR', 0, 'R', fill)
            self.cell(w_total, height, f"{item['total']:.2f}", 'LR', 1, 'R', fill)

            fill = not fill # Alternar color

        # Línea inferior de la tabla
        self.cell(w_desc + w_cant + w_precio + w_total, 0, '', 'T', 1)
        self.ln(5)

        # --- Resumen de Totales ---
        total_width = w_precio + w_total
        self.set_x(10 + w_desc + w_cant) # Alinear a la derecha
        self.set_font(FONT_FAMILY, '', 10)
        
        self.cell(w_precio, 7, "Base Imponible:", 0, 0, 'R')
        self.cell(w_total, 7, f"{base_imponible:.2f} €", 'B', 1, 'R')
        
        if aplicar_iva:
            self.set_x(10 + w_desc + w_cant)
            self.cell(w_precio, 7, f"IVA ({int(IVA_RATE*100)}%):", 0, 0, 'R')
            self.cell(w_total, 7, f"{iva:.2f} €", 'B', 1, 'R')
        
        self.set_x(10 + w_desc + w_cant)
        self.set_font(FONT_FAMILY, 'B', 12) # TOTAL en negrita y más grande
        self.cell(w_precio, 8, "TOTAL:", 0, 0, 'R')
        self.cell(w_total, 8, f"{total:.2f} €", 'B', 1, 'R')
        
        # --- Notas y Condiciones ---
        if notas:
            self.set_y(self.get_y() + 10)
            self.set_font(FONT_FAMILY, 'B', 9)
            self.cell(0, 7, "Notas y Condiciones:", 0, 1, 'L')
            self.set_font(FONT_FAMILY, '', 9)
            self.multi_cell(0, 5, notas, border='T')


# --- FUNCIONES AUXILIARES ---
def safe_float(value):
    """Convierte de forma segura un valor a float. Si falla, devuelve 0.0."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def initialize_session_state():
    """Inicializa el estado de la sesión si no existe."""
    default_state = {
        'datos_empresa': {'nombre': '', 'nif': '', 'direccion': '', 'telefono': '', 'email': '', 'logo_path': 'logo.png'},
        'datos_cliente': {'nombre': '', 'nif': '', 'direccion': ''},
        'detalles_presupuesto': {'numero': '', 'fecha': datetime.now().strftime('%d/%m/%Y')},
        'conceptos': [],
        'aplicar_iva': True,
        'notas': 'Forma de pago: 50% al aceptar el presupuesto, 50% a la entrega.\nValidez del presupuesto: 30 días.',
        'base_imponible': 0.0,
        'iva': 0.0,
        'total': 0.0,
        'pdf_buffer': None,
        'json_buffer': None
    }
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

def calculate_totals():
    """Calcula y actualiza los totales en el estado de la sesión."""
    base_imponible = sum(safe_float(item.get('cantidad', 0)) * safe_float(item.get('precio', 0)) for item in st.session_state.conceptos)
    
    # Actualizar el total de cada item
    for item in st.session_state.conceptos:
        item['total'] = safe_float(item.get('cantidad', 0)) * safe_float(item.get('precio', 0))

    iva = base_imponible * IVA_RATE if st.session_state.aplicar_iva else 0.0
    total = base_imponible + iva
    
    st.session_state.base_imponible = base_imponible
    st.session_state.iva = iva
    st.session_state.total = total

def add_concepto():
    """Añade una nueva fila de concepto vacía."""
    st.session_state.conceptos.append({'descripcion': '', 'cantidad': 1, 'precio': 0.0, 'total': 0.0})
    calculate_totals()

def remove_concepto(index):
    """Elimina un concepto por su índice."""
    if 0 <= index < len(st.session_state.conceptos):
        st.session_state.conceptos.pop(index)
        calculate_totals()
        # st.experimental_rerun() -> Ya no es estrictamente necesario en versiones modernas
        # pero se deja como comentario por si hiciera falta en algún caso extremo.

def load_from_json(uploaded_file):
    """Carga los datos del presupuesto desde un archivo JSON."""
    try:
        data = json.load(uploaded_file)
        
        # Limpiar buffers para evitar descargas de archivos antiguos
        st.session_state.pdf_buffer = None
        st.session_state.json_buffer = None

        # Cargar datos, usando .get() para evitar errores si una clave no existe
        st.session_state.datos_empresa = data.get('datos_empresa', st.session_state.datos_empresa)
        st.session_state.datos_cliente = data.get('datos_cliente', st.session_state.datos_cliente)
        st.session_state.detalles_presupuesto = data.get('detalles_presupuesto', st.session_state.detalles_presupuesto)
        st.session_state.conceptos = data.get('conceptos', [])
        st.session_state.aplicar_iva = data.get('aplicar_iva', True)
        st.session_state.notas = data.get('notas', '')

        calculate_totals()
        st.success("Presupuesto cargado correctamente desde el archivo JSON.")
    except Exception as e:
        st.error(f"Error al leer el archivo JSON: {e}")
        st.exception(e)


# --- INTERFAZ DE USUARIO (UI) ---

# Inicializar estado al principio de la ejecución
initialize_session_state()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("logo.png", width=150) # Muestra el logo en la sidebar también
    st.title("Opciones")
    
    st.subheader("Cargar Presupuesto")
    uploaded_file = st.file_uploader(
        "Cargar Presupuesto para Editar (.json)",
        type="json",
        help="Sube un archivo JSON generado por esta aplicación para continuar editándolo."
    )
    if uploaded_file:
        load_from_json(uploaded_file)


# --- TÍTULO PRINCIPAL ---
st.title("📊 Generador de Presupuestos Profesional")
st.markdown("Rellena los campos a continuación para crear tu presupuesto. Los cambios se guardan automáticamente.")

# --- FORMULARIO PRINCIPAL ---
with st.form(key="budget_form"):
    
    # --- SECCIÓN DATOS EMPRESA Y CLIENTE (en dos columnas) ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 Tus Datos")
        st.session_state.datos_empresa['nombre'] = st.text_input("Nombre de tu Empresa", value=st.session_state.datos_empresa['nombre'])
        st.session_state.datos_empresa['nif'] = st.text_input("NIF/CIF", value=st.session_state.datos_empresa['nif'])
        st.session_state.datos_empresa['direccion'] = st.text_area("Dirección", value=st.session_state.datos_empresa['direccion'], height=100)
        st.session_state.datos_empresa['telefono'] = st.text_input("Teléfono", value=st.session_state.datos_empresa['telefono'])
        st.session_state.datos_empresa['email'] = st.text_input("Email", value=st.session_state.datos_empresa['email'])
        st.session_state.datos_empresa['logo_path'] = st.text_input("Nombre archivo del Logo", value=st.session_state.datos_empresa['logo_path'], help="Ej: logo.png. El archivo debe estar en la misma carpeta.")

    with col2:
        st.subheader("👤 Datos del Cliente")
        st.session_state.datos_cliente['nombre'] = st.text_input("Nombre del Cliente", value=st.session_state.datos_cliente['nombre'])
        st.session_state.datos_cliente['nif'] = st.text_input("DNI/NIF del Cliente", value=st.session_state.datos_cliente['nif'])
        st.session_state.datos_cliente['direccion'] = st.text_area("Dirección del Cliente", value=st.session_state.datos_cliente['direccion'], height=100)

    st.divider()

    # --- SECCIÓN DETALLES DEL PRESUPUESTO ---
    st.subheader("📑 Detalles del Presupuesto")
    col_det1, col_det2 = st.columns([1, 1])
    with col_det1:
        st.session_state.detalles_presupuesto['numero'] = st.text_input("Número de Presupuesto", value=st.session_state.detalles_presupuesto['numero'])
    with col_det2:
        # La fecha se convierte a objeto datetime para el widget y se formatea de vuelta a string
        try:
            fecha_obj = datetime.strptime(st.session_state.detalles_presupuesto['fecha'], '%d/%m/%Y')
        except ValueError:
            fecha_obj = datetime.now()
        
        nueva_fecha = st.date_input("Fecha del Presupuesto", value=fecha_obj, format="DD/MM/YYYY")
        st.session_state.detalles_presupuesto['fecha'] = nueva_fecha.strftime('%d/%m/%Y')
    
    st.divider()

    # --- SECCIÓN DE CONCEPTOS (ITEMS) ---
    st.subheader("📦 Conceptos")

    # Mostrar cabeceras fuera del bucle
    col_desc, col_cant, col_precio, col_total_item, col_del = st.columns([4, 1, 1.5, 1.5, 0.5])
    with col_desc:
        st.markdown("**Descripción**")
    with col_cant:
        st.markdown("**Cantidad**")
    with col_precio:
        st.markdown("**Precio (€)**")
    with col_total_item:
        st.markdown("**Total (€)**")

    # Bucle para mostrar cada concepto
    for i, item in enumerate(st.session_state.conceptos):
        col_desc, col_cant, col_precio, col_total_item, col_del = st.columns([4, 1, 1.5, 1.5, 0.5])
        
        with col_desc:
            st.session_state.conceptos[i]['descripcion'] = st.text_input(f"desc_{i}", value=item['descripcion'], label_visibility="collapsed")
        with col_cant:
            # Validación numérica implícita al usar st.number_input
            st.session_state.conceptos[i]['cantidad'] = st.number_input(f"cant_{i}", value=item['cantidad'], min_value=0, step=1, label_visibility="collapsed", on_change=calculate_totals)
        with col_precio:
            st.session_state.conceptos[i]['precio'] = st.number_input(f"precio_{i}", value=safe_float(item['precio']), min_value=0.0, step=0.01, format="%.2f", label_visibility="collapsed", on_change=calculate_totals)
        with col_total_item:
            # Muestra el total del item, no es un campo de entrada
            total_item = safe_float(st.session_state.conceptos[i]['cantidad']) * safe_float(st.session_state.conceptos[i]['precio'])
            st.session_state.conceptos[i]['total'] = total_item
            st.text(f"{total_item:.2f}")

        with col_del:
            st.button("❌", key=f"del_{i}", on_click=remove_concepto, args=(i,), help="Eliminar este concepto")
    
    if st.button("➕ Añadir Concepto", on_click=add_concepto):
        pass # La lógica está en la función on_click

    st.divider()

    # --- SECCIÓN FINALES Y TOTALES ---
    col_final1, col_final2 = st.columns([2, 1])
    with col_final1:
        st.subheader("📝 Notas y Opciones")
        st.session_state.aplicar_iva = st.checkbox("Calcular IVA (21%)", value=st.session_state.aplicar_iva, on_change=calculate_totals)
        st.session_state.notas = st.text_area("Notas y Condiciones", value=st.session_state.notas, height=150)

    with col_final2:
        st.subheader("💰 Resumen")
        
        # Recalcular por si acaso antes de mostrar
        calculate_totals()
        
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #f9f9f9;">
            <p style="margin: 0;"><strong>Base Imponible:</strong> <span style="float: right;">{st.session_state.base_imponible:.2f} €</span></p>
            <p style="margin: 0;"><strong>IVA (21%):</strong> <span style="float: right;">{st.session_state.iva:.2f} €</span></p>
            <hr>
            <h3 style="margin: 0;">TOTAL: <span style="float: right;">{st.session_state.total:.2f} €</span></h3>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- BOTÓN DE ENVÍO DEL FORMULARIO ---
    submitted = st.form_submit_button("✅ GENERAR PRESUPUESTO", use_container_width=True, type="primary")


# --- LÓGICA POST-ENVÍO (FUERA DEL FORMULARIO) ---
if submitted:
    # Validar que al menos el nombre del cliente y un concepto existan
    if not st.session_state.datos_cliente['nombre'] or not st.session_state.conceptos:
        st.warning("⚠️ Por favor, introduce al menos el nombre del cliente y un concepto.")
    else:
        with st.spinner("Generando documentos... por favor, espera."):
            try:
                # 1. Recopilar todos los datos en un único diccionario
                presupuesto_data = {
                    "datos_empresa": st.session_state.datos_empresa,
                    "datos_cliente": st.session_state.datos_cliente,
                    "detalles_presupuesto": st.session_state.detalles_presupuesto,
                    "conceptos": st.session_state.conceptos,
                    "aplicar_iva": st.session_state.aplicar_iva,
                    "notas": st.session_state.notas,
                    "base_imponible": st.session_state.base_imponible,
                    "iva": st.session_state.iva,
                    "total": st.session_state.total,
                }
                
                # 2. Generar el PDF
                pdf = PDF()
                pdf.add_fonts()
                pdf.set_auto_page_break(auto=True, margin=25)
                # Pasar datos a la clase PDF
                pdf.datos_empresa = presupuesto_data["datos_empresa"]
                pdf.datos_cliente = presupuesto_data["datos_cliente"]
                pdf.detalles_presupuesto = presupuesto_data["detalles_presupuesto"]
                pdf.logo_path = presupuesto_data["datos_empresa"].get("logo_path", "logo.png")
                
                pdf.add_page()
                pdf.create_body(
                    conceptos=presupuesto_data["conceptos"],
                    base_imponible=presupuesto_data["base_imponible"],
                    iva=presupuesto_data["iva"],
                    total=presupuesto_data["total"],
                    aplicar_iva=presupuesto_data["aplicar_iva"],
                    notas=presupuesto_data["notas"]
                )
                
                # Guardar PDF en un buffer en memoria
                pdf_output_bytes = pdf.output(dest='S').encode('latin-1')
                st.session_state.pdf_buffer = pdf_output_bytes
                
                # 3. Generar el JSON
                json_output_string = json.dumps(presupuesto_data, indent=4)
                st.session_state.json_buffer = json_output_string
                
                st.success("¡Presupuesto generado con éxito! Ya puedes descargar los archivos.")

            except Exception as e:
                st.error("Ha ocurrido un error al generar el PDF.")
                st.exception(e) # Muestra el traceback del error para depuración


# --- BOTONES DE DESCARGA (se muestran si los buffers tienen datos) ---
if st.session_state.get('pdf_buffer') and st.session_state.get('json_buffer'):
    
    # Limpiar nombre de cliente y número de presupuesto para el nombre del archivo
    cliente_limpio = re.sub(r'[^a-zA-Z0-9_]', '', st.session_state.datos_cliente['nombre'].replace(' ', '_'))
    numero_limpio = re.sub(r'[^a-zA-Z0-9_]', '', st.session_state.detalles_presupuesto['numero'])
    file_name_base = f"Presupuesto_{numero_limpio}_{cliente_limpio}"

    st.subheader("📥 Descargar Archivos Generados")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📄 Descargar PDF",
            data=st.session_state.pdf_buffer,
            file_name=f"{file_name_base}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col_dl2:
        st.download_button(
            label="💾 Descargar Plantilla JSON",
            data=st.session_state.json_buffer,
            file_name=f"{file_name_base}.json",
            mime="application/json",
            use_container_width=True
        )

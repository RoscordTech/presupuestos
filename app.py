# -*- coding: utf-8 -*-

import streamlit as st
from fpdf import FPDF
from datetime import datetime
import json
import re
import os
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Generador de Presupuestos",
    page_icon="📄",
    layout="centered",
)

# --- CLASE PDF PERSONALIZADA (con fpdf2) ---
# Hereda de FPDF para crear una plantilla base con encabezado y pie de página
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datos_empresa = {}
        self.datos_cliente = {}
        self.logo_path = ""

    def set_datos(self, datos_empresa, datos_cliente, logo_path):
        """Guarda los datos de la empresa y cliente para usarlos en el header."""
        self.datos_empresa = datos_empresa
        self.datos_cliente = datos_cliente
        self.logo_path = logo_path

    def header(self):
        """Define el encabezado del PDF."""
        # Cargar fuentes Unicode
        self.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)

        # --- Logo ---
        # Centrado en la parte superior. Se ajusta el tamaño si existe.
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # Usar Pillow para obtener las dimensiones y mantener la proporción
                with Image.open(self.logo_path) as img:
                    img_w, img_h = img.size
                    aspect_ratio = img_h / img_w
                    logo_width = 50 # Ancho deseado del logo
                    logo_height = logo_width * aspect_ratio
                    # Centrar el logo
                    self.image(self.logo_path, x=(210 - logo_width) / 2, y=10, w=logo_width)
            except Exception as e:
                # No se pudo cargar el logo, se puede mostrar un warning en la app
                pass # El PDF se genera sin logo
        
        self.set_y(40) # Moverse hacia abajo para dejar espacio al logo

        # --- Datos de Empresa y Cliente ---
        self.set_font('DejaVu', '', 10)
        
        # Guardar la posición inicial Y
        top_y = self.get_y()
        
        # Columna de la Empresa (Izquierda)
        self.set_xy(10, top_y)
        self.multi_cell(90, 5, 
            f"{self.datos_empresa.get('nombre', '')}\n"
            f"NIF/CIF: {self.datos_empresa.get('nif', '')}\n"
            f"{self.datos_empresa.get('direccion', '')}\n"
            f"Tel: {self.datos_empresa.get('telefono', '')}\n"
            f"Email: {self.datos_empresa.get('email', '')}",
            border=0, align='L'
        )
        
        # Columna del Cliente (Derecha)
        self.set_xy(110, top_y)
        self.multi_cell(90, 5, 
            f"CLIENTE:\n"
            f"{self.datos_cliente.get('nombre', '')}\n"
            f"DNI/NIF: {self.datos_cliente.get('nif', '')}\n"
            f"{self.datos_cliente.get('direccion', '')}",
            border=0, align='L'
        )
        
        # Espacio después del encabezado
        self.ln(20)

    def footer(self):
        """Define el pie de página del PDF."""
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.cell(0, 10, 'Gracias por su confianza.', 0, 0, 'C')

# --- FUNCIONES AUXILIARES ---

def inicializar_estado():
    """Inicializa st.session_state si no existe."""
    if 'conceptos' not in st.session_state:
        st.session_state.conceptos = [{'descripcion': '', 'cantidad': 1.0, 'precio': 0.0}]
    
    # Datos de la empresa
    if 'empresa_nombre' not in st.session_state: st.session_state.empresa_nombre = ""
    if 'empresa_nif' not in st.session_state: st.session_state.empresa_nif = ""
    if 'empresa_direccion' not in st.session_state: st.session_state.empresa_direccion = ""
    if 'empresa_telefono' not in st.session_state: st.session_state.empresa_telefono = ""
    if 'empresa_email' not in st.session_state: st.session_state.empresa_email = ""
    if 'empresa_logo' not in st.session_state: st.session_state.empresa_logo = "logo.png"

    # Datos del cliente
    if 'cliente_nombre' not in st.session_state: st.session_state.cliente_nombre = ""
    if 'cliente_nif' not in st.session_state: st.session_state.cliente_nif = ""
    if 'cliente_direccion' not in st.session_state: st.session_state.cliente_direccion = ""

    # Detalles del presupuesto
    if 'presupuesto_numero' not in st.session_state: st.session_state.presupuesto_numero = ""
    if 'presupuesto_fecha' not in st.session_state: st.session_state.presupuesto_fecha = datetime.now().strftime("%d/%m/%Y")
    
    # Opciones
    if 'aplicar_iva' not in st.session_state: st.session_state.aplicar_iva = True
    if 'notas' not in st.session_state: st.session_state.notas = "Validez del presupuesto: 30 días.\nForma de pago: 50% a la aceptación, 50% a la entrega."

    # Estado de la generación de archivos
    if 'pdf_generado' not in st.session_state: st.session_state.pdf_generado = None
    if 'json_generado' not in st.session_state: st.session_state.json_generado = None
    if 'nombres_archivos' not in st.session_state: st.session_state.nombres_archivos = {}

def limpiar_nombre_archivo(nombre):
    """Limpia una cadena para que sea un nombre de archivo válido."""
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', nombre)

def cargar_datos_desde_json(archivo_cargado):
    """Carga los datos de un archivo JSON y actualiza el estado de la sesión."""
    try:
        datos = json.load(archivo_cargado)
        
        st.session_state.empresa_nombre = datos.get('empresa', {}).get('nombre', '')
        st.session_state.empresa_nif = datos.get('empresa', {}).get('nif', '')
        st.session_state.empresa_direccion = datos.get('empresa', {}).get('direccion', '')
        st.session_state.empresa_telefono = datos.get('empresa', {}).get('telefono', '')
        st.session_state.empresa_email = datos.get('empresa', {}).get('email', '')
        st.session_state.empresa_logo = datos.get('empresa', {}).get('logo_path', 'logo.png')
        
        st.session_state.cliente_nombre = datos.get('cliente', {}).get('nombre', '')
        st.session_state.cliente_nif = datos.get('cliente', {}).get('nif', '')
        st.session_state.cliente_direccion = datos.get('cliente', {}).get('direccion', '')

        st.session_state.presupuesto_numero = datos.get('detalles', {}).get('numero', '')
        st.session_state.presupuesto_fecha = datos.get('detalles', {}).get('fecha', datetime.now().strftime("%d/%m/%Y"))
        
        st.session_state.conceptos = datos.get('conceptos', [{'descripcion': '', 'cantidad': 1.0, 'precio': 0.0}])
        
        st.session_state.aplicar_iva = datos.get('opciones', {}).get('aplicar_iva', True)
        st.session_state.notas = datos.get('opciones', {}).get('notas', '')
        
        st.success("✅ Presupuesto cargado correctamente.")
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo JSON: {e}")

def crear_pdf_presupuesto(datos_presupuesto):
    """Genera el archivo PDF con los datos del presupuesto."""
    pdf = PDF()
    pdf.set_datos(
        datos_presupuesto['empresa'], 
        datos_presupuesto['cliente'], 
        datos_presupuesto['empresa']['logo_path']
    )
    pdf.add_page()
    
    # --- Título y Detalles del Presupuesto ---
    pdf.set_font('DejaVu', 'B', 14)
    pdf.cell(0, 10, 'PRESUPUESTO', 0, 1, 'R')
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 5, f"Nº Presupuesto: {datos_presupuesto['detalles']['numero']}", 0, 1, 'R')
    pdf.cell(0, 5, f"Fecha: {datos_presupuesto['detalles']['fecha']}", 0, 1, 'R')
    pdf.ln(10)

    # --- Tabla de Conceptos ---
    pdf.set_font('DejaVu', 'B', 10)
    pdf.set_fill_color(220, 220, 220) # Color de fondo para la cabecera
    
    # Cabeceras de la tabla
    col_widths = {'desc': 110, 'cant': 20, 'precio': 30, 'total': 30}
    pdf.cell(col_widths['desc'], 8, 'Descripción', 1, 0, 'C', fill=True)
    pdf.cell(col_widths['cant'], 8, 'Cantidad', 1, 0, 'C', fill=True)
    pdf.cell(col_widths['precio'], 8, 'P. Unitario (€)', 1, 0, 'C', fill=True)
    pdf.cell(col_widths['total'], 8, 'Total (€)', 1, 1, 'C', fill=True)
    
    pdf.set_font('DejaVu', '', 10)
    fill = False # Para alternar colores de fila
    
    # Contenido de la tabla
    for item in datos_presupuesto['conceptos']:
        pdf.set_fill_color(245, 245, 245) # Color de fondo para filas
        
        # Guardar posición actual para MultiCell
        x_pos = pdf.get_x()
        y_pos = pdf.get_y()
        
        # La descripción puede ocupar varias líneas
        pdf.multi_cell(col_widths['desc'], 8, str(item['descripcion']), border='LR', align='L', fill=fill)
        
        # Calcular la altura de la celda de descripción para alinear las otras
        y_after_multicell = pdf.get_y()
        cell_height = y_after_multicell - y_pos
        
        # Restaurar posición y dibujar las otras celdas con la altura correcta
        pdf.set_xy(x_pos + col_widths['desc'], y_pos)
        pdf.cell(col_widths['cant'], cell_height, str(item['cantidad']), 1, 0, 'C', fill=fill)
        pdf.cell(col_widths['precio'], cell_height, f"{item['precio']:.2f}", 1, 0, 'R', fill=fill)
        pdf.cell(col_widths['total'], cell_height, f"{item['total']:.2f}", 1, 1, 'R', fill=fill)
        
        fill = not fill # Alternar color para la siguiente fila

    # Dibujar la línea inferior de la tabla
    pdf.cell(sum(col_widths.values()), 0, '', 'T', 1)

    # --- Resumen de Totales ---
    pdf.ln(5)
    
    # Guardar la X para alinear a la derecha
    x_pos_total = pdf.get_x()
    
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(130, 8, 'Base Imponible:', 0, 0, 'R')
    pdf.cell(60, 8, f"{datos_presupuesto['resumen']['base_imponible']:.2f} €", 0, 1, 'R')
    
    if datos_presupuesto['opciones']['aplicar_iva']:
        pdf.cell(130, 8, 'IVA (21%):', 0, 0, 'R')
        pdf.cell(60, 8, f"{datos_presupuesto['resumen']['iva']:.2f} €", 0, 1, 'R')

    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(130, 8, 'TOTAL:', 0, 0, 'R')
    pdf.cell(60, 8, f"{datos_presupuesto['resumen']['total']:.2f} €", 0, 1, 'R')
    
    # --- Notas y Condiciones ---
    if datos_presupuesto['opciones']['notas']:
        pdf.ln(10)
        pdf.set_font('DejaVu', 'B', 10)
        pdf.cell(0, 8, 'Notas y Condiciones:', 0, 1, 'L')
        pdf.set_font('DejaVu', '', 9)
        pdf.multi_cell(0, 5, datos_presupuesto['opciones']['notas'], border=0, align='L')

    # Retornar el PDF como bytes
    return pdf.output(dest='S').encode('latin-1')


# --- INTERFAZ DE USUARIO CON STREAMLIT ---

# Inicializar el estado de la sesión
inicializar_estado()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image(st.session_state.empresa_logo, use_column_width=True)
    st.header("Cargar Presupuesto")
    archivo_cargado = st.file_uploader("Sube un archivo .json para editar", type="json")
    if archivo_cargado:
        cargar_datos_desde_json(archivo_cargado)
        # Limpiar el uploader después de cargar
        st.rerun()

    st.header("Ayuda")
    st.info(
        "Esta aplicación te permite crear, editar y descargar presupuestos profesionales en formato PDF y JSON. "
        "Rellena el formulario y haz clic en 'GENERAR PRESUPUESTO'."
    )

# --- TÍTULO PRINCIPAL ---
st.title("📄 Generador de Presupuestos Profesional")

# --- FORMULARIO PRINCIPAL ---
# Usamos st.form para agrupar todos los widgets y enviar los datos de una sola vez.
with st.form(key="presupuesto_form"):
    
    # --- Datos de la Empresa y Cliente en columnas ---
    col_empresa, col_cliente = st.columns(2)
    with col_empresa:
        st.subheader("Datos de tu Empresa")
        st.text_input("Nombre", key="empresa_nombre")
        st.text_input("NIF/CIF", key="empresa_nif")
        st.text_area("Dirección", key="empresa_direccion", height=100)
        st.text_input("Teléfono", key="empresa_telefono")
        st.text_input("Email", key="empresa_email")
        st.text_input("Nombre del archivo del Logo", key="empresa_logo", help="Debe estar en la misma carpeta que la app.")
    
    with col_cliente:
        st.subheader("Datos del Cliente")
        st.text_input("Nombre del Cliente", key="cliente_nombre")
        st.text_input("DNI/NIF del Cliente", key="cliente_nif")
        st.text_area("Dirección del Cliente", key="cliente_direccion", height=100)

    st.divider()

    # --- Detalles del Presupuesto ---
    st.subheader("Detalles del Presupuesto")
    col_num, col_fecha = st.columns(2)
    with col_num:
        st.text_input("Número de Presupuesto", key="presupuesto_numero")
    with col_fecha:
        st.text_input("Fecha", key="presupuesto_fecha", help="Formato DD/MM/AAAA")

    st.divider()

    # --- Conceptos (Ítems del Presupuesto) ---
    st.subheader("Conceptos del Presupuesto")
    
    base_imponible = 0.0

    # Cabeceras de la tabla de conceptos
    col_desc, col_cant, col_precio, col_total, col_accion = st.columns([4, 1, 1, 1, 0.5])
    col_desc.write("**Descripción**")
    col_cant.write("**Cantidad**")
    col_precio.write("**Precio (€)**")
    col_total.write("**Total (€)**")

    # Bucle para mostrar y gestionar cada concepto
    for i, item in enumerate(st.session_state.conceptos):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 0.5])
            
            # Usamos una clave única para cada widget dentro del bucle
            key_prefix = f"item_{i}"
            
            st.session_state.conceptos[i]['descripcion'] = col1.text_area("Descripción", value=item['descripcion'], label_visibility="collapsed", key=f"{key_prefix}_desc")
            
            # Validación robusta de campos numéricos
            try:
                cantidad = float(col2.text_input("Cantidad", value=item['cantidad'], label_visibility="collapsed", key=f"{key_prefix}_cant"))
            except (ValueError, TypeError):
                cantidad = 0.0
            st.session_state.conceptos[i]['cantidad'] = cantidad

            try:
                precio = float(col3.text_input("Precio", value=item['precio'], label_visibility="collapsed", key=f"{key_prefix}_precio"))
            except (ValueError, TypeError):
                precio = 0.0
            st.session_state.conceptos[i]['precio'] = precio

            total_item = cantidad * precio
            col4.text(f"{total_item:.2f} €")
            base_imponible += total_item
            
            # Botón para eliminar el concepto
            if col5.button("❌", key=f"{key_prefix}_del", help="Eliminar este concepto"):
                st.session_state.conceptos.pop(i)
                st.rerun() # Forzar el refresco de la UI

    # Botón para añadir un nuevo concepto
    if st.button("➕ Añadir Concepto"):
        st.session_state.conceptos.append({'descripcion': '', 'cantidad': 1.0, 'precio': 0.0})
        st.rerun() # Forzar el refresco

    st.divider()

    # --- Opciones y Resumen ---
    col_opts, col_resumen = st.columns([1, 1])

    with col_opts:
        st.subheader("Opciones y Notas")
        st.checkbox("Calcular IVA (21%)", key="aplicar_iva")
        st.text_area("Notas y Condiciones", key="notas", height=150)

    # Cálculos finales
    iva = base_imponible * 0.21 if st.session_state.aplicar_iva else 0.0
    total_final = base_imponible + iva

    with col_resumen:
        st.subheader("Resumen de Totales")
        st.metric(label="Base Imponible", value=f"{base_imponible:.2f} €")
        st.metric(label="IVA (21%)", value=f"{iva:.2f} €")
        st.metric(label="**TOTAL**", value=f"**{total_final:.2f} €**")

    st.divider()

    # --- BOTÓN DE ENVÍO DEL FORMULARIO ---
    submitted = st.form_submit_button("🚀 GENERAR PRESUPUESTO", type="primary", use_container_width=True)


# --- LÓGICA DE GENERACIÓN (se ejecuta fuera y después del formulario) ---
if submitted:
    with st.spinner('Generando documentos, por favor espera...'):
        try:
            # Recopilar todos los datos del st.session_state en un único diccionario
            datos_presupuesto = {
                "empresa": {
                    "nombre": st.session_state.empresa_nombre,
                    "nif": st.session_state.empresa_nif,
                    "direccion": st.session_state.empresa_direccion,
                    "telefono": st.session_state.empresa_telefono,
                    "email": st.session_state.empresa_email,
                    "logo_path": st.session_state.empresa_logo,
                },
                "cliente": {
                    "nombre": st.session_state.cliente_nombre,
                    "nif": st.session_state.cliente_nif,
                    "direccion": st.session_state.cliente_direccion,
                },
                "detalles": {
                    "numero": st.session_state.presupuesto_numero,
                    "fecha": st.session_state.presupuesto_fecha,
                },
                "conceptos": [
                    {**item, 'total': item['cantidad'] * item['precio']}
                    for item in st.session_state.conceptos
                ],
                "resumen": {
                    "base_imponible": base_imponible,
                    "iva": iva,
                    "total": total_final
                },
                "opciones": {
                    "aplicar_iva": st.session_state.aplicar_iva,
                    "notas": st.session_state.notas
                }
            }

            # 1. Generar el PDF en memoria
            pdf_bytes = crear_pdf_presupuesto(datos_presupuesto)
            st.session_state.pdf_generado = pdf_bytes

            # 2. Generar el JSON en memoria
            json_string = json.dumps(datos_presupuesto, indent=4, ensure_ascii=False)
            st.session_state.json_generado = json_string

            # 3. Preparar nombres de archivo limpios
            cliente_limpio = limpiar_nombre_archivo(st.session_state.cliente_nombre)
            numero_limpio = limpiar_nombre_archivo(st.session_state.presupuesto_numero)
            st.session_state.nombres_archivos = {
                'pdf': f"Presupuesto_{numero_limpio}_{cliente_limpio}.pdf",
                'json': f"Plantilla_Presupuesto_{numero_limpio}.json"
            }
            
            st.success("✅ ¡Documentos generados con éxito!")

        except Exception as e:
            st.error("❌ Ocurrió un error al generar los documentos.")
            st.exception(e) # Muestra los detalles del error para depuración
            # Limpiar el estado para evitar botones de descarga rotos
            st.session_state.pdf_generado = None
            st.session_state.json_generado = None

# --- MOSTRAR BOTONES DE DESCARGA (solo si los archivos se generaron) ---
# Esta sección se encuentra fuera del 'if submitted' para que los botones persistan
# después del rerun que ocurre al hacer clic en ellos.
if st.session_state.get('pdf_generado') and st.session_state.get('json_generado'):
    st.divider()
    st.subheader("Descargar Documentos Generados")
    
    col_pdf, col_json = st.columns(2)
    
    with col_pdf:
        st.download_button(
            label="📥 Descargar PDF",
            data=st.session_state.pdf_generado,
            file_name=st.session_state.nombres_archivos['pdf'],
            mime="application/pdf",
            use_container_width=True
        )
    
    with col_json:
        st.download_button(
            label="📥 Descargar Plantilla JSON",
            data=st.session_state.json_generado,
            file_name=st.session_state.nombres_archivos['json'],
            mime="application/json",
            use_container_width=True
        )

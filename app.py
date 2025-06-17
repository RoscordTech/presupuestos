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
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datos_empresa = {}
        self.datos_cliente = {}
        self.logo_path = ""

    def set_datos(self, datos_empresa, datos_cliente, logo_path):
        self.datos_empresa = datos_empresa
        self.datos_cliente = datos_cliente
        self.logo_path = logo_path

    def header(self):
        try:
            self.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
            self.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)
        except RuntimeError:
            # Este error es improbable en Streamlit Cloud si los archivos están presentes,
            # pero es una buena práctica manejarlo.
            st.error("Error Crítico: Archivos de fuente (DejaVuSansCondensed.ttf) no encontrados.")
            return

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                with Image.open(self.logo_path) as img:
                    img_w, img_h = img.size
                    aspect_ratio = img_h / img_w
                    logo_width = 50
                    logo_height = logo_width * aspect_ratio
                    self.image(self.logo_path, x=(210 - logo_width) / 2, y=10, w=logo_width)
            except Exception:
                pass
        
        self.set_y(40)
        self.set_font('DejaVu', '', 10)
        top_y = self.get_y()
        self.set_xy(10, top_y)
        self.multi_cell(90, 5, 
            f"{self.datos_empresa.get('nombre', '')}\n"
            f"NIF/CIF: {self.datos_empresa.get('nif', '')}\n"
            f"{self.datos_empresa.get('direccion', '')}\n"
            f"Tel: {self.datos_empresa.get('telefono', '')}\n"
            f"Email: {self.datos_empresa.get('email', '')}",
            border=0, align='L'
        )
        self.set_xy(110, top_y)
        self.multi_cell(90, 5, 
            f"CLIENTE:\n"
            f"{self.datos_cliente.get('nombre', '')}\n"
            f"DNI/NIF: {self.datos_cliente.get('nif', '')}\n"
            f"{self.datos_cliente.get('direccion', '')}",
            border=0, align='L'
        )
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        # <<-- CORRECCIÓN AQUÍ (AttributeError) -->>
        # Se comprueba 'dejavu' (en minúsculas) en el diccionario self.fonts
        if 'dejavu' in self.fonts:
            self.set_font('DejaVu', '', 8)
            self.cell(0, 10, 'Gracias por su confianza.', 0, 0, 'C')

# --- FUNCIONES AUXILIARES ---
def inicializar_estado():
    if 'conceptos' not in st.session_state:
        st.session_state.conceptos = [{'descripcion': '', 'cantidad': 1.0, 'precio': 0.0}]
    
    if 'empresa_nombre' not in st.session_state: st.session_state.empresa_nombre = ""
    if 'empresa_nif' not in st.session_state: st.session_state.empresa_nif = ""
    if 'empresa_direccion' not in st.session_state: st.session_state.empresa_direccion = ""
    if 'empresa_telefono' not in st.session_state: st.session_state.empresa_telefono = ""
    if 'empresa_email' not in st.session_state: st.session_state.empresa_email = ""
    if 'empresa_logo' not in st.session_state: st.session_state.empresa_logo = "logo.png"

    if 'cliente_nombre' not in st.session_state: st.session_state.cliente_nombre = ""
    if 'cliente_nif' not in st.session_state: st.session_state.cliente_nif = ""
    if 'cliente_direccion' not in st.session_state: st.session_state.cliente_direccion = ""

    if 'presupuesto_numero' not in st.session_state: st.session_state.presupuesto_numero = ""
    if 'presupuesto_fecha' not in st.session_state: st.session_state.presupuesto_fecha = datetime.now().strftime("%d/%m/%Y")
    
    if 'aplicar_iva' not in st.session_state: st.session_state.aplicar_iva = True
    if 'notas' not in st.session_state: st.session_state.notas = "Validez del presupuesto: 30 días.\nForma de pago: 50% a la aceptación, 50% a la entrega."

    if 'pdf_generado' not in st.session_state: st.session_state.pdf_generado = None
    if 'json_generado' not in st.session_state: st.session_state.json_generado = None
    if 'nombres_archivos' not in st.session_state: st.session_state.nombres_archivos = {}

def limpiar_nombre_archivo(nombre):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', str(nombre))

def cargar_datos_desde_json(archivo_cargado):
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
    pdf = PDF()
    pdf.set_datos(
        datos_presupuesto['empresa'], 
        datos_presupuesto['cliente'], 
        datos_presupuesto['empresa']['logo_path']
    )
    pdf.add_page()
    
    pdf.set_font('DejaVu', 'B', 14)
    pdf.cell(0, 10, 'PRESUPUESTO', 0, 1, 'R')
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 5, f"Nº Presupuesto: {datos_presupuesto['detalles']['numero']}", 0, 1, 'R')
    pdf.cell(0, 5, f"Fecha: {datos_presupuesto['detalles']['fecha']}", 0, 1, 'R')
    pdf.ln(10)

    pdf.set_font('DejaVu', 'B', 10)
    pdf.set_fill_color(220, 220, 220)
    
    col_widths = {'desc': 110, 'cant': 20, 'precio': 30, 'total': 30}
    pdf.cell(col_widths['desc'], 8, 'Descripción', 1, 0, 'C', fill=True)
    pdf.cell(col_widths['cant'], 8, 'Cantidad', 1, 0, 'C', fill=True)
    pdf.cell(col_widths['precio'], 8, 'P. Unitario (€)', 1, 0, 'C', fill=True)
    pdf.cell(col_widths['total'], 8, 'Total (€)', 1, 1, 'C', fill=True)
    
    pdf.set_font('DejaVu', '', 10)
    fill = False
    
    for item in datos_presupuesto['conceptos']:
        pdf.set_fill_color(245, 245, 245)
        x_pos = pdf.get_x()
        y_pos = pdf.get_y()
        pdf.multi_cell(col_widths['desc'], 8, str(item['descripcion']), border='LR', align='L', fill=fill)
        y_after_multicell = pdf.get_y()
        cell_height = max(8, y_after_multicell - y_pos) # Asegurar altura mínima
        pdf.set_xy(x_pos + col_widths['desc'], y_pos)
        pdf.cell(col_widths['cant'], cell_height, str(item['cantidad']), 1, 0, 'C', fill=fill)
        pdf.cell(col_widths['precio'], cell_height, f"{item['precio']:.2f}", 1, 0, 'R', fill=fill)
        pdf.cell(col_widths['total'], cell_height, f"{item['total']:.2f}", 1, 1, 'R', fill=fill)
        fill = not fill

    pdf.cell(sum(col_widths.values()), 0, '', 'T', 1)
    pdf.ln(5)
    
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(130, 8, 'Base Imponible:', 0, 0, 'R')
    pdf.cell(60, 8, f"{datos_presupuesto['resumen']['base_imponible']:.2f} €", 0, 1, 'R')
    
    if datos_presupuesto['opciones']['aplicar_iva']:
        pdf.cell(130, 8, 'IVA (21%):', 0, 0, 'R')
        pdf.cell(60, 8, f"{datos_presupuesto['resumen']['iva']:.2f} €", 0, 1, 'R')

    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(130, 8, 'TOTAL:', 0, 0, 'R')
    pdf.cell(60, 8, f"{datos_presupuesto['resumen']['total']:.2f} €", 0, 1, 'R')
    
    if datos_presupuesto['opciones']['notas']:
        pdf.ln(10)
        pdf.set_font('DejaVu', 'B', 10)
        pdf.cell(0, 8, 'Notas y Condiciones:', 0, 1, 'L')
        pdf.set_font('DejaVu', '', 9)
        pdf.multi_cell(0, 5, datos_presupuesto['opciones']['notas'], border=0, align='L')

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ DE USUARIO ---
inicializar_estado()

with st.sidebar:
    if os.path.exists(st.session_state.empresa_logo):
        # <<-- CORRECCIÓN AQUÍ (Advertencia de Deprecación) -->>
        st.image(st.session_state.empresa_logo, use_container_width=True)
    
    st.header("Cargar Presupuesto")
    archivo_cargado = st.file_uploader("Sube un archivo .json para editar", type="json")
    if archivo_cargado:
        cargar_datos_desde_json(archivo_cargado)
        st.rerun()

    st.header("Ayuda")
    st.info("Esta aplicación te permite crear, editar y descargar presupuestos profesionales en formato PDF y JSON.")

st.title("📄 Generador de Presupuestos Profesional")

st.subheader("Conceptos del Presupuesto")
base_imponible = 0.0

col_desc, col_cant, col_precio, col_total, col_accion = st.columns([4, 1, 1, 1, 0.5])
col_desc.write("**Descripción**")
col_cant.write("**Cantidad**")
col_precio.write("**Precio (€)**")
col_total.write("**Total (€)**")

for i, item in enumerate(st.session_state.conceptos):
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 0.5])
        
        key_prefix = f"item_{i}"
        st.session_state.conceptos[i]['descripcion'] = col1.text_area("Descripción", value=item['descripcion'], label_visibility="collapsed", key=f"{key_prefix}_desc")
        
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
        
        if col5.button("❌", key=f"{key_prefix}_del", help="Eliminar este concepto"):
            st.session_state.conceptos.pop(i)
            st.rerun()

if st.button("➕ Añadir Concepto"):
    st.session_state.conceptos.append({'descripcion': '', 'cantidad': 1.0, 'precio': 0.0})
    st.rerun()

st.divider()

st.subheader("Resumen de Totales")
iva_check = st.checkbox("Calcular IVA (21%)", key="aplicar_iva")
iva = base_imponible * 0.21 if iva_check else 0.0
total_final = base_imponible + iva

col_base, col_iva, col_total = st.columns(3)
col_base.metric(label="Base Imponible", value=f"{base_imponible:.2f} €")
col_iva.metric(label="IVA (21%)", value=f"{iva:.2f} €")
col_total.metric(label="**TOTAL**", value=f"**{total_final:.2f} €**")

st.divider()

with st.form(key="presupuesto_form"):
    st.subheader("Datos para el Presupuesto")
    col_empresa, col_cliente = st.columns(2)
    with col_empresa:
        st.markdown("##### Datos de tu Empresa")
        st.text_input("Nombre", key="empresa_nombre")
        st.text_input("NIF/CIF", key="empresa_nif")
        st.text_area("Dirección", key="empresa_direccion", height=100)
        st.text_input("Teléfono", key="empresa_telefono")
        st.text_input("Email", key="empresa_email")
        st.text_input("Nombre del archivo del Logo", key="empresa_logo", help="Debe estar en la misma carpeta que la app.")
    
    with col_cliente:
        st.markdown("##### Datos del Cliente")
        st.text_input("Nombre del Cliente", key="cliente_nombre")
        st.text_input("DNI/NIF del Cliente", key="cliente_nif")
        st.text_area("Dirección del Cliente", key="cliente_direccion", height=100)

    st.markdown("##### Detalles y Notas")
    col_num, col_fecha = st.columns(2)
    with col_num:
        st.text_input("Número de Presupuesto", key="presupuesto_numero")
    with col_fecha:
        st.text_input("Fecha", key="presupuesto_fecha", help="Formato DD/MM/AAAA")
    
    st.text_area("Notas y Condiciones", key="notas", height=150)

    submitted = st.form_submit_button("🚀 GENERAR PRESUPUESTO", type="primary", use_container_width=True)

# --- LÓGICA DE GENERACIÓN ---
if submitted:
    with st.spinner('Generando documentos...'):
        try:
            datos_presupuesto = {
                "empresa": {
                    "nombre": st.session_state.empresa_nombre, "nif": st.session_state.empresa_nif,
                    "direccion": st.session_state.empresa_direccion, "telefono": st.session_state.empresa_telefono,
                    "email": st.session_state.empresa_email, "logo_path": st.session_state.empresa_logo,
                },
                "cliente": {
                    "nombre": st.session_state.cliente_nombre, "nif": st.session_state.cliente_nif,
                    "direccion": st.session_state.cliente_direccion,
                },
                "detalles": {
                    "numero": st.session_state.presupuesto_numero, "fecha": st.session_state.presupuesto_fecha,
                },
                "conceptos": [
                    {**item, 'total': item['cantidad'] * item['precio']} for item in st.session_state.conceptos
                ],
                "resumen": {"base_imponible": base_imponible, "iva": iva, "total": total_final},
                "opciones": {"aplicar_iva": st.session_state.aplicar_iva, "notas": st.session_state.notas}
            }

            pdf_bytes = crear_pdf_presupuesto(datos_presupuesto)
            st.session_state.pdf_generado = pdf_bytes

            json_string = json.dumps(datos_presupuesto, indent=4, ensure_ascii=False)
            st.session_state.json_generado = json_string

            cliente_limpio = limpiar_nombre_archivo(st.session_state.cliente_nombre)
            numero_limpio = limpiar_nombre_archivo(st.session_state.presupuesto_numero)
            st.session_state.nombres_archivos = {
                'pdf': f"Presupuesto_{numero_limpio}_{cliente_limpio}.pdf",
                'json': f"Plantilla_Presupuesto_{numero_limpio}.json"
            }
            
            st.success("✅ ¡Documentos generados con éxito!")

        except Exception as e:
            st.error("❌ Ocurrió un error al generar los documentos.")
            st.exception(e)
            st.session_state.pdf_generado = None
            st.session_state.json_generado = None

# --- BOTONES DE DESCARGA ---
if st.session_state.get('pdf_generado') and st.session_state.get('json_generado'):
    st.divider()
    st.subheader("Descargar Documentos Generados")
    col_pdf, col_json = st.columns(2)
    with col_pdf:
        st.download_button(label="📥 Descargar PDF", data=st.session_state.pdf_generado,
                           file_name=st.session_state.nombres_archivos['pdf'], mime="application/pdf", use_container_width=True)
    with col_json:
        st.download_button(label="📥 Descargar Plantilla JSON", data=st.session_state.json_generado,
                           file_name=st.session_state.nombres_archivos['json'], mime="application/json", use_container_width=True)

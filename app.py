import streamlit as st # La librería principal para crear aplicaciones web interactivas
import os # Para trabajar con rutas de archivos del sistema operativo
import json # Para manejar datos en formato JSON
from datetime import datetime # Para obtener la fecha actual
from fpdf import FPDF # <-- Nueva librería para generar PDFs

# --- Función para inicializar el estado de la sesión de Streamlit ---
def initialize_session_state():
    if 'empresa' not in st.session_state:
        st.session_state.empresa = {
            "nombre": "SERVICIO TECNICO ERB",
            "nif": "60379728J",
            "direccion": "CL RAMBLA BRASIL, 7 D EN 4\n08028 – BARCELONA",
            "telefono": "",
            "email": "",
            "logo_file": "logo.png" # <--- ¡IMPORTANTE! Asegúrate que este sea el nombre EXACTO de tu archivo de logo (ej. logo.jpg)
        }
    if 'cliente' not in st.session_state:
        st.session_state.cliente = {
            "nombre": "",
            "dni": "",
            "direccion": ""
        }
    if 'detalles' not in st.session_state:
        st.session_state.detalles = {
            "numero": "",
            "fecha": datetime.now().strftime("%d/%m/%Y")
        }
    if 'conceptos' not in st.session_state:
        st.session_state.conceptos = [{"descripcion": "", "cantidad": "", "precio": ""}]
    if 'notas' not in st.session_state:
        st.session_state.notas = ""
    if 'aplicar_iva' not in st.session_state:
        st.session_state.aplicar_iva = True

# --- Función para generar el PDF con fpdf2 ---
# Ahora dibujamos directamente en el PDF en lugar de usar HTML.
def generate_pdf_bytes(data):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=10)

        # Configuración de márgenes y posiciones (ajusta si es necesario)
        margin = 20
        col1_x = margin
        col2_x = 100 # Columna para datos del cliente
        current_y = 20

        # --- Logo ---
        logo_path = os.path.join(os.path.dirname(__file__), data["empresa"]["logo_file"])
        if os.path.exists(logo_path):
            try:
                # fpdf2 puede usar PNG, JPG, etc. directamente si Pillow está instalado.
                # Ajusta las coordenadas y el tamaño del logo según necesites
                pdf.image(logo_path, x=(pdf.w - 30) / 2, y=current_y, w=30)
                current_y += 35 # Espacio después del logo
            except Exception as e:
                st.warning(f"No se pudo incrustar el logo. Error: {e}")
                current_y += 10 # Dejar un pequeño espacio
        else:
            st.warning(f"Archivo de logo no encontrado: {logo_path}")
            current_y += 10 # Dejar un pequeño espacio

        # --- Datos de la Empresa ---
        pdf.set_font("helvetica", "B", 12)
        pdf.set_xy(col1_x, current_y)
        pdf.multi_cell(0, 5, data["empresa"]["nombre"])
        pdf.set_font("helvetica", "", 10)
        current_y = pdf.get_y()
        pdf.set_xy(col1_x, current_y)
        pdf.multi_cell(0, 5, data["empresa"]["direccion"])
        pdf.set_xy(col1_x, pdf.get_y())
        pdf.cell(0, 5, f"NIF: {data['empresa']['nif']}")
        pdf.set_xy(col1_x, pdf.get_y() + 5)
        pdf.cell(0, 5, f"Teléfono: {data['empresa']['telefono']}")
        pdf.set_xy(col1_x, pdf.get_y() + 5)
        pdf.cell(0, 5, f"Email: {data['empresa']['email']}")

        # --- Datos del Cliente ---
        client_y = current_y
        pdf.set_font("helvetica", "B", 12)
        pdf.set_xy(col2_x, client_y)
        pdf.cell(0, 5, "DATOS DEL CLIENTE")
        client_y += 7
        pdf.set_font("helvetica", "", 10)
        pdf.set_xy(col2_x, client_y)
        pdf.cell(0, 5, f"Nombre: {data['cliente']['nombre']}")
        client_y += 5
        pdf.set_xy(col2_x, client_y)
        pdf.multi_cell(0, 5, f"Dirección: {data['cliente']['direccion']}")
        pdf.set_xy(col2_x, pdf.get_y())
        pdf.cell(0, 5, f"DNI: {data['cliente']['dni']}")
        
        current_y = max(pdf.get_y(), client_y + 20) + 10 # Asegura suficiente espacio


        # --- Detalles del Presupuesto (Número y Fecha) ---
        pdf.set_font("helvetica", "B", 16)
        pdf.set_xy(col2_x + 30, current_y)
        pdf.cell(0, 10, "PRESUPUESTO")
        pdf.set_font("helvetica", "", 10)
        pdf.set_xy(col2_x + 30, current_y + 10)
        pdf.cell(0, 10, f"Nº Presupuesto: {data['detalles']['numero']}")
        pdf.set_xy(col2_x + 30, current_y + 15)
        pdf.cell(0, 10, f"Fecha: {data['detalles']['fecha']}")
        current_y += 30

        pdf.ln(10) # Salto de línea

        # --- Tabla de Conceptos ---
        table_headers = ["Descripción", "Cantidad", "P. Unitario (€)", "Total (€)"]
        col_widths = [80, 25, 30, 30] # Ancho de las columnas

        # Dibujar encabezados de la tabla
        pdf.set_fill_color(224, 224, 224) # Color de fondo gris
        pdf.set_font("helvetica", "B", 10)
        x_pos = margin
        for i, header in enumerate(table_headers):
            pdf.set_xy(x_pos, current_y + 10)
            pdf.cell(col_widths[i], 10, header, 1, 0, 'C', True) # 1 para borde, 0 para no salto de línea, C para centrado, True para fondo
            x_pos += col_widths[i]
        pdf.ln(10) # Salto de línea después de los encabezados
        current_y = pdf.get_y()

        # Dibujar filas de conceptos
        pdf.set_font("helvetica", "", 10)
        for i, item in enumerate(data["conceptos"]):
            pdf.set_fill_color(255, 255, 255) if i % 2 == 0 else pdf.set_fill_color(245, 245, 245) # Fondo alterno
            x_pos = margin
            
            # Descripción (multilínea si es necesario)
            pdf.set_xy(x_pos, current_y)
            pdf.multi_cell(col_widths[0], 6, str(item["descripcion"]), 1, 'L', True)
            desc_height = pdf.get_y() - current_y # Altura que ocupó la descripción
            
            # Cantidad
            pdf.set_xy(x_pos + col_widths[0], current_y)
            pdf.cell(col_widths[1], desc_height, str(item["cantidad"]), 1, 0, 'C', True)
            
            # Precio Unitario
            pdf.set_xy(x_pos + col_widths[0] + col_widths[1], current_y)
            pdf.cell(col_widths[2], desc_height, f"{item['precio']:.2f}", 1, 0, 'C', True)
            
            # Total por item
            item_total = item["cantidad"] * item["precio"]
            pdf.set_xy(x_pos + col_widths[0] + col_widths[1] + col_widths[2], current_y)
            pdf.cell(col_widths[3], desc_height, f"{item_total:.2f}", 1, 0, 'C', True)
            
            current_y += desc_height # Mover Y para la siguiente fila

        pdf.ln(10) # Salto de línea después de la tabla

        # --- Totales ---
        pdf.set_font("helvetica", "", 10)
        pdf.set_x(col2_x + 30) # Mueve la posición X para alinear los totales a la derecha
        pdf.cell(0, 7, f"Base Imponible: {data['totales']['base_imponible']:.2f} €", 0, 1, 'R')
        pdf.set_x(col2_x + 30)
        pdf.cell(0, 7, f"IVA (21%): {data['totales']['iva']:.2f} €", 0, 1, 'R')
        pdf.set_x(col2_x + 30)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"TOTAL: {data['totales']['total']:.2f} €", 'T', 1, 'R') # 'T' para borde superior

        pdf.ln(10)

        # --- Notas ---
        pdf.set_font("helvetica", "B", 10)
        pdf.set_x(margin)
        pdf.cell(0, 5, "Notas y Condiciones:")
        pdf.ln(7)
        pdf.set_font("helvetica", "", 9)
        pdf.set_x(margin)
        pdf.multi_cell(pdf.w - 2 * margin, 4, data['notas']) # multi_cell para texto largo

        # --- Pie de página ---
        pdf.set_font("helvetica", "I", 8)
        pdf.set_xy(margin, pdf.h - 15) # Posición cerca del final de la página
        pdf.cell(0, 10, "Gracias por su confianza.", 0, 0, 'C')

        # Devolver el PDF como bytes
        return pdf.output(dest='S').encode('latin-1') # 'S' devuelve como cadena, luego codifica a bytes

    except Exception as e:
        st.error(f"Ocurrió un error al generar el PDF: {e}")
        st.exception(e) # Muestra el traceback completo en los logs de Streamlit
        return None

# --- Configuración inicial de la página de Streamlit ---
st.set_page_config(
    page_title="Generador de Presupuestos Profesional",
    page_icon="💸",
    layout="centered"
)

st.title("Generador de Presupuestos Profesional 💸")

initialize_session_state()

# --- Sección de Cargar Plantilla Editable (JSON) en la barra lateral ---
st.sidebar.header("Plantillas Editables (JSON)")

uploaded_file = st.sidebar.file_uploader("Cargar Presupuesto para Editar (.json)", type="json")
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        st.session_state.empresa = data.get("empresa", st.session_state.empresa)
        st.session_state.cliente = data.get("cliente", st.session_state.cliente)
        st.session_state.detalles = data.get("detalles", st.session_state.detalles)
        st.session_state.conceptos = data.get("conceptos", [{"descripcion": "", "cantidad": "", "precio": ""}])
        st.session_state.notas = data.get("notas", "")
        st.session_state.aplicar_iva = data.get("aplicar_iva", True)
        st.sidebar.success("Plantilla cargada con éxito!")
    except Exception as e:
        st.sidebar.error(f"Error al cargar la plantilla: {e}")

# --- Formulario Principal ---

# Sección: Datos de tu Empresa
st.subheader("Datos de tu Empresa") # Cambiado a subheader para un tamaño más pequeño
st.session_state.empresa["nombre"] = st.text_input("Nombre:", value=st.session_state.empresa["nombre"], key="empresa_nombre")
st.session_state.empresa["nif"] = st.text_input("NIF/CIF:", value=st.session_state.empresa["nif"], key="empresa_nif")
st.session_state.empresa["direccion"] = st.text_area("Dirección:", value=st.session_state.empresa["direccion"], key="empresa_direccion")
st.session_state.empresa["telefono"] = st.text_input("Teléfono:", value=st.session_state.empresa["telefono"], key="empresa_telefono")
st.session_state.empresa["email"] = st.text_input("Email:", value=st.session_state.empresa["email"], key="empresa_email")
# El logo_file ahora solo se usa como referencia visual, no para previsualizar aquí.
st.session_state.empresa["logo_file"] = st.text_input("Nombre del archivo del Logo (ej. logo.png):", value=st.session_state.empresa["logo_file"], key="empresa_logo_file")


# Sección: Datos del Cliente
st.subheader("Datos del Cliente")
st.session_state.cliente["nombre"] = st.text_input("Nombre del Cliente:", value=st.session_state.cliente["nombre"], key="cliente_nombre")
st.session_state.cliente["dni"] = st.text_input("DNI/NIF del Cliente:", value=st.session_state.cliente["dni"], key="cliente_dni")
st.session_state.cliente["direccion"] = st.text_area("Dirección del Cliente:", value=st.session_state.cliente["direccion"], key="cliente_direccion")

# Sección: Detalles del Presupuesto
st.subheader("Detalles del Presupuesto")
st.session_state.detalles["numero"] = st.text_input("Número de Presupuesto:", value=st.session_state.detalles["numero"], key="presupuesto_numero")
st.session_state.detalles["fecha"] = st.text_input("Fecha (DD/MM/AAAA):", value=st.session_state.detalles["fecha"], key="presupuesto_fecha")

# Sección: Conceptos
st.subheader("Conceptos")
col1, col2, col3, col4 = st.columns([0.6, 0.15, 0.15, 0.1])
with col1: st.write("**Descripción**")
with col2: st.write("**Cant.**")
with col3: st.write("**Precio (€)**")
with col4: st.write("") # Columna para el botón de borrar

# Para cada concepto en la lista, creamos una fila de campos
new_conceptos = []
# Mantener un registro de los índices borrados
deleted_indices = set() 

for i, concepto in enumerate(st.session_state.conceptos):
    # Solo mostrar si no fue marcado para borrarse en la ejecución actual
    if i not in deleted_indices:
        cols = st.columns([0.6, 0.15, 0.15, 0.1])
        with cols[0]:
            desc = st.text_input(f"Descripción_{i}", value=concepto["descripcion"], label_visibility="collapsed", key=f"desc_{i}")
        with cols[1]:
            cant_str = st.text_input(f"Cantidad_{i}", value=str(concepto["cantidad"]), label_visibility="collapsed", key=f"cant_{i}")
            cant = float(cant_str) if cant_str.replace('.', '', 1).isdigit() else 0.0
        with cols[2]:
            precio_str = st.text_input(f"Precio_{i}", value=str(concepto["precio"]), label_visibility="collapsed", key=f"precio_{i}")
            precio = float(precio_str) if precio_str.replace('.', '', 1).isdigit() else 0.0
        with cols[3]:
            # El botón de borrar. st.button devuelve True si fue clickeado en esta ejecución
            if st.button("X", key=f"delete_btn_{i}"):
                deleted_indices.add(i) # Marcar para eliminación

        # Agregamos a la lista temporal si no está marcado para eliminación
        new_conceptos.append({"descripcion": desc, "cantidad": cant, "precio": precio})

# Reconstruir la lista de conceptos después de procesar todas las filas
st.session_state.conceptos = [c for i, c in enumerate(new_conceptos) if i not in deleted_indices]

# Si se marcó algún elemento para borrar, forzar un rerun para que la UI se actualice
if deleted_indices:
    st.experimental_rerun()


if st.button("Añadir Concepto"):
    st.session_state.conceptos.append({"descripcion": "", "cantidad": "", "precio": ""})
    st.experimental_rerun() # Fuerza una nueva ejecución para actualizar la UI

# Sección: Opciones y Finalización
st.subheader("Opciones y Finalización")
st.session_state.aplicar_iva = st.checkbox("Calcular IVA (21%)", value=st.session_state.aplicar_iva)
st.session_state.notas = st.text_area("Notas y Condiciones:", value=st.session_state.notas)

# --- Calcular Totales y Mostrar ---
subtotal = sum(c["cantidad"] * c["precio"] for c in st.session_state.conceptos if isinstance(c["cantidad"], (int, float)) and isinstance(c["precio"], (int, float)))
iva = subtotal * 0.21 if st.session_state.aplicar_iva else 0
total = subtotal + iva

st.markdown("---") # Una línea divisoria para separar
st.subheader("Resumen de Totales:")
st.write(f"**Base Imponible:** {subtotal:.2f} €")
st.write(f"**IVA (21%):** {iva:.2f} €")
st.write(f"**TOTAL:** {total:.2f} €")
st.markdown("---")

# --- Botón de Generar PDF y JSON ---
if st.button("GENERAR PRESUPUESTO"):
    # Recolectar todos los datos para el PDF y JSON
    budget_data = {
        "empresa": st.session_state.empresa,
        "cliente": st.session_state.cliente,
        "detalles": st.session_state.detalles,
        "conceptos": st.session_state.conceptos,
        "notas": st.session_state.notas,
        "aplicar_iva": st.session_state.aplicar_iva,
        "totales": {"base_imponible": subtotal, "iva": iva, "total": total}
    }

    # Generar PDF
    pdf_output = generate_pdf_bytes(budget_data)
    if pdf_output:
        numero_limpio = "".join(c for c in budget_data["detalles"]["numero"] if c.isalnum() or c in ('-', '_')).rstrip()
        cliente_limpio = "".join(c for c in budget_data["cliente"]["nombre"] if c.isalnum() or c in ('-', '_')).rstrip()
        filename_base = f"Presupuesto_{numero_limpio}_{cliente_limpio}"

        st.download_button(
            label="Descargar PDF",
            data=pdf_output,
            file_name=f"{filename_base}.pdf",
            mime="application/pdf",
            key="download_pdf_button"
        )
        st.success("PDF generado. Haz clic en el botón 'Descargar PDF' de arriba.")
    else:
        st.error("No se pudo generar el PDF. Revisa los mensajes de error.")


    # Generar JSON editable
    json_output = json.dumps(budget_data, ensure_ascii=False, indent=4).encode('utf-8')
    st.download_button(
        label="Descargar Plantilla JSON",
        data=json_output,
        file_name=f"Plantilla_{filename_base}.json",
        mime="application/json",
        key="download_json_button"
    )

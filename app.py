import streamlit as st  # Librería para crear apps
import os  # Para rutas de archivos
import json  # Para leer y escribir JSON
from datetime import datetime  # Para fechas
from fpdf import FPDF  # Generador de PDF
from io import BytesIO  # Buffer de bytes

# --- Inicializar estado de sesión ---
def initialize_session_state():
    if 'empresa' not in st.session_state:
        st.session_state.empresa = {
            "nombre": "SERVICIO TECNICO ERB",
            "nif": "60379728J",
            "direccion": "CL RAMBLA BRASIL, 7 D EN 4\n08028 - BARCELONA",
            "telefono": "",
            "email": "",
            "logo_file": "logo.png"
        }
    if 'cliente' not in st.session_state:
        st.session_state.cliente = {"nombre": "", "dni": "", "direccion": ""}
    if 'detalles' not in st.session_state:
        st.session_state.detalles = {"numero": "", "fecha": datetime.now().strftime("%d/%m/%Y")}
    if 'conceptos' not in st.session_state:
        st.session_state.conceptos = [{"descripcion": "", "cantidad": "", "precio": ""}]
    if 'notas' not in st.session_state:
        st.session_state.notas = ""
    if 'aplicar_iva' not in st.session_state:
        st.session_state.aplicar_iva = True

initialize_session_state()

# --- FPDF + BytesIO ---
def generate_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()

    font_name = "DejaVuSans"
    pdf.add_font(font_name, "", "DejaVuSansCondensed.ttf", uni=True)
    pdf.add_font(font_name, "B", "DejaVuSansCondensed-Bold.ttf", uni=True)
    pdf.set_font(font_name, size=10)

    margin = 20
    col1_x = margin
    col2_x = 100
    current_y = 20

    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), data["empresa"]["logo_file"])
    if os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=(pdf.w - 30) / 2, y=current_y, w=30)
            current_y += 35
        except:
            current_y += 10
    else:
        current_y += 10

    # Datos empresa
    pdf.set_xy(col1_x, current_y)
    pdf.set_font(font_name, "B", 12)
    pdf.multi_cell(0, 5, data["empresa"]["nombre"])
    pdf.set_font(font_name, "", 10)
    pdf.set_xy(col1_x, pdf.get_y())
    pdf.multi_cell(0, 5, data["empresa"]["direccion"])
    pdf.cell(0, 5, f"NIF: {data['empresa']['nif']}", ln=1)
    pdf.cell(0, 5, f"Teléfono: {data['empresa']['telefono']}", ln=1)
    pdf.cell(0, 5, f"Email: {data['empresa']['email']}", ln=1)

    # Datos cliente
    client_y = current_y
    pdf.set_font(font_name, "B", 12)
    pdf.set_xy(col2_x, client_y)
    pdf.cell(0, 5, "DATOS DEL CLIENTE", ln=1)
    pdf.set_font(font_name, "", 10)
    pdf.cell(0, 5, f"Nombre: {data['cliente']['nombre']}", ln=1)
    pdf.multi_cell(0, 5, f"Dirección: {data['cliente']['direccion']}")
    pdf.cell(0, 5, f"DNI: {data['cliente']['dni']}", ln=1)

    current_y = pdf.get_y() + 10

    # Encabezado presupuesto
    pdf.set_font(font_name, "B", 16)
    pdf.set_xy(col2_x + 30, current_y)
    pdf.cell(0, 10, "PRESUPUESTO")
    pdf.set_font(font_name, "", 10)
    pdf.set_xy(col2_x + 30, current_y + 10)
    pdf.cell(0, 10, f"Nº: {data['detalles']['numero']}", ln=1)
    pdf.cell(0, 10, f"Fecha: {data['detalles']['fecha']}", ln=1)
    current_y = pdf.get_y() + 10

    # Tabla conceptos
    headers = ["Descripción", "Cant.", "Precio (€)", "Total (€)"]
    widths = [80, 25, 30, 30]
    pdf.set_fill_color(224, 224, 224)
    pdf.set_font(font_name, "B", 10)

    for i, h in enumerate(headers):
        pdf.cell(widths[i], 10, h, 1, 0, "C", True)
    pdf.ln()

    pdf.set_font(font_name, "", 10)
    fill = False
    for item in data["conceptos"]:
        pdf.set_fill_color(245, 245, 245 if fill else 255)
        pdf.cell(widths[0], 6, item["descripcion"], 1, 0, "L", fill)
        pdf.cell(widths[1], 6, str(item["cantidad"]), 1, 0, "C", fill)
        pdf.cell(widths[2], 6, f"{item['precio']:.2f}", 1, 0, "C", fill)
        total = item["cantidad"] * item["precio"]
        pdf.cell(widths[3], 6, f"{total:.2f}", 1, 0, "C", fill)
        pdf.ln()
        fill = not fill

    # Totales
    pdf.ln(5)
    pdf.cell(0, 5, f"Base Imponible: {data['totales']['base_imponible']:.2f} €", align="R", ln=1)
    pdf.cell(0, 5, f"IVA (21%): {data['totales']['iva']:.2f} €", align="R", ln=1)
    pdf.set_font(font_name, "B", 12)
    pdf.cell(0, 10, f"TOTAL: {data['totales']['total']:.2f} €", align="R", ln=1)

    pdf.ln(5)
    pdf.set_font(font_name, "B", 10)
    pdf.cell(0, 5, "Notas y condiciones:")
    pdf.ln(4)
    pdf.set_font(font_name, "", 9)
    pdf.multi_cell(0, 4, data["notas"])

    pdf.set_xy(margin, pdf.h - 15)
    pdf.set_font(font_name, "", 8)
    pdf.cell(0, 10, "Gracias por su confianza.", align="C")

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- UI Streamlit ---
st.set_page_config(page_title="Generador de Presupuestos", layout="centered")
st.title("Generador de Presupuestos Profesional 💸")

# Carga JSON
uploaded = st.sidebar.file_uploader("Cargar plantilla JSON", type="json")
if uploaded:
    try:
        data = json.load(uploaded)
        for key in ("empresa", "cliente", "detalles", "conceptos", "notas", "aplicar_iva"):
            if key in data:
                st.session_state[key] = data[key]
        st.sidebar.success("Plantilla cargada")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Formulario
with st.form("form"):
    st.subheader("Datos de la Empresa")
    for fld in ("nombre", "nif", "direccion", "telefono", "email", "logo_file"):
        st.session_state.empresa[fld] = st.text_input(fld.capitalize(), st.session_state.empresa[fld])

    st.subheader("Datos del Cliente")
    for fld in ("nombre", "dni", "direccion"):
        st.session_state.cliente[fld] = st.text_input(f"C. {fld}", st.session_state.cliente[fld])

    st.subheader("Detalles")
    for fld in ("numero", "fecha"):
        st.session_state.detalles[fld] = st.text_input(fld.capitalize(), st.session_state.detalles[fld])

    st.subheader("Conceptos")
    idxs = list(range(len(st.session_state.conceptos)))
    borrar = []
    for i in idxs:
        c = st.session_state.conceptos[i]
        cols = st.columns([6, 1, 1, 0.5])
        c["descripcion"] = cols[0].text_input("Desc", c["descripcion"], key=f"desc_{i}")
        c["cantidad"] = float(cols[1].text_input("Cant", str(c["cantidad"]), key=f"cant_{i}") or 0)
        c["precio"] = float(cols[2].text_input("Precio", str(c["precio"]), key=f"precio_{i}") or 0)
        if cols[3].button("X", key=f"del_{i}"):
            borrar.append(i)
    for i in sorted(borrar, reverse=True):
        st.session_state.conceptos.pop(i)
    if st.form_submit_button("Añadir concepto"):
        st.session_state.conceptos.append({"descripcion": "", "cantidad": 0, "precio": 0})

    # Notas e IVA
    st.session_state.aplicar_iva = st.checkbox("Aplicar IVA 21%", st.session_state.aplicar_iva)
    st.session_state.notas = st.text_area("Notas", st.session_state.notas)

# Totales
subtotal = sum(c["cantidad"] * c["precio"] for c in st.session_state.conceptos)
iva = subtotal * 0.21 if st.session_state.aplicar_iva else 0
total = subtotal + iva

st.subheader("Resumen")
st.write(f"Base imponible: {subtotal:.2f} €")
st.write(f"IVA (21%): {iva:.2f} €")
st.write(f"TOTAL: {total:.2f} €")

# Botón de generar
if st.button("GENERAR PRESUPUESTO"):
    data = {
        "empresa": st.session_state.empresa,
        "cliente": st.session_state.cliente,
        "detalles": st.session_state.detalles,
        "conceptos": st.session_state.conceptos,
        "notas": st.session_state.notas,
        "aplicar_iva": st.session_state.aplicar_iva,
        "totales": {"base_imponible": subtotal, "iva": iva, "total": total}
    }
    pdf_buffer = generate_pdf_bytes(data)
    json_bytes = json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")

    st.success("📄 ¡Listo para descargar!")
    st.download_button("Descargar PDF", pdf_buffer, file_name="presupuesto.pdf", mime="application/pdf")
    st.download_button("Descargar JSON", json_bytes, file_name="plantilla_presupuesto.json", mime="application/json")

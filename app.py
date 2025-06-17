import streamlit as st # La librería principal para crear aplicaciones web interactivas
import os # Para trabajar con rutas de archivos del sistema operativo
import json # Para manejar datos en formato JSON
import base64 # Para codificar/decodificar imágenes en base64 para HTML
from datetime import datetime # Para obtener la fecha actual

from jinja2 import Environment, FileSystemLoader # Jinja2 para cargar y renderizar plantillas HTML
from weasyprint import HTML # WeasyPrint para convertir HTML a PDF

# --- Función para inicializar el estado de la sesión de Streamlit ---
# st.session_state es como un almacenamiento temporal para que los datos
# no se pierdan cada vez que el usuario interactúa con la app.
def initialize_session_state():
    # Si 'empresa' no existe en el estado de la sesión, lo inicializamos con valores por defecto.
    if 'empresa' not in st.session_state:
        st.session_state.empresa = {
            "nombre": "SERVICIO TECNICO ERB",
            "nif": "60379728J",
            "direccion": "CL RAMBLA BRASIL, 7 D EN 4\n08028 – BARCELONA", # \n crea saltos de línea
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
            "fecha": datetime.now().strftime("%d/%m/%Y") # Fecha actual en formato DD/MM/AAAA
        }
    # La lista de conceptos. Empezamos con un concepto vacío.
    if 'conceptos' not in st.session_state:
        st.session_state.conceptos = [{"descripcion": "", "cantidad": "", "precio": ""}]
    if 'notas' not in st.session_state:
        st.session_state.notas = ""
    if 'aplicar_iva' not in st.session_state:
        st.session_state.aplicar_iva = True

# --- Función para generar el PDF ---
# Esta función es similar a la que tenías en tu código Python original,
# pero adaptada para devolver los bytes del PDF en lugar de guardarlo en disco.
def generate_pdf_bytes(data):
    """Genera el PDF como bytes utilizando Jinja2 y WeasyPrint."""
    try:
        # Preparamos los datos que se enviarán a la plantilla HTML
        render_context = {
            'numero': data['detalles']['numero'],
            'fecha': data['detalles']['fecha'],
            'empresa': data['empresa'],
            'cliente': data['cliente'],
            'items': [
                {
                    "descripcion": c["descripcion"],
                    "cantidad": c["cantidad"],
                    "precio_unitario": c["precio"]
                } for c in data["conceptos"] # Iteramos sobre la lista de conceptos
            ],
            'base_imponible': data['totales']['base_imponible'],
            'iva': data['totales']['iva'],
            'total': data['totales']['total'],
            'notas': data['notas']
        }

        # Carga el logo y lo codifica en Base64 para incrustarlo directamente en el HTML del PDF.
        # Esto es importante para que el logo aparezca en el PDF final.
        # os.path.dirname(__file__) obtiene la ruta de la carpeta donde está 'app.py'
        logo_path = os.path.join(os.path.dirname(__file__), data["empresa"]["logo_file"])
        if os.path.exists(logo_path): # Verificamos si el archivo del logo existe
            with open(logo_path, "rb") as image_file: # Abrimos el archivo en modo binario de lectura
                encoded = base64.b64encode(image_file.read()).decode("utf-8") # Codificamos a Base64
                ext = os.path.splitext(logo_path)[1].lower().replace('.', '') # Obtenemos la extensión (png, jpg)
                render_context['logo_path'] = f"data:image/{ext};base64,{encoded}" # Formato para incrustar en HTML
        else:
            render_context['logo_path'] = None # Si no hay logo, la variable es None

        # Configura Jinja2 para buscar la plantilla HTML en la misma carpeta que 'app.py'
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template("plantilla.html") # <--- Tu archivo plantilla.html

        # Renderiza (genera) el HTML final con todos los datos
        html_out = template.render(render_context)

        # Usa WeasyPrint para convertir el HTML renderizado a un PDF en memoria (bytes)
        pdf_bytes = HTML(string=html_out).write_pdf()
        return pdf_bytes # Devuelve los bytes del PDF
    except Exception as e:
        # Si algo falla en la generación del PDF, mostramos un error en la interfaz de Streamlit
        st.error(f"Ocurrió un error al generar el PDF: {e}")
        return None

# --- Configuración inicial de la página de Streamlit ---
# Esto define el título de la pestaña del navegador y el icono
st.set_page_config(
    page_title="Generador de Presupuestos Profesional",
    page_icon="💸", # Puedes usar un emoji como icono
    layout="centered" # El diseño de la página será centrado
)

st.title("Generador de Presupuestos Profesional 💸") # Título principal de la aplicación

initialize_session_state() # Llama a la función para cargar los datos por defecto o del estado de la sesión

# --- Sección de Cargar Plantilla Editable (JSON) en la barra lateral ---
st.sidebar.header("Plantillas Editables (JSON)")

# st.sidebar.file_uploader crea un botón para subir un archivo
uploaded_file = st.sidebar.file_uploader("Cargar Presupuesto para Editar (.json)", type="json")
if uploaded_file is not None: # Si el usuario subió un archivo
    try:
        data = json.load(uploaded_file) # Cargamos el JSON
        # Actualizamos el estado de la sesión con los datos del JSON
        st.session_state.empresa = data.get("empresa", st.session_state.empresa)
        st.session_state.cliente = data.get("cliente", st.session_state.cliente)
        st.session_state.detalles = data.get("detalles", st.session_state.detalles)
        st.session_state.conceptos = data.get("conceptos", [{"descripcion": "", "cantidad": "", "precio": ""}])
        st.session_state.notas = data.get("notas", "")
        st.session_state.aplicar_iva = data.get("aplicar_iva", True)
        st.sidebar.success("Plantilla cargada con éxito!") # Mensaje de éxito
    except Exception as e:
        st.sidebar.error(f"Error al cargar la plantilla: {e}") # Mensaje de error

# --- Formulario Principal de la Interfaz (replicando tu app de escritorio) ---

# Sección: Datos de tu Empresa
st.header("Datos de tu Empresa")
# st.text_input crea un campo de texto. 'value' es el valor inicial. 'key' es para que Streamlit
# identifique el widget y mantenga su estado correctamente.
st.session_state.empresa["nombre"] = st.text_input("Nombre:", value=st.session_state.empresa["nombre"], key="empresa_nombre")
st.session_state.empresa["nif"] = st.text_input("NIF/CIF:", value=st.session_state.empresa["nif"], key="empresa_nif")
st.session_state.empresa["direccion"] = st.text_area("Dirección:", value=st.session_state.empresa["direccion"], key="empresa_direccion")
st.session_state.empresa["telefono"] = st.text_input("Teléfono:", value=st.session_state.empresa["telefono"], key="empresa_telefono")
st.session_state.empresa["email"] = st.text_input("Email:", value=st.session_state.empresa["email"], key="empresa_email")
st.session_state.empresa["logo_file"] = st.text_input("Archivo del Logo (ej. logo.png):", value=st.session_state.empresa["logo_file"], key="empresa_logo_file")

# Sección: Datos del Cliente
st.header("Datos del Cliente")
st.session_state.cliente["nombre"] = st.text_input("Nombre del Cliente:", value=st.session_state.cliente["nombre"], key="cliente_nombre")
st.session_state.cliente["dni"] = st.text_input("DNI/NIF del Cliente:", value=st.session_state.cliente["dni"], key="cliente_dni")
st.session_state.cliente["direccion"] = st.text_area("Dirección del Cliente:", value=st.session_state.cliente["direccion"], key="cliente_direccion")

# Sección: Detalles del Presupuesto
st.header("Detalles del Presupuesto")
st.session_state.detalles["numero"] = st.text_input("Número de Presupuesto:", value=st.session_state.detalles["numero"], key="presupuesto_numero")
st.session_state.detalles["fecha"] = st.text_input("Fecha (DD/MM/AAAA):", value=st.session_state.detalles["fecha"], key="presupuesto_fecha")

# Sección: Conceptos (La tabla dinámica)
st.header("Conceptos")
# Definimos las columnas para los encabezados de la tabla
col1, col2, col3, col4 = st.columns([0.6, 0.15, 0.15, 0.1])
with col1: st.write("**Descripción**")
with col2: st.write("**Cant.**")
with col3: st.write("**Precio (€)**")
with col4: st.write("") # Columna vacía para el botón de borrar

new_conceptos = [] # Lista temporal para guardar los conceptos actualizados
# Iteramos sobre la lista de conceptos actual para mostrar los campos de entrada
for i, concepto in enumerate(st.session_state.conceptos):
    cols = st.columns([0.6, 0.15, 0.15, 0.1]) # Creamos columnas para cada fila
    with cols[0]:
        # text_input con label_visibility="collapsed" oculta la etiqueta para una vista compacta
        desc = st.text_input(f"Descripción_{i}", value=concepto["descripcion"], label_visibility="collapsed", key=f"desc_{i}")
    with cols[1]:
        cant_str = st.text_input(f"Cantidad_{i}", value=str(concepto["cantidad"]), label_visibility="collapsed", key=f"cant_{i}")
        # Intentamos convertir la cantidad a float, si no es un número válido, usamos 0.0
        cant = float(cant_str) if cant_str.replace('.', '', 1).isdigit() else 0.0
    with cols[2]:
        precio_str = st.text_input(f"Precio_{i}", value=str(concepto["precio"]), label_visibility="collapsed", key=f"precio_{i}")
        # Intentamos convertir el precio a float, si no es válido, usamos 0.0
        precio = float(precio_str) if precio_str.replace('.', '', 1).isdigit() else 0.0
    with cols[3]:
        # El botón "X" para borrar la fila. Su acción se manejará después del bucle.
        if st.button("X", key=f"delete_{i}"):
            # Aquí no hacemos nada, solo registramos que el botón fue presionado.
            # La eliminación real ocurre después de este bucle.
            pass

    new_conceptos.append({"descripcion": desc, "cantidad": cant, "precio": precio})

# Lógica para manejar la eliminación de conceptos.
# Es necesario hacerlo fuera del bucle para evitar modificar la lista mientras se itera sobre ella.
deleted_index = -1
for i in range(len(st.session_state.conceptos)):
    if st.session_state.get(f"delete_{i}"): # Verifica si el botón de borrar para este índice fue presionado
        deleted_index = i
        break
if deleted_index != -1:
    del new_conceptos[deleted_index] # Elimina el concepto de la lista temporal
    st.session_state.conceptos = new_conceptos # Actualiza la lista en el estado de la sesión
    st.experimental_rerun() # Fuerza a Streamlit a volver a ejecutar el script para actualizar la UI

st.session_state.conceptos = new_conceptos # Aseguramos que los conceptos actualizados se guarden

# Botón para añadir una nueva fila de concepto
if st.button("Añadir Concepto"):
    st.session_state.conceptos.append({"descripcion": "", "cantidad": "", "precio": ""})
    st.experimental_rerun() # Fuerza una nueva ejecución para añadir la fila a la UI

# Sección: Opciones y Finalización
st.header("Opciones y Finalización")
# st.checkbox crea una casilla de verificación para el IVA
st.session_state.aplicar_iva = st.checkbox("Calcular IVA (21%)", value=st.session_state.aplicar_iva)
# st.text_area crea un campo de texto para múltiples líneas
st.session_state.notas = st.text_area("Notas y Condiciones:", value=st.session_state.notas)

# --- Calcular Totales ---
# Sumamos las cantidades * precios de todos los conceptos válidos
subtotal = sum(c["cantidad"] * c["precio"] for c in st.session_state.conceptos if isinstance(c["cantidad"], (int, float)) and isinstance(c["precio"], (int, float)))
iva = subtotal * 0.21 if st.session_state.aplicar_iva else 0 # Calcula el IVA si la casilla está marcada
total = subtotal + iva # Calcula el total

st.subheader("Resumen de Totales:") # Subtítulo para el resumen
st.write(f"**Base Imponible:** {subtotal:.2f} €") # Muestra la base imponible formateada a 2 decimales
st.write(f"**IVA (21%):** {iva:.2f} €")
st.write(f"**TOTAL:** {total:.2f} €")


# --- Botón de Generar PDF y JSON ---
# Este bloque se ejecuta cuando se presiona el botón "GENERAR PRESUPUESTO EN PDF"
if st.button("GENERAR PRESUPUESTO EN PDF"):
    # Recolectamos todos los datos del formulario en un diccionario
    budget_data = {
        "empresa": st.session_state.empresa,
        "cliente": st.session_state.cliente,
        "detalles": st.session_state.detalles,
        "conceptos": st.session_state.conceptos,
        "notas": st.session_state.notas,
        "aplicar_iva": st.session_state.aplicar_iva,
        "totales": {"base_imponible": subtotal, "iva": iva, "total": total} # Incluimos los totales calculados
    }

    # Intentamos generar el PDF
    pdf_output = generate_pdf_bytes(budget_data)
    if pdf_output: # Si el PDF se generó correctamente (no es None)
        # Limpiamos el nombre del archivo para que sea compatible con sistemas de archivos
        numero_limpio = "".join(c for c in budget_data["detalles"]["numero"] if c.isalnum() or c in ('-', '_')).rstrip()
        cliente_limpio = "".join(c for c in budget_data["cliente"]["nombre"] if c.isalnum() or c in ('-', '_')).rstrip()
        filename_base = f"Presupuesto_{numero_limpio}_{cliente_limpio}"

        # st.download_button crea un botón para descargar el archivo.
        # 'data' son los bytes del PDF, 'file_name' es el nombre que tendrá el archivo al descargarse,
        # 'mime' es el tipo de archivo (PDF).
        st.download_button(
            label="Descargar PDF",
            data=pdf_output,
            file_name=f"{filename_base}.pdf",
            mime="application/pdf",
            key="download_pdf_button" # Una clave única para el botón
        )
        st.success("PDF generado. Haz clic en el botón 'Descargar PDF' de arriba.") # Mensaje de éxito

    # Generamos el JSON editable
    # json.dumps convierte el diccionario a una cadena JSON, ensure_ascii=False para caracteres especiales
    # indent=4 para que sea legible. .encode('utf-8') lo convierte a bytes.
    json_output = json.dumps(budget_data, ensure_ascii=False, indent=4).encode('utf-8')
    st.download_button(
        label="Descargar Plantilla JSON",
        data=json_output,
        file_name=f"Plantilla_{filename_base}.json",
        mime="application/json",
        key="download_json_button"
    )

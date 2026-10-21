import os
import html
from decimal import Decimal, InvalidOperation

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# DERCELL — catálogo de celulares
st.set_page_config(page_title="DERCELL | Catálogo de celulares", page_icon="📱", layout="wide")

WHATSAPP_URL = "https://wa.me/593990359268"

def whatsapp_product_url(phone: dict) -> str:
    product_name = f"{phone.get('brand', '')} {phone.get('model', '')}".strip()
    message = f"Hola, DERCELL. Estoy interesado/a en el {product_name} que aparece en su catálogo. ¿Me pueden dar más información sobre su disponibilidad y precio?"
    return WHATSAPP_URL + "?text=" + __import__("urllib.parse", fromlist=["quote"]).quote(message)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

def setting(name: str, default: str = "") -> str:
    """Read Streamlit secrets first, then environment variables."""
    try:
        value = st.secrets.get(name, None)
        if value is not None:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)

@st.cache_resource
def supabase_client() -> Client:
    url = setting("SUPABASE_URL")
    key = setting("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Falta configurar SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .env o en Secrets."
        )
    return create_client(url, key)

def money(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def safe_text(value) -> str:
    return html.escape(str(value or ""))

def image_urls(phone: dict) -> list[str]:
    photos = phone.get("photos") or []
    if isinstance(photos, str):
        return [photos] if photos else []
    return [p for p in photos if isinstance(p, str) and p.strip()]

def load_phones():
    sb = supabase_client()
    result = sb.table("phones").select("*").order("created_at", desc=True).execute()
    return result.data or []

def upload_photos(files) -> list[str]:
    """Upload image files to the Supabase Storage bucket named phone-photos."""
    sb = supabase_client()
    urls = []
    for file in files or []:
        clean_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in file.name)
        path = f"{__import__('uuid').uuid4().hex}_{clean_name}"
        content_type = file.type or "image/jpeg"
        sb.storage.from_("phone-photos").upload(
            path, file.getvalue(),
            file_options={"content-type": content_type, "upsert": "false"}
        )
        public_url = sb.storage.from_("phone-photos").get_public_url(path)
        urls.append(public_url)
    return urls

def render_header():
    left, right = st.columns([1, 5], vertical_alignment="center")
    with left:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=115)
        else:
            st.markdown("<div style='font-size:2rem;font-weight:900'>D<span style='color:#19a7a1'>E</span>RCELL</div>", unsafe_allow_html=True)
    with right:
        st.markdown(
            "<div style='padding:8px 0'><div style='font-size:2.25rem;font-weight:850;letter-spacing:2px'>DERCELL</div>"
            "<div style='color:#64748b;font-size:1.02rem'>Tecnología que conecta contigo</div></div>",
            unsafe_allow_html=True
        )
    st.divider()

def render_phone_card(phone: dict):
    photos = image_urls(phone)
    with st.container(border=True):
        if photos:
            st.image(photos[0], use_container_width=True)
        else:
            st.markdown("<div style='height:180px;display:flex;align-items:center;justify-content:center;background:#f1f5f9;border-radius:12px;font-size:4rem'>📱</div>", unsafe_allow_html=True)
        st.subheader(f"{phone.get('brand', '')} {phone.get('model', '')}".strip())
        st.markdown(f"<div style='font-size:1.65rem;font-weight:800;color:#0f766e'>{money(phone.get('price'))}</div>", unsafe_allow_html=True)
        if phone.get("short_description"):
            st.write(phone["short_description"])
        specs = [
            ("Almacenamiento", phone.get("storage")),
            ("RAM", phone.get("ram")),
            ("Pantalla", phone.get("screen")),
            ("Cámara", phone.get("camera")),
            ("Batería", phone.get("battery")),
            ("Color", phone.get("color")),
            ("Estado", phone.get("condition")),
        ]
        for label, value in specs:
            if value:
                st.caption(f"**{label}:** {value}")
        with st.expander("Ver todas las características"):
            fields = [
                ("Procesador", "processor"), ("Sistema operativo", "os"),
                ("Conectividad", "connectivity"), ("SIM", "sim"),
                ("Garantía", "warranty"), ("Stock", "stock"),
                ("Descripción completa", "description"),
            ]
            for label, key in fields:
                if phone.get(key) not in (None, ""):
                    st.write(f"**{label}:** {phone[key]}")
            if len(photos) > 1:
                st.markdown("**Más fotografías**")
                st.image(photos[1:], use_container_width=True)
        st.link_button("Consultar por WhatsApp", whatsapp_product_url(phone), type="primary", use_container_width=True)

def client_panel():
    st.markdown("## Catálogo de celulares")
    st.write("Encuentra tu próximo celular y consúltanos directamente por WhatsApp.")
    try:
        phones = load_phones()
    except Exception as exc:
        st.error("No se pudo conectar con Supabase. Revisa la configuración y vuelve a intentarlo.")
        st.caption(str(exc))
        return

    available = [p for p in phones if p.get("active", True)]
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        query = st.text_input("Buscar", placeholder="Marca o modelo (ej. Samsung, Redmi)")
    with c2:
        brands = sorted({p.get("brand", "") for p in available if p.get("brand")})
        brand = st.selectbox("Marca", ["Todas"] + brands)
    with c3:
        sort = st.selectbox("Ordenar precio", ["Recomendados", "Menor a mayor", "Mayor a menor"])
    if query:
        available = [p for p in available if query.lower() in f"{p.get('brand','')} {p.get('model','')}".lower()]
    if brand != "Todas":
        available = [p for p in available if p.get("brand") == brand]
    if sort == "Menor a mayor":
        available.sort(key=lambda p: float(p.get("price") or 0))
    elif sort == "Mayor a menor":
        available.sort(key=lambda p: float(p.get("price") or 0), reverse=True)

    if not available:
        st.info("Todavía no hay celulares publicados con esos filtros.")
        return
    st.caption(f"{len(available)} celular(es) disponible(s)")
    cols = st.columns(3, gap="large")
    for index, phone in enumerate(available):
        with cols[index % 3]:
            render_phone_card(phone)

def admin_panel():
    st.markdown("## Panel de administración")
    if not st.session_state.get("admin_authenticated", False):
        st.info("Inicia sesión para gestionar el catálogo.")
        with st.form("admin_login"):
            password = st.text_input("Contraseña de administrador", type="password")
            submitted = st.form_submit_button("Ingresar", type="primary")
        if submitted:
            admin_password = setting("ADMIN_PASSWORD")
            if admin_password and password == admin_password:
                st.session_state["admin_authenticated"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta o ADMIN_PASSWORD no configurada.")
        return

    if st.button("Cerrar sesión"):
        st.session_state["admin_authenticated"] = False
        st.rerun()

    try:
        sb = supabase_client()
        phones = load_phones()
    except Exception as exc:
        st.error("No se pudo conectar con Supabase. Revisa la configuración.")
        st.caption(str(exc))
        return

    add_tab, manage_tab = st.tabs(["➕ Añadir celular", "🛠️ Administrar catálogo"])
    with add_tab:
        with st.form("new_phone", clear_on_submit=True):
            st.markdown("### Información principal")
            a, b, c = st.columns(3)
            brand = a.text_input("Marca *", placeholder="Samsung")
            model = b.text_input("Modelo *", placeholder="Galaxy A55 5G")
            price = c.number_input("Precio (USD) *", min_value=0.0, step=10.0, format="%.2f")
            d, e, f = st.columns(3)
            condition = d.selectbox("Estado", ["Nuevo", "Seminuevo", "Usado"])
            stock = e.number_input("Unidades en stock", min_value=0, step=1, value=1)
            color = f.text_input("Color", placeholder="Negro")
            short_description = st.text_input("Descripción corta", placeholder="Potente, elegante y con gran cámara")
            description = st.text_area("Descripción completa")
            st.markdown("### Especificaciones técnicas")
            x1, x2, x3 = st.columns(3)
            storage = x1.text_input("Almacenamiento", placeholder="256 GB")
            ram = x2.text_input("Memoria RAM", placeholder="8 GB")
            processor = x3.text_input("Procesador")
            x4, x5, x6 = st.columns(3)
            screen = x4.text_input("Pantalla", placeholder="6.7 pulgadas AMOLED")
            camera = x5.text_input("Cámara", placeholder="50 MP + 12 MP")
            battery = x6.text_input("Batería", placeholder="5000 mAh")
            x7, x8, x9 = st.columns(3)
            os_name = x7.text_input("Sistema operativo", placeholder="Android 15")
            connectivity = x8.text_input("Conectividad", placeholder="5G, Wi-Fi, Bluetooth")
            sim = x9.text_input("SIM", placeholder="Dual SIM")
            warranty = st.text_input("Garantía", placeholder="12 meses")
            photos = st.file_uploader("Fotografías del celular", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
            active = st.checkbox("Publicar en el catálogo de clientes", value=True)
            submitted = st.form_submit_button("Guardar celular", type="primary", use_container_width=True)
        if submitted:
            if not brand.strip() or not model.strip() or price <= 0:
                st.error("Completa Marca, Modelo y un precio mayor que cero.")
            else:
                try:
                    photo_urls = upload_photos(photos)
                    payload = {
                        "brand": brand.strip(), "model": model.strip(), "price": float(price),
                        "condition": condition, "stock": int(stock), "color": color.strip(),
                        "short_description": short_description.strip(), "description": description.strip(),
                        "storage": storage.strip(), "ram": ram.strip(), "processor": processor.strip(),
                        "screen": screen.strip(), "camera": camera.strip(), "battery": battery.strip(),
                        "os": os_name.strip(), "connectivity": connectivity.strip(), "sim": sim.strip(),
                        "warranty": warranty.strip(), "photos": photo_urls, "active": active,
                    }
                    sb.table("phones").insert(payload).execute()
                    st.success("Celular guardado correctamente.")
                    st.rerun()
                except Exception as exc:
                    st.error("No se pudo guardar el celular. Revisa la tabla y el bucket de Supabase.")
                    st.caption(str(exc))

    with manage_tab:
        if not phones:
            st.info("Todavía no hay celulares registrados.")
        for phone in phones:
            title = f"{phone.get('brand','')} {phone.get('model','')} — {money(phone.get('price'))}"
            with st.expander(title):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"ID: `{phone.get('id')}`")
                    st.write(f"Publicado: {'Sí' if phone.get('active', True) else 'No'} · Stock: {phone.get('stock', 0)}")
                    pics = image_urls(phone)
                    if pics:
                        st.image(pics, width=140)
                with col2:
                    new_active = st.toggle("Visible para clientes", value=bool(phone.get("active", True)), key=f"active_{phone.get('id')}")
                    if new_active != bool(phone.get("active", True)):
                        try:
                            sb.table("phones").update({"active": new_active}).eq("id", phone["id"]).execute()
                            st.success("Visibilidad actualizada.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"No se pudo actualizar: {exc}")
                    confirm = st.checkbox("Confirmo eliminar", key=f"confirm_{phone.get('id')}")
                    if st.button("Eliminar celular", key=f"delete_{phone.get('id')}", type="secondary", disabled=not confirm):
                        try:
                            sb.table("phones").delete().eq("id", phone["id"]).execute()
                            st.success("Celular eliminado del catálogo.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"No se pudo eliminar: {exc}")

def main():
    render_header()
    st.markdown(
        f"<div style='background:linear-gradient(100deg,#0f172a,#134e4a);padding:22px 26px;border-radius:18px;color:white;margin-bottom:18px'>"
        f"<div style='font-size:1.75rem;font-weight:800'>Tu próximo celular está en DERCELL</div>"
        f"<div style='opacity:.9;margin:5px 0 14px'>Consulta precios, especificaciones y disponibilidad.</div>"
        f"<a href='{WHATSAPP_URL}' target='_blank' style='display:inline-block;background:#25D366;color:#062b18;padding:10px 16px;border-radius:9px;text-decoration:none;font-weight:750'>Escríbenos por WhatsApp</a></div>",
        unsafe_allow_html=True
    )
    client_tab, admin_tab = st.tabs(["🛍️ Panel de clientes", "🔐 Panel de administrador"])
    with client_tab:
        client_panel()
    with admin_tab:
        admin_panel()
    st.divider()
    st.caption("© DERCELL · Catálogo digital de celulares · Atención por WhatsApp")

if __name__ == "__main__":
    main()

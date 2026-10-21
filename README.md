# DERCELL — Catálogo profesional de celulares

Aplicación web en Python + Streamlit conectada a Supabase, con:
- Panel de clientes con búsqueda, filtro por marca, orden por precio y fichas de producto.
- Panel de administrador protegido por contraseña.
- Alta de celulares con precio, descripción, especificaciones técnicas, stock, estado y varias fotografías.
- Activar/desactivar productos y eliminarlos del catálogo.
- Enlace de consulta directa a WhatsApp: https://wa.me/593990359268
- Cada celular prepara un mensaje de WhatsApp con la marca y modelo de ese dispositivo.
- Logo proporcionado, incluido en `assets/logo.png`.

## 1. Configurar Supabase
1. Crea un proyecto en https://supabase.com/.
2. En `SQL Editor`, ejecuta el archivo `supabase_setup.sql`.
3. En `Project Settings > API`, copia la Project URL y la `service_role` key (o secret key equivalente compatible).
4. **Nunca publiques la service role key ni la pongas en el navegador.** Esta app la utiliza solamente en el servidor.

## 2. Instalar y ejecutar en tu computadora
Requiere Python 3.10 o superior.

```bash
python -m venv .venv
```
Windows:
```bash
.venv\Scripts\activate
```
macOS/Linux:
```bash
source .venv/bin/activate
```
Después:
```bash
pip install -r requirements.txt
```
Copia `.env.example` a `.env` y completa los valores. Para cargar `.env`, ejecuta:
```bash
streamlit run app.py
```
Si tu entorno no carga `.env` automáticamente, configura esas tres variables como variables de entorno o crea `.streamlit/secrets.toml` con:

```toml
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "TU_CLAVE_PRIVADA"
ADMIN_PASSWORD = "UNA_CONTRASENA_SEGURA"
```

## 3. Publicar en internet
Puedes desplegar el proyecto en Streamlit Community Cloud o en un servidor propio:
1. Sube los archivos del proyecto a un repositorio privado.
2. Crea una app y selecciona `app.py` como archivo principal.
3. Añade `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y `ADMIN_PASSWORD` en la sección Secrets del despliegue.
4. No subas `.env` ni publiques la clave privada.

## Notas de seguridad
- El panel de administración está protegido por una contraseña compartida configurada en `ADMIN_PASSWORD`; usa una contraseña larga y no la compartas.
- Para un negocio con varios administradores, pagos o datos sensibles, conviene migrar a autenticación Supabase Auth con roles individuales, registro de auditoría y políticas RLS por usuario.
- Las fotos se guardan en el bucket público `phone-photos`; el bucket permite visualizar imágenes, no escribir desde el navegador.

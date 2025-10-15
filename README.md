# 🤖 R-60 Bot

Sistema de automatización inteligente para procesar formularios R-60 desde Gmail, validar y escribir en Google Sheets, archivar en Google Drive y notificar resultados automáticamente.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Configuración Inicial](#-configuración-inicial)
  - [1. Obtener Credenciales de Google Cloud](#1-obtener-credenciales-de-google-cloud)
  - [2. Configurar Variables de Entorno](#2-configurar-variables-de-entorno)
  - [3. Primera Autenticación OAuth2](#3-primera-autenticación-oauth2)
- [Instalación y Ejecución](#-instalación-y-ejecución)
  - [Opción A: Ejecución Local](#opción-a-ejecución-local)
  - [Opción B: Docker (Recomendado)](#opción-b-docker-recomendado)
  - [Opción C: Portainer (Producción)](#opción-c-portainer-producción)
- [Ejecución Periódica Automática](#-ejecución-periódica-automática)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tipos de Formularios Soportados](#-tipos-de-formularios-soportados)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

---

## ✨ Características

- ✅ **Monitoreo Automático de Gmail** - Busca emails con adjuntos R-60 según query personalizable
- ✅ **Detección Inteligente de Tipo** - Identifica automáticamente si es formulario de Compras, Servicios o Costos
- ✅ **Validación de Duplicados** - Evita procesar el mismo formulario dos veces
- ✅ **Extracción Robusta de Datos** - Parser inteligente con manejo de errores
- ✅ **Integración con Google Sheets** - Escritura automática con formato consistente
- ✅ **Archivo en Google Drive** - Estructura organizada por año/mes
- ✅ **Notificaciones por Email** - Confirmaciones de éxito, errores y duplicados con formato HTML
- ✅ **Etiquetado Automático** - Clasifica emails procesados con etiquetas personalizables
- ✅ **Logging Completo** - Logs detallados con rotación automática
- ✅ **Dockerizado** - Listo para producción con Portainer

---

## 🏗️ Arquitectura

El bot está construido con una arquitectura modular y escalable:

```
R-60 Bot
├── main.py                    # Orquestador principal
├── config.py                  # Configuración centralizada
├── src/
│   ├── auth/                  # Autenticación OAuth2
│   ├── services/              # Servicios de Google APIs
│   │   ├── gmail_service.py
│   │   ├── sheets_service.py
│   │   └── drive_service.py
│   ├── parsers/               # Parseo de formularios
│   │   └── excel_parser.py
│   └── utils/                 # Utilidades compartidas
│       ├── exceptions.py
│       └── logger.py
└── credentials/               # Credenciales de Google
```

**Flujo de Datos:**
```
Gmail → Descarga → Parser → Validación → Sheets → Drive → Notificación
```

---

## 📦 Requisitos Previos

### Software Necesario

- **Python 3.11+** (para ejecución local)
- **Docker** (para ejecución en contenedor)
- **Portainer** (opcional, para gestión web)

### Cuentas y Accesos

1. **Cuenta de Google** con acceso a:
   - Gmail API
   - Google Sheets API
   - Google Drive API

2. **Proyecto en Google Cloud Console**
   - Con las APIs habilitadas
   - Credenciales OAuth2 configuradas

---

## ⚙️ Configuración Inicial

### 1. Obtener Credenciales de Google Cloud

#### Paso 1.1: Crear Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un nuevo proyecto o selecciona uno existente
3. Anota el **nombre del proyecto**

#### Paso 1.2: Habilitar APIs

1. En el menú lateral, ve a **APIs y servicios** > **Biblioteca**
2. Busca y habilita las siguientes APIs:
   - **Gmail API**
   - **Google Sheets API**
   - **Google Drive API**

#### Paso 1.3: Crear Credenciales OAuth2

1. Ve a **APIs y servicios** > **Credenciales**
2. Click en **+ CREAR CREDENCIALES** > **ID de cliente de OAuth**
3. Si es la primera vez, configura la **Pantalla de consentimiento OAuth**:
   - Tipo de usuario: **Externo** (o Interno si tienes Google Workspace)
   - Completa la información básica de la app
   - En **Scopes**, no es necesario agregar nada aún
   - Agrega tu email como usuario de prueba
4. Vuelve a **Credenciales** > **+ CREAR CREDENCIALES** > **ID de cliente de OAuth**
5. Tipo de aplicación: **Aplicación de escritorio**
6. Nombre: `R60 Bot`
7. Click en **CREAR**
8. **Descarga el JSON** (botón de descarga junto a las credenciales creadas)
9. Renombra el archivo descargado a `credentials.json`
10. Guárdalo en la carpeta `credentials/` del proyecto

```bash
# Estructura esperada
credentials/
└── credentials.json  # ← Tu archivo descargado y renombrado
```

### 2. Configurar Variables de Entorno

#### Paso 2.1: Obtener IDs Necesarios

**Google Sheet ID:**
- Abre tu planilla de Google Sheets
- La URL tiene este formato: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`
- Copia el `SHEET_ID`

**Google Drive Folder ID:**
- Abre la carpeta de Drive donde quieres archivar los formularios
- La URL tiene este formato: `https://drive.google.com/drive/folders/{FOLDER_ID}`
- Copia el `FOLDER_ID`

#### Paso 2.2: Crear Archivo .env

1. Copia el archivo de ejemplo:
   ```bash
   cp env.example .env
   ```

2. Edita `.env` con tus valores:
   ```bash
   # --- GOOGLE SHEETS ---
   GOOGLE_SHEET_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz123456789
   GOOGLE_SHEET_NAME=Hoja 1
   
   # --- GOOGLE DRIVE ---
   GOOGLE_DRIVE_FOLDER_ID=1ZyXwVuTsRqPoNmLkJiHgFeDcBa987654321
   
   # --- GMAIL ---
   GMAIL_QUERY=subject:R-60 has:attachment filename:xlsx is:unread
   NOTIFICATION_EMAIL=tu_email@ejemplo.com
   
   # --- CONFIGURACIÓN ---
   LOG_LEVEL=INFO
   MAX_EMAILS_PER_RUN=10
   
   # --- ETIQUETAS GMAIL ---
   LABEL_PROCESSED=R60/Procesado
   LABEL_ERROR=R60/Error
   LABEL_DUPLICATE=R60/Duplicado
   ```

### 3. Primera Autenticación OAuth2

El primer vez que ejecutes el bot, se abrirá tu navegador para completar el flujo OAuth2:

1. El navegador se abrirá automáticamente
2. Selecciona tu cuenta de Google
3. Acepta los permisos solicitados
4. Verás un mensaje de éxito
5. El bot guardará un `token.json` automáticamente
6. Las siguientes ejecuciones usarán este token (válido por ~1 semana)

> ⚠️ **Importante:** Si ves advertencia de "App no verificada", click en "Avanzado" > "Ir a R60 Bot (no seguro)". Esto es normal para apps en desarrollo.

---

## 🚀 Instalación y Ejecución

### Opción A: Ejecución Local

#### 1. Clonar e Instalar

```bash
# Clonar repositorio
git clone <tu-repositorio>
cd R-60-Bot-Test

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### 2. Configurar

Sigue los pasos de [Configuración Inicial](#-configuración-inicial)

#### 3. Ejecutar

```bash
# Primera ejecución (autenticación OAuth2)
python main.py

# Ejecuciones posteriores
python main.py
```

---

### Opción B: Docker (Recomendado)

#### 1. Construir Imagen

```bash
docker build -t r60-bot:latest .
```

#### 2. Ejecutar con Docker Compose

```bash
# Editar docker-compose.yml con tus variables de entorno
# O crear archivo .env (ver sección anterior)

# Primera ejecución para autenticación
docker-compose run --rm r60-bot

# Ejecuciones posteriores
docker-compose up -d
```

#### 3. Ver Logs

```bash
docker-compose logs -f r60-bot
```

---

### Opción C: Portainer (Producción)

#### Método 1: Stack desde Template

1. En Portainer, ve a **Stacks** > **Add Stack**
2. Nombre: `r60-bot`
3. En **Web editor**, pega el contenido de `portainer-stack.yml`
4. Edita las variables de entorno directamente en el YAML
5. Click en **Deploy the stack**

#### Método 2: Docker Compose Upload

1. En Portainer, ve a **Stacks** > **Add Stack**
2. Nombre: `r60-bot`
3. En **Upload**, sube el archivo `docker-compose.yml`
4. En **Environment variables**, agrega tus valores
5. Click en **Deploy the stack**

#### Copiar Credenciales al Volumen

**Opción A: Desde Portainer UI**
1. Ve a **Volumes** > `r60_credentials` > **Browse**
2. Sube `credentials.json` (y `token.json` si ya lo tienes)

**Opción B: Desde CLI del Host**
```bash
# Crear volumen
docker volume create r60_credentials

# Copiar credentials.json
docker run --rm \
  -v r60_credentials:/data \
  -v $(pwd)/credentials:/source \
  alpine cp /source/credentials.json /data/

# Si ya tienes token.json
docker run --rm \
  -v r60_credentials:/data \
  -v $(pwd)/credentials:/source \
  alpine cp /source/token.json /data/
```

#### Primera Ejecución OAuth2 en Docker

Si no tienes `token.json`, ejecuta localmente primero:
```bash
python main.py  # Se abrirá navegador
# Copia el token.json generado al volumen de Docker
```

O ejecuta el contenedor en modo interactivo (no recomendado para servidores sin GUI):
```bash
docker run --rm -it \
  -v r60_credentials:/app/credentials \
  -v r60_logs:/app/logs \
  --env-file .env \
  r60-bot:latest
```

---

## ⏰ Ejecución Periódica Automática

### Opción 1: Cron Job en el Host (Linux/Mac)

```bash
# Editar crontab
crontab -e

# Ejecutar cada 30 minutos
*/30 * * * * docker start r60-bot >> /var/log/r60-bot-cron.log 2>&1

# Ejecutar cada hora a los :05 minutos
5 * * * * docker start r60-bot >> /var/log/r60-bot-cron.log 2>&1

# Ejecutar de lunes a viernes a las 9 AM
0 9 * * 1-5 docker start r60-bot >> /var/log/r60-bot-cron.log 2>&1
```

### Opción 2: Task Scheduler (Windows)

1. Abre **Programador de tareas**
2. **Crear tarea básica**
3. Nombre: `R60 Bot Execution`
4. Desencadenador: **Diariamente** (o según necesidad)
5. Acción: **Iniciar un programa**
6. Programa: `docker`
7. Argumentos: `start r60-bot`

### Opción 3: Portainer Webhook + Cron Externo

1. En Portainer, ve al contenedor `r60-bot` > **Container details**
2. Copia el **Webhook URL**
3. Configura un cron job que llame a ese webhook:

```bash
# Crontab
*/30 * * * * curl -X POST https://tu-portainer.com/api/webhooks/xxxxxx
```

---

## 📁 Estructura del Proyecto

```
R-60 Bot-Test/
├── main.py                    # Orquestador principal
├── config.py                  # Configuración centralizada
├── requirements.txt           # Dependencias Python
├── Dockerfile                 # Imagen Docker multi-etapa
├── docker-compose.yml         # Orquestación Docker
├── portainer-stack.yml        # Template para Portainer
├── .gitignore                 # Archivos ignorados por Git
├── .dockerignore              # Archivos ignorados por Docker
├── env.example                # Plantilla de variables de entorno
├── README.md                  # Esta documentación
│
├── src/                       # Código fuente
│   ├── auth/                  # Autenticación
│   │   └── google_auth.py
│   ├── services/              # Servicios de APIs
│   │   ├── gmail_service.py
│   │   ├── sheets_service.py
│   │   └── drive_service.py
│   ├── parsers/               # Parseo de formularios
│   │   └── excel_parser.py
│   └── utils/                 # Utilidades
│       ├── exceptions.py
│       └── logger.py
│
├── credentials/               # Credenciales (NO en Git)
│   ├── credentials.json       # OAuth2 credentials
│   └── token.json             # Token de acceso (generado)
│
├── temp/                      # Archivos temporales
├── logs/                      # Logs de ejecución
└── tests/                     # Tests unitarios
```

---

## 📝 Tipos de Formularios Soportados

El bot detecta automáticamente tres tipos de formularios R-60:

### 1. Formularios de COMPRAS
- **Detección:** Palabras clave como "compra", "adquisición", "purchase"
- **Campos extraídos:**
  - Descripción del producto
  - Cantidad
  - Unidad de medida
  - Precio unitario
  - Total

### 2. Formularios de SERVICIOS
- **Detección:** Palabras clave como "servicio", "service"
- **Campos extraídos:**
  - Descripción del servicio
  - Proveedor
  - Monto
  - Fecha del servicio

### 3. Formularios de COSTOS
- **Detección:** Palabras clave como "costo", "gasto", "expense", "cost"
- **Campos extraídos:**
  - Concepto del gasto
  - Categoría
  - Monto
  - Fecha

### Personalizar Mapeo de Celdas

Edita `config.py` para ajustar las celdas según tu formato de formulario:

```python
FORM_TYPE_MAPPINGS = {
    'COMPRAS': {
        'header': {
            'numero_formulario': 'D2',  # Celda donde está el número
            'fecha': 'D3',
            'solicitante': 'D4',
            # ...
        },
        'items_start_row': 10,  # Fila donde comienza la tabla
        'items_columns': {
            'numero_item': 'A',
            'descripcion': 'B',
            # ...
        }
    }
}
```

---

## 🔧 Troubleshooting

### Error: "Archivo de credenciales no encontrado"

**Causa:** No existe `credentials.json` en la carpeta `credentials/`

**Solución:**
1. Sigue el paso [1. Obtener Credenciales de Google Cloud](#1-obtener-credenciales-de-google-cloud)
2. Asegúrate de que el archivo se llame exactamente `credentials.json`
3. Verifica la ruta: `credentials/credentials.json`

---

### Error: "Configuración incompleta. Faltan variables de entorno"

**Causa:** El archivo `.env` no existe o está incompleto

**Solución:**
1. Copia `env.example` a `.env`
2. Completa todas las variables obligatorias
3. Verifica que no haya espacios extra en los valores

---

### Error: "The file has been identified as malware"

**Causa:** Google marca el archivo OAuth como sospechoso

**Solución:**
1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. **APIs y servicios** > **Pantalla de consentimiento OAuth**
3. Publica la aplicación (cambiar de Testing a Production)
4. O agrega tu email como usuario de prueba

---

### Error: "El formulario Nº XXX ya ha sido procesado anteriormente"

**Causa:** Formulario duplicado detectado

**Comportamiento esperado:** El bot:
- No procesa el formulario nuevamente
- Etiqueta el email como "R60/Duplicado"
- Envía notificación de duplicado
- Continúa con el siguiente email

**Si necesitas reprocesar:**
1. Elimina la fila del formulario en Google Sheets
2. Remueve la etiqueta "R60/Duplicado" del email en Gmail
3. Ejecuta el bot nuevamente

---

### El bot no encuentra emails

**Causa:** La query de Gmail no coincide con tus emails

**Solución:**
1. Verifica la variable `GMAIL_QUERY` en `.env`
2. Prueba la query directamente en Gmail
3. Ajusta según tus necesidades:
   ```bash
   # Ejemplos de queries válidas:
   GMAIL_QUERY="subject:R-60 has:attachment filename:xlsx"
   GMAIL_QUERY="from:usuario@ejemplo.com has:attachment"
   GMAIL_QUERY="subject:(R-60 OR formulario) has:attachment"
   ```

---

### OAuth2 falla en Docker/Servidor sin GUI

**Causa:** El flujo OAuth2 requiere un navegador

**Solución 1 (Recomendada):**
1. Ejecuta `python main.py` localmente (con GUI)
2. Se abrirá el navegador y completarás la autenticación
3. Copia el `token.json` generado al volumen de Docker:
   ```bash
   docker cp credentials/token.json r60-bot:/app/credentials/
   ```

**Solución 2 (Avanzada):**
Usa flujo OAuth2 con puerto de callback configurado manualmente

---

### Los logs no se guardan

**Causa:** Permisos incorrectos en el volumen

**Solución:**
```bash
# Verificar permisos del volumen
docker volume inspect r60_logs

# Si es necesario, ajustar permisos
docker run --rm -v r60_logs:/data alpine chmod 777 /data
```

---

## ❓ FAQ

### ¿Cuánto tiempo es válido el token.json?

El token de acceso expira típicamente después de 1 hora, pero el token de refresco es válido por ~7 días. El bot automáticamente refresca el token cuando expira.

### ¿Puedo procesar formularios de múltiples cuentas de Gmail?

No directamente. Cada instancia del bot se autentica con una cuenta. Para múltiples cuentas, despliega múltiples instancias con diferentes credenciales.

### ¿Cómo cambio el formato del nombre de archivo en Drive?

Edita la función `archive_form()` en `src/services/drive_service.py`:

```python
# Formato actual: YYYY-MM-DD_Form-NUMERO_Solicitante.xlsx
new_name = f"{fecha_str}_Form-{numero_form}_{solicitante}.xlsx"

# Ejemplo alternativo:
new_name = f"R60_{numero_form}_{fecha_str}.xlsx"
```

### ¿El bot borra los emails procesados?

No. El bot solo:
- Marca como leído
- Agrega etiquetas (Procesado/Error/Duplicado)
- Los emails permanecen en tu bandeja

### ¿Puedo personalizar las notificaciones por email?

Sí. Edita las plantillas en `config.py`:

```python
EMAIL_TEMPLATES = {
    'success': {
        'subject': '✅ Tu asunto personalizado...',
        'body': '''<html>... tu HTML ...</html>'''
    }
}
```

### ¿Cómo monitoreo el bot en producción?

**Opción 1: Portainer**
- Ve a Containers > r60-bot > Logs
- Activa "Auto-refresh logs"

**Opción 2: Logs persistentes**
```bash
# Ver logs en tiempo real
docker exec r60-bot tail -f /app/logs/r60bot_$(date +%Y%m%d).log

# O con volumen montado
tail -f /ruta/al/volumen/logs/r60bot_*.log
```

**Opción 3: Integración con sistemas de monitoreo**
- Los logs están en formato estructurado
- Puedes integrar con: ELK Stack, Prometheus, Grafana, etc.

---

## 📞 Soporte

Si encuentras problemas no cubiertos en este README:

1. Revisa los logs detallados en `logs/r60bot_YYYYMMDD.log`
2. Verifica que todas las APIs estén habilitadas en Google Cloud Console
3. Confirma que las variables de entorno estén correctamente configuradas
4. Asegúrate de tener la versión correcta de Python (3.11+)

---

## 📄 Licencia

Este proyecto es de uso interno. Todos los derechos reservados.

---

## 🎯 Roadmap Futuro

- [ ] Soporte para más tipos de formularios
- [ ] Dashboard web para visualización
- [ ] API REST para integración externa
- [ ] Procesamiento en lote de archivos históricos
- [ ] Notificaciones por Slack/Teams
- [ ] Tests unitarios completos
- [ ] CI/CD con GitHub Actions

---

**Desarrollado con ❤️ por el equipo de automatización**



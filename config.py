"""
Configuración centralizada del R-60 Bot
Contiene constantes, mapeos de celdas y configuraciones del sistema
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==================== RUTAS DEL PROYECTO ====================
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Archivos de credenciales Google
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

# ==================== CONFIGURACIÓN GOOGLE APIs ====================

# Scopes necesarios para las APIs de Google
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# Google Sheets
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Hoja 1')

# Google Drive
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
DRIVE_ROOT_FOLDER = 'R60_PROCESADOS'

# Gmail
GMAIL_QUERY = os.getenv('GMAIL_QUERY', 'subject:R-60 has:attachment filename:xlsx is:unread')
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')

# ==================== ETIQUETAS GMAIL ====================
LABEL_PROCESSED = os.getenv('LABEL_PROCESSED', 'R60/Procesado')
LABEL_ERROR = os.getenv('LABEL_ERROR', 'R60/Error')
LABEL_DUPLICATE = os.getenv('LABEL_DUPLICATE', 'R60/Duplicado')

# ==================== CONFIGURACIÓN DE EJECUCIÓN ====================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_EMAILS_PER_RUN = int(os.getenv('MAX_EMAILS_PER_RUN', '10'))

# ==================== MAPEO DE CELDAS R-60 ====================

# Encabezado común para todos los tipos de formularios
HEADER_MAPPING_COMMON = {
    'numero_formulario': 'D2',
    'fecha': 'D3',
    'solicitante': 'D4',
    'area': 'D5',
    'observaciones': 'D6',
}

# Mapeo específico por tipo de formulario
FORM_TYPE_MAPPINGS = {
    'COMPRAS': {
        'header': HEADER_MAPPING_COMMON,
        'items_start_row': 10,  # Fila donde comienza la tabla de ítems
        'items_columns': {
            'numero_item': 'A',
            'descripcion': 'B',
            'cantidad': 'C',
            'unidad': 'D',
            'precio_unitario': 'E',
            'total': 'F',
        }
    },
    'SERVICIOS': {
        'header': HEADER_MAPPING_COMMON,
        'items_start_row': 10,
        'items_columns': {
            'numero_item': 'A',
            'servicio': 'B',
            'proveedor': 'C',
            'monto': 'D',
            'fecha_servicio': 'E',
        }
    },
    'COSTOS': {
        'header': HEADER_MAPPING_COMMON,
        'items_start_row': 10,
        'items_columns': {
            'numero_item': 'A',
            'concepto': 'B',
            'categoria': 'C',
            'monto': 'D',
            'fecha': 'E',
        }
    }
}

# Identificación de tipo de formulario (palabras clave en el título/hoja)
FORM_TYPE_KEYWORDS = {
    'COMPRAS': ['compra', 'adquisición', 'purchase'],
    'SERVICIOS': ['servicio', 'service'],
    'COSTOS': ['costo', 'gasto', 'expense', 'cost']
}

# ==================== ENCABEZADOS GOOGLE SHEETS ====================

# Encabezado para la planilla de destino
SHEET_HEADERS = [
    'Fecha Procesamiento',
    'Nº Formulario',
    'Fecha Formulario',
    'Tipo Formulario',
    'Solicitante',
    'Área',
    'Nº Item',
    'Descripción/Servicio/Concepto',
    'Cantidad/Proveedor/Categoría',
    'Unidad/Monto',
    'Precio Unitario/Fecha Servicio/Fecha',
    'Total/Monto',
    'Observaciones',
    'Archivo Original'
]

# ==================== PLANTILLAS DE NOTIFICACIÓN ====================

EMAIL_TEMPLATES = {
    'success': {
        'subject': '✅ Formulario R-60 procesado exitosamente - {form_number}',
        'body': '''
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #28a745;">✅ Formulario Procesado Exitosamente</h2>
                    <p>El formulario R-60 ha sido procesado correctamente:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Nº de Formulario:</strong> {form_number}</p>
                        <p><strong>Fecha:</strong> {form_date}</p>
                        <p><strong>Solicitante:</strong> {requester}</p>
                        <p><strong>Tipo:</strong> {form_type}</p>
                        <p><strong>Ítems procesados:</strong> {items_count}</p>
                    </div>
                    
                    <p>Los datos han sido registrados en la planilla de Google Sheets y el archivo original ha sido archivado en Google Drive.</p>
                    
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #dee2e6;">
                    <p style="font-size: 0.9em; color: #6c757d;">
                        <em>Este es un mensaje automático del R-60 Bot. No responder a este email.</em>
                    </p>
                </div>
            </body>
        </html>
        '''
    },
    'error': {
        'subject': '❌ Error al procesar formulario R-60',
        'body': '''
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545;">❌ Error en el Procesamiento</h2>
                    <p>Se ha producido un error al procesar el formulario R-60:</p>
                    
                    <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <p><strong>Error:</strong> {error_message}</p>
                        <p><strong>Archivo:</strong> {file_name}</p>
                    </div>
                    
                    <p>Por favor, revisa el formulario y vuelve a enviarlo. Si el problema persiste, contacta al administrador del sistema.</p>
                    
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #dee2e6;">
                    <p style="font-size: 0.9em; color: #6c757d;">
                        <em>Este es un mensaje automático del R-60 Bot. No responder a este email.</em>
                    </p>
                </div>
            </body>
        </html>
        '''
    },
    'duplicate': {
        'subject': '⚠️ Formulario R-60 duplicado - {form_number}',
        'body': '''
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #ffc107;">⚠️ Formulario Duplicado</h2>
                    <p>El formulario R-60 ya ha sido procesado anteriormente:</p>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <p><strong>Nº de Formulario:</strong> {form_number}</p>
                        <p><strong>Solicitante:</strong> {requester}</p>
                    </div>
                    
                    <p>No se han realizado cambios en la planilla. Si necesitas modificar este formulario, contacta al administrador.</p>
                    
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #dee2e6;">
                    <p style="font-size: 0.9em; color: #6c757d;">
                        <em>Este es un mensaje automático del R-60 Bot. No responder a este email.</em>
                    </p>
                </div>
            </body>
        </html>
        '''
    }
}

# ==================== VALIDACIONES ====================

def validate_config():
    """Valida que las configuraciones esenciales estén definidas"""
    missing_configs = []
    
    if not GOOGLE_SHEET_ID:
        missing_configs.append('GOOGLE_SHEET_ID')
    if not GOOGLE_DRIVE_FOLDER_ID:
        missing_configs.append('GOOGLE_DRIVE_FOLDER_ID')
    if not NOTIFICATION_EMAIL:
        missing_configs.append('NOTIFICATION_EMAIL')
    
    if missing_configs:
        raise ValueError(
            f"Configuración incompleta. Faltan las siguientes variables de entorno: {', '.join(missing_configs)}\n"
            f"Por favor, crea un archivo .env basado en env.example y completa los valores."
        )
    
    # Validar que existan las carpetas necesarias
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    # Test de configuración
    try:
        validate_config()
        print("✅ Configuración válida")
        print(f"Sheet ID: {GOOGLE_SHEET_ID}")
        print(f"Drive Folder ID: {GOOGLE_DRIVE_FOLDER_ID}")
        print(f"Notification Email: {NOTIFICATION_EMAIL}")
    except ValueError as e:
        print(f"❌ {e}")



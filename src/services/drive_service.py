"""
Servicio para interactuar con Google Drive API
Encapsula todas las operaciones de Drive: gestión de carpetas y archivos
"""

from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

import config
from src.utils.logger import logger, log_api_call
from src.utils.exceptions import GoogleAPIError


class DriveService:
    """Servicio para gestionar operaciones con Google Drive"""
    
    def __init__(self, credentials: Credentials):
        """
        Inicializa el servicio de Drive
        
        Args:
            credentials: Credenciales de Google autenticadas
        """
        self.credentials = credentials
        self.service = build('drive', 'v3', credentials=credentials)
        self.root_folder_id = config.GOOGLE_DRIVE_FOLDER_ID
        logger.info("Drive Service inicializado")
    
    @log_api_call(logger, "Drive")
    def find_folder_by_name(self, folder_name: str, parent_id: str = None) -> Optional[str]:
        """
        Busca una carpeta por nombre dentro de un padre específico
        
        Args:
            folder_name: Nombre de la carpeta a buscar
            parent_id: ID de la carpeta padre (si no se proporciona, busca en root_folder_id)
            
        Returns:
            ID de la carpeta si existe, None si no existe
        """
        parent_id = parent_id or self.root_folder_id
        
        try:
            query = (
                f"name='{folder_name}' and "
                f"'{parent_id}' in parents and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"trashed=false"
            )
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                logger.debug(f"Carpeta '{folder_name}' encontrada: {items[0]['id']}")
                return items[0]['id']
            
            logger.debug(f"Carpeta '{folder_name}' no encontrada")
            return None
        
        except HttpError as e:
            raise GoogleAPIError('Drive', 'find_folder_by_name', str(e))
    
    @log_api_call(logger, "Drive")
    def create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Crea una carpeta en Drive
        
        Args:
            folder_name: Nombre de la carpeta a crear
            parent_id: ID de la carpeta padre (si no se proporciona, usa root_folder_id)
            
        Returns:
            ID de la carpeta creada
        """
        parent_id = parent_id or self.root_folder_id
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()
            
            logger.info(f"✅ Carpeta '{folder_name}' creada: {folder.get('id')}")
            return folder.get('id')
        
        except HttpError as e:
            raise GoogleAPIError('Drive', 'create_folder', str(e))
    
    @log_api_call(logger, "Drive")
    def ensure_folder_exists(self, folder_name: str, parent_id: str = None) -> str:
        """
        Asegura que una carpeta exista, creándola si es necesario
        
        Args:
            folder_name: Nombre de la carpeta
            parent_id: ID de la carpeta padre
            
        Returns:
            ID de la carpeta (existente o recién creada)
        """
        folder_id = self.find_folder_by_name(folder_name, parent_id)
        
        if folder_id:
            return folder_id
        
        return self.create_folder(folder_name, parent_id)
    
    @log_api_call(logger, "Drive")
    def ensure_folder_structure(self, year: str = None, month: str = None) -> str:
        """
        Asegura que exista la estructura de carpetas /R60_PROCESADOS/YYYY/MM/
        
        Args:
            year: Año (formato YYYY), si no se proporciona usa el año actual
            month: Mes (formato MM), si no se proporciona usa el mes actual
            
        Returns:
            ID de la carpeta final (mes)
        """
        now = datetime.now()
        year = year or now.strftime('%Y')
        month = month or now.strftime('%m')
        
        logger.info(f"Asegurando estructura de carpetas: {config.DRIVE_ROOT_FOLDER}/{year}/{month}")
        
        # 1. Asegurar carpeta raíz R60_PROCESADOS
        root_id = self.ensure_folder_exists(
            config.DRIVE_ROOT_FOLDER, 
            self.root_folder_id
        )
        
        # 2. Asegurar carpeta del año
        year_id = self.ensure_folder_exists(year, root_id)
        
        # 3. Asegurar carpeta del mes
        month_id = self.ensure_folder_exists(month, year_id)
        
        logger.info(f"✅ Estructura de carpetas lista: {month_id}")
        return month_id
    
    @log_api_call(logger, "Drive")
    def upload_file(
        self, 
        file_path: Path, 
        folder_id: str, 
        new_name: str = None
    ) -> Dict[str, str]:
        """
        Sube un archivo a Drive
        
        Args:
            file_path: Ruta del archivo local
            folder_id: ID de la carpeta de destino
            new_name: Nuevo nombre para el archivo (opcional)
            
        Returns:
            Diccionario con id, name y webViewLink del archivo subido
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        file_name = new_name or file_path.name
        
        try:
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            # Determinar MIME type
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            media = MediaFileUpload(
                str(file_path),
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            logger.info(f"✅ Archivo subido a Drive: {file_name} ({file.get('id')})")
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'webViewLink': file.get('webViewLink', '')
            }
        
        except HttpError as e:
            raise GoogleAPIError('Drive', 'upload_file', str(e))
    
    @log_api_call(logger, "Drive")
    def archive_form(
        self, 
        file_path: Path, 
        form_data: Dict
    ) -> Dict[str, str]:
        """
        Archiva un formulario R-60 en la estructura de carpetas apropiada
        
        Args:
            file_path: Ruta del archivo Excel local
            form_data: Datos del formulario (para determinar año/mes y nombre)
            
        Returns:
            Información del archivo subido
        """
        # Extraer fecha del formulario para determinar año/mes
        fecha_formulario = form_data.get('fecha', '')
        
        try:
            # Intentar parsear la fecha
            if fecha_formulario:
                fecha_obj = datetime.strptime(str(fecha_formulario), '%Y-%m-%d')
            else:
                fecha_obj = datetime.now()
        except ValueError:
            # Si no se puede parsear, usar fecha actual
            fecha_obj = datetime.now()
        
        year = fecha_obj.strftime('%Y')
        month = fecha_obj.strftime('%m')
        
        # Asegurar estructura de carpetas
        folder_id = self.ensure_folder_structure(year, month)
        
        # Generar nombre estandarizado
        # Formato: YYYY-MM-DD_Form-NUMERO_Solicitante.xlsx
        numero_form = form_data.get('numero_formulario', 'SinNumero')
        solicitante = form_data.get('solicitante', 'Desconocido')
        # Limpiar nombre de caracteres inválidos
        solicitante = "".join(c for c in solicitante if c.isalnum() or c in (' ', '-', '_')).strip()
        solicitante = solicitante.replace(' ', '_')
        
        fecha_str = fecha_obj.strftime('%Y-%m-%d')
        new_name = f"{fecha_str}_Form-{numero_form}_{solicitante}.xlsx"
        
        # Subir archivo
        file_info = self.upload_file(file_path, folder_id, new_name)
        
        logger.info(f"✅ Formulario archivado: {new_name}")
        return file_info
    
    @log_api_call(logger, "Drive")
    def get_file_link(self, file_id: str) -> str:
        """
        Obtiene el enlace web de un archivo
        
        Args:
            file_id: ID del archivo
            
        Returns:
            URL del archivo
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            
            return file.get('webViewLink', '')
        
        except HttpError as e:
            raise GoogleAPIError('Drive', 'get_file_link', str(e))



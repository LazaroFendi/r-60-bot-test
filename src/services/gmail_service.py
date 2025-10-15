"""
Servicio para interactuar con Gmail API
Encapsula todas las operaciones de Gmail: búsqueda, descarga, etiquetado y notificaciones
"""

import base64
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

import config
from src.utils.logger import logger, log_api_call
from src.utils.exceptions import GoogleAPIError, AdjuntoNoEncontradoError


class GmailService:
    """Servicio para gestionar operaciones con Gmail"""
    
    def __init__(self, credentials: Credentials):
        """
        Inicializa el servicio de Gmail
        
        Args:
            credentials: Credenciales de Google autenticadas
        """
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)
        logger.info("Gmail Service inicializado")
    
    @log_api_call(logger, "Gmail")
    def search_emails(self, query: str = None, max_results: int = None) -> List[Dict]:
        """
        Busca emails según una query
        
        Args:
            query: Query de búsqueda de Gmail (si no se proporciona, usa la del config)
            max_results: Número máximo de resultados (si no se proporciona, usa el del config)
            
        Returns:
            Lista de mensajes encontrados con sus metadatos
        """
        query = query or config.GMAIL_QUERY
        max_results = max_results or config.MAX_EMAILS_PER_RUN
        
        logger.info(f"Buscando emails con query: '{query}'")
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results if max_results > 0 else None
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"✅ Encontrados {len(messages)} email(s)")
            
            return messages
        
        except HttpError as e:
            raise GoogleAPIError('Gmail', 'search_emails', str(e))
    
    @log_api_call(logger, "Gmail")
    def get_message_details(self, message_id: str) -> Dict:
        """
        Obtiene los detalles completos de un mensaje
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            Detalles completos del mensaje
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return message
        
        except HttpError as e:
            raise GoogleAPIError('Gmail', 'get_message_details', str(e))
    
    @log_api_call(logger, "Gmail")
    def download_attachment(self, message_id: str, output_dir: Path = None) -> Tuple[Path, str]:
        """
        Descarga el primer adjunto Excel (.xlsx) de un mensaje
        
        Args:
            message_id: ID del mensaje
            output_dir: Directorio donde guardar el adjunto (por defecto: temp/)
            
        Returns:
            Tupla con (ruta del archivo descargado, nombre original del archivo)
            
        Raises:
            AdjuntoNoEncontradoError: Si no se encuentra adjunto Excel
        """
        output_dir = output_dir or config.TEMP_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            message = self.get_message_details(message_id)
            
            # Buscar adjuntos en las partes del mensaje
            for part in message.get('payload', {}).get('parts', []):
                filename = part.get('filename', '')
                
                # Verificar si es un archivo Excel
                if filename.endswith('.xlsx'):
                    attachment_id = part['body'].get('attachmentId')
                    
                    if attachment_id:
                        # Descargar el adjunto
                        attachment = self.service.users().messages().attachments().get(
                            userId='me',
                            messageId=message_id,
                            id=attachment_id
                        ).execute()
                        
                        # Decodificar y guardar
                        file_data = base64.urlsafe_b64decode(attachment['data'])
                        file_path = output_dir / filename
                        
                        with open(file_path, 'wb') as f:
                            f.write(file_data)
                        
                        logger.info(f"✅ Adjunto descargado: {filename} ({len(file_data)} bytes)")
                        return file_path, filename
            
            # Si llegamos aquí, no se encontró adjunto Excel
            raise AdjuntoNoEncontradoError(message_id)
        
        except HttpError as e:
            raise GoogleAPIError('Gmail', 'download_attachment', str(e))
    
    @log_api_call(logger, "Gmail")
    def create_label(self, label_name: str) -> str:
        """
        Crea una etiqueta en Gmail si no existe
        
        Args:
            label_name: Nombre de la etiqueta (puede incluir / para subcarpetas)
            
        Returns:
            ID de la etiqueta creada o existente
        """
        try:
            # Primero buscar si ya existe
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            for label in labels:
                if label['name'] == label_name:
                    logger.debug(f"Etiqueta '{label_name}' ya existe")
                    return label['id']
            
            # Si no existe, crearla
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            logger.info(f"✅ Etiqueta '{label_name}' creada")
            return created_label['id']
        
        except HttpError as e:
            raise GoogleAPIError('Gmail', 'create_label', str(e))
    
    @log_api_call(logger, "Gmail")
    def add_label(self, message_id: str, label_name: str) -> None:
        """
        Agrega una etiqueta a un mensaje
        
        Args:
            message_id: ID del mensaje
            label_name: Nombre de la etiqueta
        """
        try:
            # Asegurar que la etiqueta existe
            label_id = self.create_label(label_name)
            
            # Agregar la etiqueta al mensaje
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            
            logger.info(f"✅ Etiqueta '{label_name}' agregada al mensaje {message_id}")
        
        except HttpError as e:
            raise GoogleAPIError('Gmail', 'add_label', str(e))
    
    @log_api_call(logger, "Gmail")
    def remove_label(self, message_id: str, label_name: str) -> None:
        """
        Remueve una etiqueta de un mensaje
        
        Args:
            message_id: ID del mensaje
            label_name: Nombre de la etiqueta
        """
        try:
            # Buscar ID de la etiqueta
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            label_id = None
            for label in labels:
                if label['name'] == label_name:
                    label_id = label['id']
                    break
            
            if label_id:
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'removeLabelIds': [label_id]}
                ).execute()
                
                logger.info(f"✅ Etiqueta '{label_name}' removida del mensaje {message_id}")
        
        except HttpError as e:
            raise GoogleAPIError('Gmail', 'remove_label', str(e))
    
    @log_api_call(logger, "Gmail")
    def mark_as_read(self, message_id: str) -> None:
        """
        Marca un mensaje como leído
        
        Args:
            message_id: ID del mensaje
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.debug(f"Mensaje {message_id} marcado como leído")
        
        except HttpError as e:
            raise GoogleAPIError('Gmail', 'mark_as_read', str(e))
    
    @log_api_call(logger, "Gmail")
    def send_email(self, to: str, subject: str, body_html: str, cc: str = None) -> None:
        """
        Envía un email con formato HTML
        
        Args:
            to: Destinatario
            subject: Asunto
            body_html: Cuerpo del mensaje en HTML
            cc: Copia (opcional)
        """
        try:
            message = MIMEText(body_html, 'html')
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"✅ Email enviado a {to}: {subject}")
        
        except HttpError as e:
            raise GoogleAPIError('Gmail', 'send_email', str(e))
    
    def send_success_notification(self, form_data: Dict) -> None:
        """
        Envía notificación de procesamiento exitoso
        
        Args:
            form_data: Datos del formulario procesado
        """
        template = config.EMAIL_TEMPLATES['success']
        
        body = template['body'].format(
            form_number=form_data.get('numero_formulario', 'N/A'),
            form_date=form_data.get('fecha', 'N/A'),
            requester=form_data.get('solicitante', 'N/A'),
            form_type=form_data.get('tipo_formulario', 'N/A'),
            items_count=len(form_data.get('items', []))
        )
        
        subject = template['subject'].format(
            form_number=form_data.get('numero_formulario', 'N/A')
        )
        
        self.send_email(config.NOTIFICATION_EMAIL, subject, body)
    
    def send_error_notification(self, error_message: str, file_name: str = "Desconocido") -> None:
        """
        Envía notificación de error en el procesamiento
        
        Args:
            error_message: Mensaje de error
            file_name: Nombre del archivo que causó el error
        """
        template = config.EMAIL_TEMPLATES['error']
        
        body = template['body'].format(
            error_message=error_message,
            file_name=file_name
        )
        
        self.send_email(config.NOTIFICATION_EMAIL, template['subject'], body)
    
    def send_duplicate_notification(self, form_data: Dict) -> None:
        """
        Envía notificación de formulario duplicado
        
        Args:
            form_data: Datos del formulario duplicado
        """
        template = config.EMAIL_TEMPLATES['duplicate']
        
        body = template['body'].format(
            form_number=form_data.get('numero_formulario', 'N/A'),
            requester=form_data.get('solicitante', 'N/A')
        )
        
        subject = template['subject'].format(
            form_number=form_data.get('numero_formulario', 'N/A')
        )
        
        self.send_email(config.NOTIFICATION_EMAIL, subject, body)



"""
R-60 Bot - Orquestador Principal
Automatiza el procesamiento de formularios R-60 desde Gmail a Google Sheets
"""

import sys
from pathlib import Path
from typing import Optional

import config
from src.utils.logger import logger
from src.utils.exceptions import (
    FormularioDuplicadoError,
    CampoObligatorioError,
    TipoFormularioNoReconocidoError,
    ArchivoExcelInvalidoError,
    AdjuntoNoEncontradoError,
    GoogleAPIError,
    CredencialesNoEncontradasError
)
from src.auth.google_auth import get_google_credentials
from src.services.gmail_service import GmailService
from src.services.sheets_service import SheetsService
from src.services.drive_service import DriveService
from src.parsers.excel_parser import parse_r60_form


class R60Bot:
    """Orquestador principal del bot de procesamiento R-60"""
    
    def __init__(self):
        """Inicializa el bot y sus servicios"""
        self.gmail_service: Optional[GmailService] = None
        self.sheets_service: Optional[SheetsService] = None
        self.drive_service: Optional[DriveService] = None
        self.processed_count = 0
        self.error_count = 0
        self.duplicate_count = 0
    
    def initialize_services(self) -> None:
        """
        Inicializa todos los servicios de Google
        
        Raises:
            CredencialesNoEncontradasError: Si no se encuentran las credenciales
        """
        logger.info("=" * 60)
        logger.info("Inicializando R-60 Bot")
        logger.info("=" * 60)
        
        # Validar configuración
        try:
            config.validate_config()
        except ValueError as e:
            logger.error(f"❌ Error de configuración: {e}")
            raise
        
        # Obtener credenciales de Google
        logger.info("Autenticando con Google...")
        credentials = get_google_credentials()
        
        # Inicializar servicios
        self.gmail_service = GmailService(credentials)
        self.sheets_service = SheetsService(credentials)
        self.drive_service = DriveService(credentials)
        
        # Asegurar que el encabezado de la planilla exista
        self.sheets_service.ensure_header_exists()
        
        logger.info("✅ Servicios inicializados correctamente")
    
    def process_emails(self) -> None:
        """
        Procesa todos los emails que coinciden con la query configurada
        """
        logger.info("\n" + "=" * 60)
        logger.info("Buscando emails para procesar")
        logger.info("=" * 60)
        
        # Buscar emails
        messages = self.gmail_service.search_emails()
        
        if not messages:
            logger.info("No hay emails para procesar")
            return
        
        logger.info(f"Se procesarán {len(messages)} email(s)")
        
        # Procesar cada email
        for i, message in enumerate(messages, 1):
            message_id = message['id']
            logger.info(f"\n--- Procesando email {i}/{len(messages)} (ID: {message_id}) ---")
            
            try:
                self._process_single_email(message_id)
                self.processed_count += 1
            
            except FormularioDuplicadoError as e:
                logger.warning(f"⚠️ Formulario duplicado: {e}")
                self._handle_duplicate(message_id, e)
                self.duplicate_count += 1
            
            except (CampoObligatorioError, TipoFormularioNoReconocidoError, 
                    ArchivoExcelInvalidoError, AdjuntoNoEncontradoError) as e:
                logger.error(f"❌ Error de validación: {e}")
                self._handle_error(message_id, str(e))
                self.error_count += 1
            
            except GoogleAPIError as e:
                logger.error(f"❌ Error de API de Google: {e}")
                self._handle_error(message_id, str(e))
                self.error_count += 1
            
            except Exception as e:
                logger.error(f"❌ Error inesperado: {e}", exc_info=True)
                self._handle_error(message_id, f"Error inesperado: {e}")
                self.error_count += 1
    
    def _process_single_email(self, message_id: str) -> None:
        """
        Procesa un solo email
        
        Args:
            message_id: ID del mensaje de Gmail
            
        Raises:
            Varias excepciones específicas del dominio
        """
        temp_file: Optional[Path] = None
        
        try:
            # 1. Descargar adjunto
            logger.info("Descargando adjunto...")
            temp_file, original_filename = self.gmail_service.download_attachment(message_id)
            
            # 2. Parsear formulario
            logger.info("Parseando formulario...")
            form_data = parse_r60_form(temp_file)
            
            # 3. Verificar duplicados y escribir en Sheets
            logger.info("Escribiendo en Google Sheets...")
            rows_added = self.sheets_service.append_rows(form_data)
            logger.info(f"✅ {rows_added} fila(s) agregada(s) a la planilla")
            
            # 4. Archivar en Drive
            logger.info("Archivando en Google Drive...")
            file_info = self.drive_service.archive_form(temp_file, form_data)
            logger.info(f"✅ Archivo archivado: {file_info['name']}")
            
            # Actualizar form_data con el enlace del archivo
            form_data['archivo_original'] = file_info.get('webViewLink', file_info['name'])
            
            # 5. Enviar notificación de éxito
            logger.info("Enviando notificación de éxito...")
            self.gmail_service.send_success_notification(form_data)
            
            # 6. Etiquetar email como procesado
            self.gmail_service.add_label(message_id, config.LABEL_PROCESSED)
            self.gmail_service.mark_as_read(message_id)
            
            logger.info(f"✅ Email procesado exitosamente: Formulario {form_data['numero_formulario']}")
        
        finally:
            # Limpiar archivo temporal
            if temp_file and temp_file.exists():
                temp_file.unlink()
                logger.debug(f"Archivo temporal eliminado: {temp_file}")
    
    def _handle_duplicate(self, message_id: str, error: FormularioDuplicadoError) -> None:
        """
        Maneja el caso de un formulario duplicado
        
        Args:
            message_id: ID del mensaje
            error: Excepción de duplicado
        """
        try:
            # Obtener detalles mínimos para la notificación
            message = self.gmail_service.get_message_details(message_id)
            
            form_data = {
                'numero_formulario': error.numero_formulario,
                'solicitante': 'Ver email original'
            }
            
            # Enviar notificación de duplicado
            self.gmail_service.send_duplicate_notification(form_data)
            
            # Etiquetar como duplicado
            self.gmail_service.add_label(message_id, config.LABEL_DUPLICATE)
            self.gmail_service.mark_as_read(message_id)
        
        except Exception as e:
            logger.error(f"Error al manejar duplicado: {e}")
    
    def _handle_error(self, message_id: str, error_message: str, file_name: str = "Desconocido") -> None:
        """
        Maneja errores en el procesamiento
        
        Args:
            message_id: ID del mensaje
            error_message: Mensaje de error
            file_name: Nombre del archivo (si está disponible)
        """
        try:
            # Enviar notificación de error
            self.gmail_service.send_error_notification(error_message, file_name)
            
            # Etiquetar como error
            self.gmail_service.add_label(message_id, config.LABEL_ERROR)
            self.gmail_service.mark_as_read(message_id)
        
        except Exception as e:
            logger.error(f"Error al manejar error: {e}")
    
    def print_summary(self) -> None:
        """Imprime un resumen de la ejecución"""
        logger.info("\n" + "=" * 60)
        logger.info("RESUMEN DE EJECUCIÓN")
        logger.info("=" * 60)
        logger.info(f"✅ Procesados exitosamente: {self.processed_count}")
        logger.info(f"⚠️  Duplicados: {self.duplicate_count}")
        logger.info(f"❌ Errores: {self.error_count}")
        logger.info(f"📊 Total: {self.processed_count + self.duplicate_count + self.error_count}")
        logger.info("=" * 60)
    
    def run(self) -> int:
        """
        Ejecuta el bot completo
        
        Returns:
            Código de salida (0 = éxito, 1 = error)
        """
        try:
            self.initialize_services()
            self.process_emails()
            self.print_summary()
            
            return 0 if self.error_count == 0 else 1
        
        except CredencialesNoEncontradasError as e:
            logger.error(f"\n❌ {e}")
            logger.info("\n📋 PASOS PARA OBTENER CREDENCIALES:")
            logger.info("1. Ve a https://console.cloud.google.com")
            logger.info("2. Crea un proyecto o selecciona uno existente")
            logger.info("3. Habilita las APIs: Gmail API, Google Sheets API, Google Drive API")
            logger.info("4. Ve a 'Credenciales' > 'Crear credenciales' > 'ID de cliente de OAuth'")
            logger.info("5. Tipo de aplicación: 'Aplicación de escritorio'")
            logger.info("6. Descarga el archivo JSON")
            logger.info(f"7. Guárdalo como: {config.CREDENTIALS_FILE}")
            logger.info("\nUna vez que tengas el archivo, vuelve a ejecutar el bot.")
            return 1
        
        except KeyboardInterrupt:
            logger.warning("\n⚠️ Ejecución interrumpida por el usuario")
            return 130
        
        except Exception as e:
            logger.critical(f"\n❌ Error crítico: {e}", exc_info=True)
            return 1


def main():
    """Punto de entrada principal"""
    bot = R60Bot()
    exit_code = bot.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()



"""
Servicio para interactuar con Google Sheets API
Encapsula todas las operaciones de Sheets: lectura, escritura y validaciones
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

import config
from src.utils.logger import logger, log_api_call
from src.utils.exceptions import GoogleAPIError, FormularioDuplicadoError


class SheetsService:
    """Servicio para gestionar operaciones con Google Sheets"""
    
    def __init__(self, credentials: Credentials):
        """
        Inicializa el servicio de Sheets
        
        Args:
            credentials: Credenciales de Google autenticadas
        """
        self.credentials = credentials
        self.service = build('sheets', 'v4', credentials=credentials)
        self.sheet_id = config.GOOGLE_SHEET_ID
        self.sheet_name = config.GOOGLE_SHEET_NAME
        logger.info("Sheets Service inicializado")
    
    @log_api_call(logger, "Sheets")
    def ensure_header_exists(self) -> None:
        """
        Verifica que el encabezado de la planilla exista, si no, lo crea
        """
        try:
            # Leer la primera fila
            range_name = f"{self.sheet_name}!A1:Z1"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Si está vacía o no coincide con el header esperado, crear/actualizar
            if not values or values[0] != config.SHEET_HEADERS:
                logger.info("Creando/actualizando encabezado de la planilla")
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f"{self.sheet_name}!A1",
                    valueInputOption='RAW',
                    body={'values': [config.SHEET_HEADERS]}
                ).execute()
                
                # Formatear encabezado (negrita)
                self._format_header()
                
                logger.info("✅ Encabezado creado/actualizado")
            else:
                logger.debug("Encabezado ya existe y es correcto")
        
        except HttpError as e:
            raise GoogleAPIError('Sheets', 'ensure_header_exists', str(e))
    
    @log_api_call(logger, "Sheets")
    def _format_header(self) -> None:
        """Aplica formato al encabezado (negrita, fondo gris)"""
        try:
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': self._get_sheet_id(),
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                                'textFormat': {'bold': True}
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': requests}
            ).execute()
            
        except HttpError as e:
            logger.warning(f"No se pudo formatear el encabezado: {e}")
    
    @log_api_call(logger, "Sheets")
    def _get_sheet_id(self) -> int:
        """Obtiene el ID interno de la hoja por su nombre"""
        try:
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()
            
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == self.sheet_name:
                    return sheet['properties']['sheetId']
            
            return 0  # Por defecto, la primera hoja
        
        except HttpError as e:
            raise GoogleAPIError('Sheets', '_get_sheet_id', str(e))
    
    @log_api_call(logger, "Sheets")
    def check_duplicate(self, form_number: str) -> bool:
        """
        Verifica si un número de formulario ya existe en la planilla
        
        Args:
            form_number: Número de formulario a verificar
            
        Returns:
            True si existe (es duplicado), False si no existe
        """
        try:
            # Leer la columna de números de formulario (columna B)
            range_name = f"{self.sheet_name}!B:B"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Buscar el número de formulario (ignorando el encabezado)
            for i, row in enumerate(values[1:], start=2):  # Empezar desde fila 2
                if row and str(row[0]).strip() == str(form_number).strip():
                    logger.warning(f"⚠️ Formulario {form_number} ya existe en fila {i}")
                    return True
            
            logger.debug(f"Formulario {form_number} no existe en la planilla")
            return False
        
        except HttpError as e:
            raise GoogleAPIError('Sheets', 'check_duplicate', str(e))
    
    @log_api_call(logger, "Sheets")
    def append_rows(self, form_data: Dict) -> int:
        """
        Agrega filas a la planilla (una por cada ítem del formulario)
        
        Args:
            form_data: Diccionario con los datos del formulario
            
        Returns:
            Número de filas agregadas
            
        Raises:
            FormularioDuplicadoError: Si el formulario ya existe
        """
        # Verificar duplicados
        if self.check_duplicate(form_data['numero_formulario']):
            raise FormularioDuplicadoError(form_data['numero_formulario'])
        
        # Preparar filas para insertar
        rows = self._prepare_rows(form_data)
        
        if not rows:
            logger.warning("No hay filas para insertar")
            return 0
        
        try:
            # Insertar filas
            range_name = f"{self.sheet_name}!A:A"
            body = {'values': rows}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updates = result.get('updates', {})
            rows_added = updates.get('updatedRows', 0)
            
            logger.info(f"✅ {rows_added} fila(s) agregada(s) a la planilla")
            return rows_added
        
        except HttpError as e:
            raise GoogleAPIError('Sheets', 'append_rows', str(e))
    
    def _prepare_rows(self, form_data: Dict) -> List[List[Any]]:
        """
        Prepara las filas para insertar en la planilla
        
        Args:
            form_data: Datos del formulario
            
        Returns:
            Lista de filas para insertar
        """
        rows = []
        fecha_procesamiento = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Datos comunes del encabezado
        common_data = {
            'fecha_procesamiento': fecha_procesamiento,
            'numero_formulario': form_data.get('numero_formulario', ''),
            'tipo_formulario': form_data.get('tipo_formulario', ''),
            'solicitante': form_data.get('solicitante', ''),
            'mail_solicitante': form_data.get('mail_solicitante', ''),
            'tel_solicitante': form_data.get('tel_solicitante', ''),
            'autorizado_por': form_data.get('autorizado_por', ''),
            'departamento': form_data.get('departamento', ''),
            'lugar_entrega': form_data.get('lugar_entrega', ''),
            'rubro': form_data.get('rubro', ''),
            'fecha_entrega': form_data.get('fecha_entrega', ''),
            'archivo_original': form_data.get('archivo_original', '')
        }
        
        # Crear una fila por cada ítem
        for item in form_data.get('items', []):
            # Estructura de la fila según SHEET_HEADERS en config.py:
            # 'Fecha Procesamiento', 'Nº Formulario', 'Tipo Formulario', 'Solicitante',
            # 'Mail Solicitante', 'Tel Solicitante', 'Autorizado Por', 'Departamento',
            # 'Lugar Entrega', 'Rubro', 'Fecha Entrega',
            # 'Código Polaris', 'Nº Item', 'Descripción', 'Cantidad', 'Unidad de Medida',
            # 'Fecha Entrega Item', 'Centro de Costo', 'Archivo Original'
            
            row = [
                common_data['fecha_procesamiento'],          # A: Fecha Procesamiento
                common_data['numero_formulario'],            # B: Nº Formulario
                common_data['tipo_formulario'],              # C: Tipo Formulario
                common_data['solicitante'],                  # D: Solicitante
                common_data['mail_solicitante'],             # E: Mail Solicitante
                common_data['tel_solicitante'],              # F: Tel Solicitante
                common_data['autorizado_por'],               # G: Autorizado Por
                common_data['departamento'],                 # H: Departamento
                common_data['lugar_entrega'],                # I: Lugar Entrega
                common_data['rubro'],                        # J: Rubro
                common_data['fecha_entrega'],                # K: Fecha Entrega
                item.get('codigo_polaris', ''),              # L: Código Polaris
                item.get('numero_item', ''),                 # M: Nº Item
                item.get('descripcion', ''),                 # N: Descripción
                item.get('cantidad', ''),                    # O: Cantidad
                item.get('unidad', ''),                      # P: Unidad de Medida
                item.get('fecha_entrega', ''),               # Q: Fecha Entrega Item
                item.get('centro_costo', ''),                # R: Centro de Costo
                common_data['archivo_original']              # S: Archivo Original
            ]
            rows.append(row)
        
        logger.debug(f"Preparadas {len(rows)} fila(s) para insertar")
        return rows
    
    @log_api_call(logger, "Sheets")
    def get_all_form_numbers(self) -> List[str]:
        """
        Obtiene todos los números de formulario existentes
        
        Returns:
            Lista de números de formulario
        """
        try:
            range_name = f"{self.sheet_name}!B:B"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Extraer números (ignorando encabezado)
            form_numbers = [row[0] for row in values[1:] if row]
            
            logger.debug(f"Encontrados {len(form_numbers)} formularios en la planilla")
            return form_numbers
        
        except HttpError as e:
            raise GoogleAPIError('Sheets', 'get_all_form_numbers', str(e))



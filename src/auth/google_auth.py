"""
Módulo de autenticación OAuth2 para Google APIs
Centraliza el flujo de autenticación para Gmail, Sheets y Drive
"""

import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import config
from src.utils.logger import logger, log_execution_time
from src.utils.exceptions import CredencialesNoEncontradasError


class GoogleAuthenticator:
    """Gestiona la autenticación OAuth2 con Google"""
    
    def __init__(self, scopes: list[str] = None):
        """
        Inicializa el autenticador
        
        Args:
            scopes: Lista de scopes de Google API. Si no se proporciona, usa los del config
        """
        self.scopes = scopes or config.GOOGLE_SCOPES
        self.credentials: Optional[Credentials] = None
    
    @log_execution_time(logger)
    def get_credentials(self) -> Credentials:
        """
        Obtiene las credenciales válidas de Google
        
        Flujo:
        1. Verifica si existe token.json válido
        2. Si existe pero expiró, intenta refrescarlo
        3. Si no existe, busca credentials.json e inicia flujo OAuth2
        4. Guarda el token resultante para futuros usos
        
        Returns:
            Credenciales válidas de Google
            
        Raises:
            CredencialesNoEncontradasError: Si no se encuentra credentials.json
        """
        # 1. Verificar si existe un token guardado
        if config.TOKEN_FILE.exists():
            logger.info(f"Token encontrado en {config.TOKEN_FILE}")
            self.credentials = Credentials.from_authorized_user_file(
                str(config.TOKEN_FILE), 
                self.scopes
            )
        
        # 2. Si no hay credenciales válidas, obtenerlas
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                # Token expirado pero se puede refrescar
                logger.info("Token expirado. Refrescando...")
                try:
                    self.credentials.refresh(Request())
                    logger.info("✅ Token refrescado exitosamente")
                except Exception as e:
                    logger.warning(f"No se pudo refrescar el token: {e}")
                    # Si falla el refresh, eliminar token y reautenticar
                    config.TOKEN_FILE.unlink(missing_ok=True)
                    self.credentials = None
            
            # Si aún no hay credenciales válidas, iniciar flujo OAuth2
            if not self.credentials or not self.credentials.valid:
                self.credentials = self._authenticate_new()
        
        logger.info("✅ Credenciales de Google obtenidas correctamente")
        return self.credentials
    
    def _authenticate_new(self) -> Credentials:
        """
        Inicia el flujo OAuth2 completo para obtener nuevas credenciales
        
        Returns:
            Credenciales nuevas de Google
            
        Raises:
            CredencialesNoEncontradasError: Si credentials.json no existe
        """
        # Verificar que exista credentials.json
        if not config.CREDENTIALS_FILE.exists():
            logger.error(f"Archivo de credenciales no encontrado: {config.CREDENTIALS_FILE}")
            raise CredencialesNoEncontradasError(str(config.CREDENTIALS_FILE))
        
        logger.info("Iniciando flujo de autenticación OAuth2...")
        logger.info("Se abrirá tu navegador para autorizar la aplicación")
        
        # Iniciar flujo OAuth2
        flow = InstalledAppFlow.from_client_secrets_file(
            str(config.CREDENTIALS_FILE),
            self.scopes
        )
        
        # Ejecutar servidor local para callback
        credentials = flow.run_local_server(
            port=8080,
            prompt='consent',
            success_message='¡Autenticación exitosa! Puedes cerrar esta ventana.'
        )
        
        # Guardar token para futuros usos
        self._save_token(credentials)
        
        logger.info("✅ Autenticación completada y token guardado")
        return credentials
    
    def _save_token(self, credentials: Credentials) -> None:
        """
        Guarda el token de autenticación en un archivo
        
        Args:
            credentials: Credenciales a guardar
        """
        # Asegurar que exista el directorio
        config.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Guardar token
        with open(config.TOKEN_FILE, 'w') as token_file:
            token_file.write(credentials.to_json())
        
        logger.debug(f"Token guardado en {config.TOKEN_FILE}")
    
    @staticmethod
    def revoke_credentials() -> None:
        """
        Revoca y elimina las credenciales guardadas
        Útil para debugging o cambio de cuenta
        """
        if config.TOKEN_FILE.exists():
            config.TOKEN_FILE.unlink()
            logger.info("Token eliminado. Se requerirá nueva autenticación.")
        else:
            logger.info("No hay token para eliminar.")


def get_google_credentials(scopes: list[str] = None) -> Credentials:
    """
    Función de conveniencia para obtener credenciales de Google
    
    Args:
        scopes: Lista de scopes necesarios
        
    Returns:
        Credenciales válidas de Google
    """
    authenticator = GoogleAuthenticator(scopes)
    return authenticator.get_credentials()


if __name__ == "__main__":
    # Test del módulo de autenticación
    print("🔐 Probando autenticación con Google...")
    print(f"Buscando credenciales en: {config.CREDENTIALS_FILE}")
    print(f"Token se guardará en: {config.TOKEN_FILE}")
    print("-" * 60)
    
    try:
        creds = get_google_credentials()
        print("\n✅ Autenticación exitosa!")
        print(f"Scopes autorizados: {creds.scopes}")
    except CredencialesNoEncontradasError as e:
        print(f"\n❌ {e}")
        print("\n📋 Pasos para obtener credentials.json:")
        print("1. Ve a https://console.cloud.google.com")
        print("2. Crea un proyecto o selecciona uno existente")
        print("3. Habilita las APIs: Gmail, Sheets, Drive")
        print("4. Ve a 'Credenciales' > 'Crear credenciales' > 'ID de cliente de OAuth'")
        print("5. Tipo: 'Aplicación de escritorio'")
        print("6. Descarga el JSON y guárdalo como 'credentials.json'")
        print(f"7. Colócalo en: {config.CREDENTIALS_DIR}/")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")



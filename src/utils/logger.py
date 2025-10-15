"""
Sistema de logging centralizado para el R-60 Bot
Configura logging robusto con rotación de archivos y formato estructurado
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

import colorlog

import config


class Logger:
    """Clase para gestionar el logging del sistema"""
    
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = "R60Bot") -> logging.Logger:
        """
        Obtiene o crea una instancia del logger
        
        Args:
            name: Nombre del logger
            
        Returns:
            Instancia configurada del logger
        """
        if cls._instance is None:
            cls._instance = cls._setup_logger(name)
        return cls._instance
    
    @classmethod
    def _setup_logger(cls, name: str) -> logging.Logger:
        """
        Configura el logger con handlers para consola y archivo
        
        Args:
            name: Nombre del logger
            
        Returns:
            Logger configurado
        """
        logger = logging.getLogger(name)
        
        # Nivel de logging desde configuración
        log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Evitar duplicación de logs
        if logger.handlers:
            return logger
        
        # Formato para archivos (más detallado)
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Formato para consola (con colores)
        console_formatter = colorlog.ColoredFormatter(
            fmt='%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Handler para archivo con rotación
        log_file = config.LOGS_DIR / f"r60bot_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=30,  # Mantener 30 archivos de respaldo
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Archivo siempre guarda DEBUG
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger


def log_execution_time(logger: logging.Logger):
    """
    Decorador para registrar el tiempo de ejecución de funciones
    
    Args:
        logger: Instancia del logger
        
    Returns:
        Función decoradora
    """
    from functools import wraps
    from time import time
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time()
            logger.debug(f"Iniciando {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                elapsed = time() - start_time
                logger.debug(f"{func.__name__} completado en {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time() - start_time
                logger.error(f"{func.__name__} falló después de {elapsed:.2f}s: {e}")
                raise
        
        return wrapper
    return decorator


def log_api_call(logger: logging.Logger, service: str):
    """
    Decorador específico para registrar llamadas a APIs
    
    Args:
        logger: Instancia del logger
        service: Nombre del servicio (Gmail, Sheets, Drive)
        
    Returns:
        Función decoradora
    """
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"[{service}] Llamando a {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"[{service}] {func.__name__} completado exitosamente")
                return result
            except Exception as e:
                logger.error(f"[{service}] Error en {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


# Instancia global del logger para uso directo
logger = Logger.get_logger()


if __name__ == "__main__":
    # Test del sistema de logging
    test_logger = Logger.get_logger("TestLogger")
    
    test_logger.debug("Este es un mensaje de DEBUG")
    test_logger.info("Este es un mensaje de INFO")
    test_logger.warning("Este es un mensaje de WARNING")
    test_logger.error("Este es un mensaje de ERROR")
    test_logger.critical("Este es un mensaje de CRITICAL")
    
    print(f"\n✅ Log guardado en: {config.LOGS_DIR}")



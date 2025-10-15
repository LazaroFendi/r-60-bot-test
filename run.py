#!/usr/bin/env python3
"""
Script helper para ejecutar y gestionar el R-60 Bot
Proporciona comandos útiles para desarrollo y producción
"""

import sys
import argparse
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

import config
from src.utils.logger import logger


def check_setup():
    """Verifica que el setup esté completo"""
    print("🔍 Verificando configuración del R-60 Bot...\n")
    
    issues = []
    warnings = []
    
    # 1. Verificar archivo .env
    env_file = Path('.env')
    if not env_file.exists():
        issues.append("❌ Archivo .env no encontrado. Copia env.example a .env")
    else:
        print("✅ Archivo .env encontrado")
    
    # 2. Verificar credentials.json
    if not config.CREDENTIALS_FILE.exists():
        issues.append(f"❌ credentials.json no encontrado en {config.CREDENTIALS_FILE}")
    else:
        print("✅ credentials.json encontrado")
    
    # 3. Verificar token.json
    if not config.TOKEN_FILE.exists():
        warnings.append(f"⚠️  token.json no encontrado (se generará en la primera ejecución)")
    else:
        print("✅ token.json encontrado")
    
    # 4. Verificar variables de entorno
    try:
        config.validate_config()
        print("✅ Variables de entorno configuradas correctamente")
    except ValueError as e:
        issues.append(f"❌ {e}")
    
    # 5. Verificar carpetas
    for folder in [config.TEMP_DIR, config.LOGS_DIR, config.CREDENTIALS_DIR]:
        if folder.exists():
            print(f"✅ Carpeta {folder.name}/ existe")
        else:
            warnings.append(f"⚠️  Carpeta {folder} no existe (se creará automáticamente)")
    
    # Resumen
    print("\n" + "=" * 60)
    if issues:
        print("🔴 PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"  {issue}")
    
    if warnings:
        print("\n🟡 ADVERTENCIAS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not issues and not warnings:
        print("🎉 ¡Todo está configurado correctamente!")
    elif not issues:
        print("\n✅ Configuración básica completa (advertencias pueden ignorarse)")
    
    print("=" * 60)
    
    return len(issues) == 0


def run_bot():
    """Ejecuta el bot principal"""
    print("🚀 Iniciando R-60 Bot...\n")
    
    from main import main
    main()


def test_auth():
    """Prueba solo la autenticación"""
    print("🔐 Probando autenticación con Google...\n")
    
    try:
        from src.auth.google_auth import get_google_credentials
        
        creds = get_google_credentials()
        print("\n✅ Autenticación exitosa!")
        print(f"Scopes: {', '.join(creds.scopes)}")
        
        if config.TOKEN_FILE.exists():
            print(f"Token guardado en: {config.TOKEN_FILE}")
    
    except Exception as e:
        print(f"\n❌ Error en autenticación: {e}")
        return False
    
    return True


def test_parser(file_path: str):
    """Prueba el parser con un archivo específico"""
    from src.parsers.excel_parser import parse_r60_form
    
    test_file = Path(file_path)
    
    if not test_file.exists():
        print(f"❌ Archivo no encontrado: {test_file}")
        return False
    
    print(f"📊 Parseando archivo: {test_file.name}\n")
    
    try:
        result = parse_r60_form(test_file)
        
        print("✅ Formulario parseado exitosamente!\n")
        print(f"Tipo: {result['tipo_formulario']}")
        print(f"Número: {result['numero_formulario']}")
        print(f"Fecha: {result['fecha']}")
        print(f"Solicitante: {result['solicitante']}")
        print(f"Área: {result['area']}")
        print(f"Ítems: {len(result['items'])}")
        
        print("\nPrimeros 3 ítems:")
        for i, item in enumerate(result['items'][:3], 1):
            print(f"  {i}. Nº {item['numero_item']}: {item['campo1']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error al parsear: {e}")
        import traceback
        traceback.print_exc()
        return False


def revoke_auth():
    """Revoca la autenticación (elimina token.json)"""
    print("🔓 Revocando autenticación...\n")
    
    from src.auth.google_auth import GoogleAuthenticator
    
    GoogleAuthenticator.revoke_credentials()
    print("✅ Token eliminado. Se requerirá nueva autenticación en la próxima ejecución.")


def show_info():
    """Muestra información del sistema"""
    import platform
    
    print("📋 Información del Sistema R-60 Bot\n")
    print("=" * 60)
    print(f"Python: {platform.python_version()}")
    print(f"SO: {platform.system()} {platform.release()}")
    print(f"Directorio: {Path.cwd()}")
    print(f"\nSheet ID: {config.GOOGLE_SHEET_ID[:20]}..." if config.GOOGLE_SHEET_ID else "No configurado")
    print(f"Drive Folder ID: {config.GOOGLE_DRIVE_FOLDER_ID[:20]}..." if config.GOOGLE_DRIVE_FOLDER_ID else "No configurado")
    print(f"Email notificaciones: {config.NOTIFICATION_EMAIL}")
    print(f"Query Gmail: {config.GMAIL_QUERY}")
    print(f"Nivel de log: {config.LOG_LEVEL}")
    print(f"Max emails/ejecución: {config.MAX_EMAILS_PER_RUN}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='R-60 Bot - Sistema de automatización de formularios',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos de uso:
  python run.py check          # Verificar configuración
  python run.py run            # Ejecutar el bot
  python run.py test-auth      # Probar autenticación
  python run.py test-parser archivo.xlsx  # Probar parser
  python run.py info           # Ver información del sistema
  python run.py revoke         # Revocar autenticación
        '''
    )
    
    parser.add_argument(
        'command',
        choices=['check', 'run', 'test-auth', 'test-parser', 'revoke', 'info'],
        help='Comando a ejecutar'
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        help='Archivo para test-parser'
    )
    
    args = parser.parse_args()
    
    # Ejecutar comando
    if args.command == 'check':
        success = check_setup()
        sys.exit(0 if success else 1)
    
    elif args.command == 'run':
        run_bot()
    
    elif args.command == 'test-auth':
        success = test_auth()
        sys.exit(0 if success else 1)
    
    elif args.command == 'test-parser':
        if not args.file:
            print("❌ Error: Debes especificar un archivo para parsear")
            print("Uso: python run.py test-parser <archivo.xlsx>")
            sys.exit(1)
        success = test_parser(args.file)
        sys.exit(0 if success else 1)
    
    elif args.command == 'revoke':
        revoke_auth()
    
    elif args.command == 'info':
        show_info()


if __name__ == '__main__':
    main()



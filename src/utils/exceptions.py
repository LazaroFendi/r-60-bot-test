"""
Excepciones personalizadas para el R-60 Bot
Define errores específicos del dominio para mejor manejo y claridad
"""


class R60BotError(Exception):
    """Clase base para todas las excepciones del R-60 Bot"""
    pass


class FormularioDuplicadoError(R60BotError):
    """Se lanza cuando se intenta procesar un formulario que ya existe en la planilla"""
    
    def __init__(self, numero_formulario: str):
        self.numero_formulario = numero_formulario
        super().__init__(
            f"El formulario Nº {numero_formulario} ya ha sido procesado anteriormente. "
            f"No se permiten duplicados."
        )


class CampoObligatorioError(R60BotError):
    """Se lanza cuando falta un campo obligatorio en el formulario"""
    
    def __init__(self, campo: str, celda: str = None):
        self.campo = campo
        self.celda = celda
        mensaje = f"Campo obligatorio '{campo}' está vacío o no encontrado"
        if celda:
            mensaje += f" (celda {celda})"
        super().__init__(mensaje)


class TipoFormularioNoReconocidoError(R60BotError):
    """Se lanza cuando no se puede identificar el tipo de formulario R-60"""
    
    def __init__(self, archivo: str):
        self.archivo = archivo
        super().__init__(
            f"No se pudo identificar el tipo de formulario R-60 en el archivo: {archivo}. "
            f"Tipos esperados: COMPRAS, SERVICIOS, COSTOS"
        )


class ArchivoExcelInvalidoError(R60BotError):
    """Se lanza cuando el archivo Excel está corrupto o no tiene el formato esperado"""
    
    def __init__(self, archivo: str, detalle: str = ""):
        self.archivo = archivo
        mensaje = f"El archivo Excel '{archivo}' es inválido o está corrupto"
        if detalle:
            mensaje += f": {detalle}"
        super().__init__(mensaje)


class GoogleAPIError(R60BotError):
    """Se lanza cuando hay un error en la comunicación con las APIs de Google"""
    
    def __init__(self, servicio: str, operacion: str, detalle: str = ""):
        self.servicio = servicio
        self.operacion = operacion
        mensaje = f"Error en {servicio} al realizar '{operacion}'"
        if detalle:
            mensaje += f": {detalle}"
        super().__init__(mensaje)


class CredencialesNoEncontradasError(R60BotError):
    """Se lanza cuando no se encuentran las credenciales de Google"""
    
    def __init__(self, archivo_esperado: str):
        self.archivo_esperado = archivo_esperado
        super().__init__(
            f"No se encontró el archivo de credenciales: {archivo_esperado}\n"
            f"Por favor, descarga las credenciales de Google Cloud Console y colócalas en la ruta indicada."
        )


class AdjuntoNoEncontradoError(R60BotError):
    """Se lanza cuando un email no contiene el adjunto esperado"""
    
    def __init__(self, message_id: str):
        self.message_id = message_id
        super().__init__(
            f"No se encontró adjunto Excel (.xlsx) en el email con ID: {message_id}"
        )


class ItemsVaciosError(R60BotError):
    """Se lanza cuando un formulario no contiene ítems para procesar"""
    
    def __init__(self, numero_formulario: str):
        self.numero_formulario = numero_formulario
        super().__init__(
            f"El formulario Nº {numero_formulario} no contiene ítems para procesar. "
            f"Verifica que la tabla de ítems tenga datos."
        )



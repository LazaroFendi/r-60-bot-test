"""
Tests unitarios para el parser de formularios R-60
Ejemplo básico para expandir la suite de tests
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.parsers.excel_parser import ExcelParser
from src.utils.exceptions import (
    ArchivoExcelInvalidoError,
    TipoFormularioNoReconocidoError,
    CampoObligatorioError
)


class TestExcelParser(unittest.TestCase):
    """Tests para el parser de formularios R-60"""
    
    def setUp(self):
        """Configuración antes de cada test"""
        self.test_file = Path("test_formulario.xlsx")
    
    def test_parser_initialization(self):
        """Test: El parser se inicializa correctamente"""
        parser = ExcelParser(self.test_file)
        
        self.assertEqual(parser.file_path, self.test_file)
        self.assertIsNone(parser.workbook)
        self.assertIsNone(parser.sheet)
        self.assertIsNone(parser.form_type)
    
    @patch('src.parsers.excel_parser.openpyxl.load_workbook')
    def test_load_workbook_invalid_file(self, mock_load):
        """Test: Manejo de archivo Excel inválido"""
        mock_load.side_effect = Exception("Archivo corrupto")
        
        parser = ExcelParser(self.test_file)
        
        with self.assertRaises(ArchivoExcelInvalidoError):
            parser._load_workbook()
    
    def test_identify_form_type_by_sheet_name(self):
        """Test: Identificación de tipo por nombre de hoja"""
        parser = ExcelParser(self.test_file)
        
        # Mock del workbook y sheet
        mock_sheet = MagicMock()
        mock_sheet.title = "Formulario de Compras 2024"
        mock_sheet.iter_rows.return_value = []
        
        parser.sheet = mock_sheet
        
        form_type = parser._identify_form_type()
        self.assertEqual(form_type, "COMPRAS")
    
    def test_identify_form_type_servicios(self):
        """Test: Identificación de tipo SERVICIOS"""
        parser = ExcelParser(self.test_file)
        
        mock_sheet = MagicMock()
        mock_sheet.title = "Servicios Contratados"
        mock_sheet.iter_rows.return_value = []
        
        parser.sheet = mock_sheet
        
        form_type = parser._identify_form_type()
        self.assertEqual(form_type, "SERVICIOS")
    
    def test_identify_form_type_not_recognized(self):
        """Test: Error cuando no se reconoce el tipo"""
        parser = ExcelParser(self.test_file)
        
        mock_sheet = MagicMock()
        mock_sheet.title = "Formulario Desconocido"
        mock_sheet.iter_rows.return_value = [(None, None, None)]
        
        parser.sheet = mock_sheet
        
        with self.assertRaises(TipoFormularioNoReconocidoError):
            parser._identify_form_type()
    
    def test_extract_header_data_missing_required_field(self):
        """Test: Error cuando falta un campo obligatorio"""
        parser = ExcelParser(self.test_file)
        parser.form_type = "COMPRAS"
        
        # Mock del sheet con campo obligatorio vacío
        mock_sheet = MagicMock()
        mock_sheet.__getitem__ = Mock(return_value=Mock(value=None))
        
        parser.sheet = mock_sheet
        
        with self.assertRaises(CampoObligatorioError):
            parser._extract_header_data()
    
    def test_get_cell_value_formats(self):
        """Test: Formateo correcto de valores de celdas"""
        from datetime import datetime
        
        parser = ExcelParser(self.test_file)
        
        # Mock del sheet
        mock_sheet = MagicMock()
        parser.sheet = mock_sheet
        
        # Test: Valor None
        mock_sheet.__getitem__ = Mock(return_value=Mock(value=None))
        self.assertEqual(parser._get_cell_value("A1"), "")
        
        # Test: Fecha
        test_date = datetime(2024, 1, 15)
        mock_sheet.__getitem__ = Mock(return_value=Mock(value=test_date))
        self.assertEqual(parser._get_cell_value("A1"), "2024-01-15")
        
        # Test: Número
        mock_sheet.__getitem__ = Mock(return_value=Mock(value=123.45))
        self.assertEqual(parser._get_cell_value("A1"), 123.45)
        
        # Test: Texto
        mock_sheet.__getitem__ = Mock(return_value=Mock(value="  Texto  "))
        self.assertEqual(parser._get_cell_value("A1"), "Texto")


class TestExcelParserIntegration(unittest.TestCase):
    """Tests de integración para el parser (requieren archivos reales)"""
    
    @unittest.skip("Requiere archivo Excel de prueba")
    def test_parse_real_compras_form(self):
        """Test: Parseo completo de formulario de COMPRAS real"""
        test_file = Path("tests/fixtures/formulario_compras.xlsx")
        
        if not test_file.exists():
            self.skipTest("Archivo de prueba no encontrado")
        
        parser = ExcelParser(test_file)
        result = parser.parse()
        
        self.assertEqual(result['tipo_formulario'], 'COMPRAS')
        self.assertIn('numero_formulario', result)
        self.assertIn('items', result)
        self.assertGreater(len(result['items']), 0)
    
    @unittest.skip("Requiere archivo Excel de prueba")
    def test_parse_real_servicios_form(self):
        """Test: Parseo completo de formulario de SERVICIOS real"""
        test_file = Path("tests/fixtures/formulario_servicios.xlsx")
        
        if not test_file.exists():
            self.skipTest("Archivo de prueba no encontrado")
        
        parser = ExcelParser(test_file)
        result = parser.parse()
        
        self.assertEqual(result['tipo_formulario'], 'SERVICIOS')


if __name__ == '__main__':
    unittest.main()



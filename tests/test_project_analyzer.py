"""
Tests for the ProjectAnalyzer class.
"""

import unittest
from unittest.mock import MagicMock, patch
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer
from qgis_ai_assistant.project_analyzer import ProjectAnalyzer


class TestProjectAnalyzer(unittest.TestCase):
    """Test cases for ProjectAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock QGIS interface
        self.mock_iface = MagicMock()
        
        # Create analyzer
        self.analyzer = ProjectAnalyzer(self.mock_iface)
        
        # Mock project
        self.mock_project = MagicMock(spec=QgsProject)
        self.analyzer.project = self.mock_project
    
    @patch('qgis_ai_assistant.project_analyzer.QgsProject')
    def test_init(self, mock_qgs_project):
        """Test initialization."""
        mock_qgs_project.instance.return_value = MagicMock()
        
        analyzer = ProjectAnalyzer(self.mock_iface)
        self.assertIsNotNone(analyzer)
        self.assertEqual(analyzer.iface, self.mock_iface)
    
    def test_get_project_name(self):
        """Test getting project name."""
        self.mock_project.baseName.return_value = "test_project"
        name = self.analyzer._get_project_name()
        self.assertEqual(name, "test_project")
    
    def test_get_project_name_error(self):
        """Test getting project name with error."""
        self.mock_project.baseName.side_effect = Exception("Error")
        name = self.analyzer._get_project_name()
        self.assertEqual(name, "Unknown")
    
    def test_get_project_path(self):
        """Test getting project path."""
        self.mock_project.fileName.return_value = "/path/to/project.qgz"
        path = self.analyzer._get_project_path()
        self.assertEqual(path, "/path/to/project.qgz")
    
    def test_get_project_path_not_saved(self):
        """Test getting project path when not saved."""
        self.mock_project.fileName.return_value = ""
        path = self.analyzer._get_project_path()
        self.assertEqual(path, "Not saved")
    
    def test_get_layer_type_vector(self):
        """Test getting layer type for vector layer."""
        mock_layer = MagicMock(spec=QgsVectorLayer)
        mock_layer.geometryType.return_value = 0  # Point
        
        layer_type = self.analyzer._get_layer_type(mock_layer)
        self.assertEqual(layer_type, "vector (point)")
    
    def test_get_layer_type_raster(self):
        """Test getting layer type for raster layer."""
        mock_layer = MagicMock(spec=QgsRasterLayer)
        
        layer_type = self.analyzer._get_layer_type(mock_layer)
        self.assertEqual(layer_type, "raster")
    
    def test_get_field_type(self):
        """Test getting field type."""
        from qgis.core import QgsField
        
        field = QgsField("test_field", QgsField.String)
        field_type = self.analyzer._get_field_type(field)
        self.assertEqual(field_type, "string")
    
    def test_get_field_type_integer(self):
        """Test getting field type for integer."""
        from qgis.core import QgsField
        
        field = QgsField("test_int", QgsField.Integer)
        field_type = self.analyzer._get_field_type(field)
        self.assertEqual(field_type, "integer")


if __name__ == '__main__':
    unittest.main()

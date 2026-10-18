"""
Analyseur de projet pour l'Assistant IA QGIS.

Ce module fournit des fonctionnalités pour analyser les projets QGIS et extraire
des informations pertinentes pour l'assistant IA.
"""

from qgis.core import (
    QgsProject, QgsMapLayer, QgsVectorLayer, 
    QgsRasterLayer, QgsWkbTypes, QgsCoordinateReferenceSystem,
    QgsRectangle, QgsFeature, QgsField
)
from qgis.PyQt.QtCore import QCoreApplication


class ProjectAnalyzer:
    """
    Analyseur pour les projets QGIS.
    
    Fournit des méthodes pour extraire et analyser des informations à partir du
    projet QGIS actuel, y compris les couches, les entités, les étendues et les métadonnées.
    """
    
    def __init__(self, iface):
        """
        Initialiser l'analyseur de projet.
        
        Args:
            iface: L'instance de l'interface QGIS.
        """
        self.iface = iface
        self.project = QgsProject.instance()
    
    def analyze_project(self):
        """
        Analyser le projet QGIS actuel.
        
        Returns:
            Dictionnaire avec les informations d'analyse du projet.
        """
        analysis = {
            'project_name': self._get_project_name(),
            'project_path': self._get_project_path(),
            'crs': self._get_project_crs(),
            'layers': self._analyze_layers(),
            'extent': self._get_project_extent(),
            'layer_count': len(self.project.mapLayers()),
            'vector_layer_count': 0,
            'raster_layer_count': 0,
            'feature_counts': {},
            'field_info': {},
            'summary': self._generate_summary()
        }
        
        # Compter les types de couches
        for layer_info in analysis['layers']:
            if layer_info['type'] == 'vector':
                analysis['vector_layer_count'] += 1
            elif layer_info['type'] == 'raster':
                analysis['raster_layer_count'] += 1
        
        return analysis
    
    def _get_project_name(self):
        """Obtenir le nom du projet."""
        try:
            return self.project.baseName()
        except Exception:
            return "Inconnu"
    
    def _get_project_path(self):
        """Obtenir le chemin du fichier du projet."""
        try:
            path = self.project.fileName()
            return path if path else "Non enregistré"
        except Exception:
            return "Non enregistré"
    
    def _get_project_crs(self):
        """Obtenir le système de coordonnées de référence du projet."""
        try:
            crs = self.project.crs()
            if crs.isValid():
                return f"{crs.authid()} - {crs.description()}"
            else:
                return "SCR invalide"
        except Exception:
            return "Inconnu"
    
    def _analyze_layers(self):
        """
        Analyser toutes les couches dans le projet.
        
        Returns:
            Liste de dictionnaires avec les informations des couches.
        """
        layers = []
        
        # Obtenir toutes les couches de la carte
        map_layers = self.project.mapLayers()
        
        for layer_id, layer in map_layers.items():
            layer_info = self._analyze_layer(layer)
            layers.append(layer_info)
        
        return layers
    
    def _analyze_layer(self, layer):
        """
        Analyser une seule couche.
        
        Args:
            layer: La couche QGIS à analyser.
        
        Returns:
            Dictionnaire avec les informations de la couche.
        """
        layer_info = {
            'id': layer.id(),
            'name': layer.name(),
            'type': self._get_layer_type(layer),
            'crs': self._get_layer_crs(layer),
            'visible': layer.isVisible(),
            'opacity': layer.opacity(),
            'feature_count': 0,
            'fields': [],
            'extent': self._get_layer_extent(layer),
            'source': self._get_layer_source(layer),
            'info': ''
        }
        
        # Obtenir des informations supplémentaires en fonction du type de couche
        if layer_info['type'] == 'vector':
            self._analyze_vector_layer(layer, layer_info)
        elif layer_info['type'] == 'raster':
            self._analyze_raster_layer(layer, layer_info)
        
        # Ajouter le nombre d'entités aux infos
        layer_info['info'] = f"{layer_info['feature_count']} entités" if layer_info['type'] == 'vector' else ""
        
        return layer_info
    
    def _get_layer_type(self, layer):
        """Obtenir le type de couche."""
        if isinstance(layer, QgsVectorLayer):
            # Déterminer le type de géométrie
            geom_type = QgsWkbTypes.geometryType(layer.geometryType())
            if geom_type == QgsWkbTypes.PointGeometry:
                return "vector (point)"
            elif geom_type == QgsWkbTypes.LineGeometry:
                return "vector (ligne)"
            elif geom_type == QgsWkbTypes.PolygonGeometry:
                return "vector (polygone)"
            else:
                return "vector"
        elif isinstance(layer, QgsRasterLayer):
            return "raster"
        else:
            return "autre"
    
    def _get_layer_crs(self, layer):
        """Obtenir le système de coordonnées de référence de la couche."""
        try:
            crs = layer.crs()
            if crs.isValid():
                return f"{crs.authid()}"
            else:
                return "Invalide"
        except Exception:
            return "Inconnu"
    
    def _get_layer_extent(self, layer):
        """Obtenir l'étendue de la couche."""
        try:
            extent = layer.extent()
            if extent.isEmpty():
                return {}
            
            return {
                'x_min': extent.xMinimum(),
                'x_max': extent.xMaximum(),
                'y_min': extent.yMinimum(),
                'y_max': extent.yMaximum()
            }
        except Exception:
            return {}
    
    def _get_layer_source(self, layer):
        """Obtenir la source de la couche."""
        try:
            return layer.source()
        except Exception:
            return "Inconnu"
    
    def _analyze_vector_layer(self, layer, layer_info):
        """
        Analyser une couche vectorielle.
        
        Args:
            layer: La couche vectorielle à analyser.
            layer_info: Dictionnaire à mettre à jour avec les informations de la couche.
        """
        try:
            # Obtenir le nombre d'entités
            layer_info['feature_count'] = layer.featureCount()
            
            # Obtenir les champs
            fields = layer.fields()
            field_info = []
            
            for i in range(fields.count()):
                field = fields.field(i)
                field_info.append({
                    'name': field.name(),
                    'type': self._get_field_type(field),
                    'length': field.length(),
                    'precision': field.precision()
                })
            
            layer_info['fields'] = field_info
            
        except Exception as e:
            self._log_error(f"Erreur lors de l'analyse de la couche vectorielle {layer.name()}: {str(e)}")
    
    def _analyze_raster_layer(self, layer, layer_info):
        """
        Analyser une couche raster.
        
        Args:
            layer: La couche raster à analyser.
            layer_info: Dictionnaire à mettre à jour avec les informations de la couche.
        """
        try:
            # Obtenir les propriétés raster
            provider = layer.dataProvider()
            if provider:
                # Obtenir le nombre de bandes
                band_count = provider.bandCount()
                layer_info['bands'] = band_count
                
                # Obtenir les dimensions du raster
                x_size = provider.xSize()
                y_size = provider.ySize()
                layer_info['dimensions'] = {'width': x_size, 'height': y_size}
                
                # Mettre à jour la chaîne d'info
                layer_info['info'] = f"{x_size}x{y_size}, {band_count} bandes"
        
        except Exception as e:
            self._log_error(f"Erreur lors de l'analyse de la couche raster {layer.name()}: {str(e)}")
    
    def _get_field_type(self, field):
        """Obtenir le type de champ sous forme de chaîne."""
        type_map = {
            QgsField.Numeric: "numérique",
            QgsField.Integer: "entier",
            QgsField.Double: "décimal",
            QgsField.String: "texte",
            QgsField.Date: "date",
            QgsField.Time: "heure",
            QgsField.DateTime: "date_heure",
            QgsField.Boolean: "booléen",
            QgsField.Binary: "binaire"
        }
        
        return type_map.get(field.type(), "inconnu")
    
    def _get_project_extent(self):
        """Obtenir l'étendue du projet."""
        try:
            # Dans QGIS 4.x, viewSettings() peut ne pas être directement disponible sur le projet
            # Essayons différentes approches
            extent = None
            
            # Approche 1 : Essayons viewSettings (QGIS 3.x et certaines versions 4.x)
            if hasattr(self.project, 'viewSettings'):
                view_settings = self.project.viewSettings()
                if hasattr(view_settings, 'fullExtent'):
                    extent = view_settings.fullExtent()
            
            # Approche 2 : Essayons layer tree root (QGIS 4.x)
            if extent is None or extent.isEmpty():
                layer_tree_root = self.project.layerTreeRoot()
                if hasattr(layer_tree_root, 'extent'):
                    extent = layer_tree_root.extent()
            
            # Approche 3 : Calculer à partir de toutes les couches
            if extent is None or extent.isEmpty():
                all_layers_extent = QgsRectangle()
                for layer in self.project.mapLayers().values():
                    if layer.isValid():
                        layer_extent = layer.extent()
                        if not layer_extent.isEmpty():
                            all_layers_extent.combineExtentWith(layer_extent)
                
                if not all_layers_extent.isEmpty():
                    extent = all_layers_extent
            
            # Si toujours vide, retourner un dict vide
            if extent is None or extent.isEmpty():
                return {}
            
            return {
                'x_min': extent.xMinimum(),
                'x_max': extent.xMaximum(),
                'y_min': extent.yMinimum(),
                'y_max': extent.yMaximum()
            }
        except Exception:
            return {}
    
    def _generate_summary(self):
        """Générer un résumé du projet."""
        try:
            layer_count = len(self.project.mapLayers())
            vector_count = 0
            raster_count = 0
            total_features = 0
            
            for layer in self.project.mapLayers().values():
                if isinstance(layer, QgsVectorLayer):
                    vector_count += 1
                    total_features += layer.featureCount()
                elif isinstance(layer, QgsRasterLayer):
                    raster_count += 1
            
            crs = self.project.crs()
            crs_name = crs.authid() if crs.isValid() else "Inconnu"
            
            return {
                'total_layers': layer_count,
                'vector_layers': vector_count,
                'raster_layers': raster_count,
                'total_features': total_features,
                'crs': crs_name,
                'project_name': self.project.baseName()
            }
        except Exception as e:
            self._log_error(f"Erreur lors de la génération du résumé: {str(e)}")
            return {}
    
    def get_layer_names(self):
        """
        Obtenir une liste des noms de couches dans le projet.
        
        Returns:
            Liste des noms de couches.
        """
        return [layer.name() for layer in self.project.mapLayers().values()]
    
    def get_layer_by_name(self, layer_name):
        """
        Obtenir une couche par son nom.
        
        Args:
            layer_name: Le nom de la couche à trouver.
        
        Returns:
            L'objet couche QGIS, ou None si non trouvé.
        """
        for layer in self.project.mapLayers().values():
            if layer.name() == layer_name:
                return layer
        return None
    
    def get_field_names(self, layer_name):
        """
        Obtenir les noms de champs pour une couche spécifique.
        
        Args:
            layer_name: Le nom de la couche.
        
        Returns:
            Liste des noms de champs, ou liste vide si la couche n'est pas trouvée.
        """
        layer = self.get_layer_by_name(layer_name)
        if layer and isinstance(layer, QgsVectorLayer):
            return [field.name() for field in layer.fields()]
        return []
    
    def get_feature_count(self, layer_name):
        """
        Obtenir le nombre d'entités pour une couche spécifique.
        
        Args:
            layer_name: Le nom de la couche.
        
        Returns:
            Le nombre d'entités, ou 0 si la couche n'est pas trouvée.
        """
        layer = self.get_layer_by_name(layer_name)
        if layer and isinstance(layer, QgsVectorLayer):
            return layer.featureCount()
        return 0
    
    def _log_error(self, message):
        """Journaliser un message d'erreur."""
        try:
            from qgis.core import QgsMessageLog, Qgis
            message_log = QgsMessageLog.getInstance()
            if message_log:
                message_log.logMessage(
                    f"[QGIS AI Assistant] {message}",
                    level=Qgis.Critical
                )
        except Exception:
            pass
    
    def tr(self, message):
        """Traduction d'un message."""
        return QCoreApplication.translate('ProjectAnalyzer', message)


class LayerInfoProvider:
    """
    Fournisseur d'informations détaillées sur les couches.
    """
    
    def __init__(self, layer):
        """
        Initialiser le fournisseur d'informations de couche.
        
        Args:
            layer: La couche QGIS.
        """
        self.layer = layer
    
    def get_statistics(self):
        """
        Obtenir les statistiques pour la couche.
        
        Returns:
            Dictionnaire avec les statistiques de la couche.
        """
        if not isinstance(self.layer, QgsVectorLayer):
            return {}
        
        stats = {
            'feature_count': self.layer.featureCount(),
            'geometry_type': self._get_geometry_type(),
            'field_count': self.layer.fields().count(),
            'crs': str(self.layer.crs().authid()),
            'extent': self._get_extent_stats()
        }
        
        return stats
    
    def _get_geometry_type(self):
        """Obtenir le type de géométrie."""
        geom_type = QgsWkbTypes.geometryType(self.layer.geometryType())
        type_map = {
            QgsWkbTypes.PointGeometry: "Point",
            QgsWkbTypes.LineGeometry: "Ligne",
            QgsWkbTypes.PolygonGeometry: "Polygone",
            QgsWkbTypes.NullGeometry: "Pas de géométrie",
            QgsWkbTypes.UnknownGeometry: "Inconnu"
        }
        return type_map.get(geom_type, "Inconnu")
    
    def _get_extent_stats(self):
        """Obtenir les statistiques d'étendue."""
        extent = self.layer.extent()
        if extent.isEmpty():
            return {}
        
        return {
            'area': extent.area(),
            'width': extent.width(),
            'height': extent.height()
        }

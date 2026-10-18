"""
Exécuteur d'outils QGIS pour l'Assistant IA.

Ce module fournit des fonctionnalités pour exécuter des outils QGIS et des algorithmes
de traitement basés sur les demandes de l'IA.
"""

import os
from qgis.core import (
    QgsProject, QgsApplication, QgsProcessingAlgorithm, 
    QgsVectorLayer, QgsRasterLayer, QgsMapLayer, 
    QgsFeature, QgsGeometry, QgsWkbTypes, QgsField,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem,
    QgsProcessingRegistry, QgsProcessingContext, 
    QgsProcessingFeedback
)
from qgis.PyQt.QtCore import QCoreApplication, QObject, pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox


class QGISToolsExecutor(QObject):
    """
    Exécuteur pour les outils QGIS et les algorithmes de traitement.
    
    Cette classe peut :
    - Découvrir les algorithmes de traitement disponibles
    - Exécuter des algorithmes de traitement avec des paramètres
    - Créer et modifier des couches
    - Effectuer des tâches de géotraitement courantes
    """
    
    # Signal pour les mises à jour de progression
    progress_updated = pyqtSignal(str, int)
    # Signal pour l'achèvement
    execution_finished = pyqtSignal(bool, str)
    
    def __init__(self, iface):
        """
        Initialiser l'exécuteur d'outils.
        
        Args:
            iface: L'instance de l'interface QGIS.
        """
        super().__init__()
        self.iface = iface
        self.project = QgsProject.instance()
        
        # Initialiser le registre de traitement
        self.registry = QgsApplication.processingRegistry()
        self.context = QgsProcessingContext()
        self.feedback = QgsProcessingFeedback()
        
        # Définir le projet dans le contexte
        self.context.setProject(self.project)
    
    def get_available_tools(self):
        """
        Obtenir une liste des algorithmes de traitement disponibles.
        
        Returns:
            Dictionnaire avec les catégories d'outils et leurs algorithmes.
        """
        tools = {}
        
        try:
            # Obtenir tous les fournisseurs d'algorithmes
            providers = self.registry.providers()
            
            for provider in providers:
                # Ignorer les fournisseurs désactivés
                if not provider.isActive():
                    continue
                
                provider_name = provider.name()
                
                # Obtenir les algorithmes de ce fournisseur
                # Dans QGIS 4.x, utiliser getAlgsList() ou algorithms() selon la version
                try:
                    algorithms = provider.algorithms()
                except AttributeError:
                    # Solution de repli pour les versions plus récentes de QGIS
                    if hasattr(provider, 'getAlgsList'):
                        algorithms = provider.getAlgsList()
                    else:
                        algorithms = []
                
                algorithm_names = []
                
                for alg in algorithms:
                    try:
                        algorithm_names.append(alg.displayName())
                    except AttributeError:
                        # Certains algorithmes peuvent ne pas avoir displayName
                        algorithm_names.append(alg.name() if hasattr(alg, 'name') else str(alg))
                
                # Trier par ordre alphabétique
                algorithm_names.sort()
                
                if algorithm_names:
                    tools[provider_name] = algorithm_names
            
            # Trier les catégories par ordre alphabétique
            sorted_tools = {}
            for category in sorted(tools.keys()):
                sorted_tools[category] = tools[category]
            
            return sorted_tools
        
        except Exception as e:
            self._log_error(f"Erreur lors de l'obtention des outils disponibles : {str(e)}")
            return {}
    
    def find_algorithm(self, algorithm_name):
        """
        Trouver un algorithme par son nom.
        
        Args:
            algorithm_name: Le nom ou le nom partiel de l'algorithme.
        
        Returns:
            L'objet QgsProcessingAlgorithm, ou None si non trouvé.
        """
        try:
            # Essayer la correspondance exacte d'abord
            algorithm = self.registry.algorithmById(algorithm_name)
            if algorithm:
                return algorithm
            
            # Essayer de trouver par nom d'affichage
            providers = self.registry.providers()
            for provider in providers:
                if not provider.isActive():
                    continue
                
                for alg in provider.algorithms():
                    if algorithm_name.lower() in alg.displayName().lower():
                        return alg
            
            return None
        
        except Exception as e:
            self._log_error(f"Erreur lors de la recherche de l'algorithme {algorithm_name}: {str(e)}")
            return None
    
    def execute_algorithm(self, algorithm_name, parameters=None):
        """
        Exécuter un algorithme de traitement.
        
        Args:
            algorithm_name: Le nom de l'algorithme à exécuter.
            parameters: Dictionnaire des valeurs de paramètres.
        
        Returns:
            Dictionnaire avec les résultats de l'exécution.
        """
        if parameters is None:
            parameters = {}
        
        try:
            # Trouver l'algorithme
            algorithm = self.find_algorithm(algorithm_name)
            if not algorithm:
                return {
                    'success': False,
                    'error': f"Algorithme '{algorithm_name}' introuvable",
                    'results': None
                }
            
            # Créer un nouvel objet de feedback
            feedback = QgsProcessingFeedback()
            
            # Exécuter l'algorithme
            self._log_message(f"Exécution de l'algorithme : {algorithm_name}")
            
            results = algorithm.run(
                parameters,
                self.context,
                feedback
            )
            
            # Traiter les résultats
            output = self._process_results(results, algorithm)
            
            self._log_message(f"Algorithme exécuté avec succès : {algorithm_name}")
            
            return {
                'success': True,
                'algorithm': algorithm_name,
                'results': output,
                'error': None
            }
        
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution de l'algorithme {algorithm_name}: {str(e)}"
            self._log_error(error_msg)
            return {
                'success': False,
                'algorithm': algorithm_name,
                'error': error_msg,
                'results': None
            }
    
    def _process_results(self, results, algorithm):
        """
        Traiter les résultats de l'exécution d'un algorithme.
        
        Args:
            results: Les résultats bruts de l'algorithme.
            algorithm: L'algorithme qui a été exécuté.
        
        Returns:
            Dictionnaire avec les résultats traités.
        """
        output = {
            'outputs': {},
            'layers': [],
            'files': []
        }
        
        try:
            # Vérifier si results est un dictionnaire
            if isinstance(results, dict):
                for output_name, output_value in results.items():
                    if output_name in ["OUTPUT", "OUTPUT_LAYER", "OUTPUT_FILE"]:
                        output['outputs'][output_name] = str(output_value)
                        
                        # Si c'est une couche, ajouter à la liste des couches
                        if isinstance(output_value, QgsMapLayer):
                            output['layers'].append({
                                'name': output_value.name(),
                                'type': 'vector' if isinstance(output_value, QgsVectorLayer) else 'raster',
                                'id': output_value.id()
                            })
                        elif isinstance(output_value, str) and os.path.exists(output_value):
                            output['files'].append(output_value)
            
            return output
        
        except Exception as e:
            self._log_error(f"Erreur lors du traitement des résultats : {str(e)}")
            return output
    
    def execute_tool_command(self, command, parameters=None):
        """
        Exécuter une commande d'outil basée sur une description en langage naturel.
        
        Args:
            command: La commande ou l'outil à exécuter.
            parameters: Dictionnaire de paramètres.
        
        Returns:
            Dictionnaire avec les résultats de l'exécution.
        """
        if parameters is None:
            parameters = {}
        
        # Mapper les commandes courantes aux noms d'algorithmes réels
        command_map = {
            'buffer': 'qgis:buffer',
            'intersection': 'qgis:intersection',
            'clip': 'qgis:clip',
            'merge': 'qgis:mergevectorlayers',
            'dissolve': 'qgis:dissolve',
            'reproject': 'qgis:reprojectlayer',
            'export': 'qgis:exportfeatures',
            'import': 'qgis:importlayer',
            'calculate field': 'qgis:fieldcalculator',
            'select by expression': 'qgis:selectbyexpression',
            'select by location': 'qgis:selectbylocation',
            'create grid': 'qgis:creategrid',
            'convex hull': 'qgis:convexhull',
            'difference': 'qgis:difference',
            'symmetric difference': 'qgis:symmetricaldifference',
            'union': 'qgis:union',
            'points to line': 'qgis:pointstoline',
            'line to polygon': 'qgis:linestopolygons',
            'polygon to line': 'qgis:polygonstolines',
            'extract by expression': 'qgis:extractbyexpression',
            'extract by location': 'qgis:extractbylocation',
            'join attributes': 'qgis:joinattributestable',
            'summarize statistics': 'qgis:statisticsbycategories',
            'create points layer': 'qgis:createpointslayerfromtable',
        }
        
        # Normaliser la commande
        command_lower = command.lower()
        
        # Essayer de trouver l'algorithme correspondant
        algorithm_name = None
        for cmd_key, alg_name in command_map.items():
            if cmd_key in command_lower:
                algorithm_name = alg_name
                break
        
        # Si aucune correspondance trouvée, essayer de trouver l'algorithme par nom
        if not algorithm_name:
            algorithm_name = command
        
        # Exécuter l'algorithme
        return self.execute_algorithm(algorithm_name, parameters)
    
    def create_vector_layer(self, name, geometry_type, crs=None, fields=None):
        """
        Créer une nouvelle couche vectorielle.
        
        Args:
            name: Le nom pour la nouvelle couche.
            geometry_type: Le type de géométrie ('point', 'line', 'polygon').
            crs: Le système de coordonnées de référence (optionnel).
            fields: Liste des définitions de champs (optionnel).
        
        Returns:
            La QgsVectorLayer créée, ou None si la création a échoué.
        """
        try:
            # SCR par défaut
            if crs is None:
                crs = self.project.crs()
            
            # Mapper le type de géométrie string à QgsWkbTypes
            geom_type_map = {
                'point': QgsWkbTypes.PointGeometry,
                'line': QgsWkbTypes.LineGeometry,
                'polygon': QgsWkbTypes.PolygonGeometry
            }
            
            geom_type = geom_type_map.get(geometry_type.lower(), QgsWkbTypes.PointGeometry)
            
            # Créer la couche
            layer = QgsVectorLayer(
                f"{geometry_type}?crs={crs.authid()}",
                name,
                "memory"
            )
            
            if not layer.isValid():
                self._log_error(f"Échec de la création de la couche vectorielle : {name}")
                return None
            
            # Définir le type de géométrie
            provider = layer.dataProvider()
            provider.setCrs(crs)
            
            # Ajouter des champs si fournis
            if fields:
                layer.startEditing()
                provider.addAttributes(fields)
                layer.updateFields()
                layer.commitChanges()
            
            # Ajouter la couche au projet
            self.project.addMapLayer(layer)
            
            self._log_message(f"Couche vectorielle créée : {name}")
            return layer
        
        except Exception as e:
            self._log_error(f"Erreur lors de la création de la couche vectorielle : {str(e)}")
            return None
    
    def execute_buffer(self, layer_name, distance, segments=5, dissolve=True):
        """
        Exécuter une opération de tampon sur une couche.
        
        Args:
            layer_name: Le nom de la couche à tamponner.
            distance: La distance du tampon.
            segments: Nombre de segments pour les arcs circulaires.
            dissolve: Si vrai, dissoudre le résultat.
        
        Returns:
            Dictionnaire avec les résultats de l'exécution.
        """
        parameters = {
            'INPUT': layer_name,
            'DISTANCE': distance,
            'SEGMENTS': segments,
            'DISSOLVE': dissolve,
            'END_CAP_STYLE': 0,  # Arrondi
            'JOIN_STYLE': 0,    # Arrondi
            'MITER_LIMIT': 2.0,
            'OUTPUT': 'memory:'
        }
        
        return self.execute_tool_command('buffer', parameters)
    
    def execute_intersection(self, layer1_name, layer2_name, output_name):
        """
        Exécuter une opération d'intersection entre deux couches.
        
        Args:
            layer1_name: Le nom de la première couche.
            layer2_name: Le nom de la deuxième couche.
            output_name: Le nom pour la couche de sortie.
        
        Returns:
            Dictionnaire avec les résultats de l'exécution.
        """
        parameters = {
            'INPUT': layer1_name,
            'OVERLAY': layer2_name,
            'OUTPUT': f'memory:{output_name}'
        }
        
        return self.execute_tool_command('intersection', parameters)
    
    def execute_clip(self, input_layer_name, overlay_layer_name, output_name):
        """
        Découper une couche en utilisant une autre couche.
        
        Args:
            input_layer_name: Le nom de la couche à découper.
            overlay_layer_name: Le nom de la couche de découpe.
            output_name: Le nom pour la couche de sortie.
        
        Returns:
            Dictionnaire avec les résultats de l'exécution.
        """
        parameters = {
            'INPUT': input_layer_name,
            'OVERLAY': overlay_layer_name,
            'OUTPUT': f'memory:{output_name}'
        }
        
        return self.execute_tool_command('clip', parameters)
    
    def get_tool_parameters(self, algorithm_name):
        """
        Obtenir les paramètres pour un outil/algorithme spécifique.
        
        Args:
            algorithm_name: Le nom de l'algorithme.
        
        Returns:
            Dictionnaire avec les informations des paramètres.
        """
        algorithm = self.find_algorithm(algorithm_name)
        if not algorithm:
            return {'error': f"Algorithme '{algorithm_name}' introuvable"}
        
        try:
            # Obtenir les définitions des paramètres
            parameter_defs = algorithm.parameterDefinitions()
            
            parameters = {}
            for param_def in parameter_defs:
                param_info = {
                    'name': param_def.name(),
                    'description': param_def.description(),
                    'type': param_def.type(),
                    'required': param_def.isRequired(),
                    'default': str(param_def.defaultValue()) if param_def.defaultValue() else None
                }
                
                # Ajouter les métadonnées si disponibles
                if hasattr(param_def, 'metadata'):
                    param_info['metadata'] = param_def.metadata()
                
                parameters[param_def.name()] = param_info
            
            return parameters
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_layer_statistics(self, layer_name):
        """
        Obtenir les statistiques pour une couche.
        
        Args:
            layer_name: Le nom de la couche.
        
        Returns:
            Dictionnaire avec les statistiques de la couche.
        """
        layer = self._get_layer_by_name(layer_name)
        if not layer:
            return {'error': f"Couche '{layer_name}' introuvable"}
        
        if not isinstance(layer, QgsVectorLayer):
            return {'error': f"La couche '{layer_name}' n'est pas une couche vectorielle"}
        
        try:
            stats = {
                'name': layer.name(),
                'type': 'vector',
                'feature_count': layer.featureCount(),
                'geometry_type': self._get_geometry_type(layer),
                'fields': self._get_field_info(layer),
                'crs': str(layer.crs().authid()),
                'extent': self._get_extent_info(layer)
            }
            
            return stats
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_layer_by_name(self, layer_name):
        """Obtenir une couche par son nom."""
        for layer in self.project.mapLayers().values():
            if layer.name() == layer_name:
                return layer
        return None
    
    def _get_geometry_type(self, layer):
        """Obtenir le type de géométrie sous forme de chaîne."""
        geom_type = QgsWkbTypes.geometryType(layer.geometryType())
        type_map = {
            QgsWkbTypes.PointGeometry: "Point",
            QgsWkbTypes.LineGeometry: "Ligne",
            QgsWkbTypes.PolygonGeometry: "Polygone",
            QgsWkbTypes.NullGeometry: "Pas de géométrie",
            QgsWkbTypes.UnknownGeometry: "Inconnu"
        }
        return type_map.get(geom_type, "Inconnu")
    
    def _get_field_info(self, layer):
        """Obtenir les informations de champs pour une couche."""
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
        
        return field_info
    
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
    
    def _get_extent_info(self, layer):
        """Obtenir les informations d'étendue pour une couche."""
        extent = layer.extent()
        if extent.isEmpty():
            return {}
        
        return {
            'x_min': extent.xMinimum(),
            'x_max': extent.xMaximum(),
            'y_min': extent.yMinimum(),
            'y_max': extent.yMaximum(),
            'area': extent.area()
        }
    
    def _log_message(self, message):
        """Journaliser un message d'information."""
        try:
            from qgis.core import QgsMessageLog, Qgis
            message_log = QgsMessageLog.getInstance()
            if message_log:
                message_log.logMessage(
                    f"[QGIS AI Assistant] {message}",
                    level=Qgis.Info
                )
        except Exception:
            pass
    
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
        return QCoreApplication.translate('QGISToolsExecutor', message)


class ToolCommandParser:
    """
    Analyseur pour extraire les commandes d'outils des réponses IA.
    """
    
    def __init__(self):
        """Initialiser l'analyseur de commandes."""
        self.command_patterns = {
            'buffer': r'buffer\s+(?:layer\s+)?["\']?([^"\']+)["\']?\s+(?:distance\s+)?([\d\.]+)',
            'intersection': r'intersection\s+(?:of\s+)?["\']?([^"\']+)["\']?\s+(?:and\s+)?["\']?([^"\']+)["\']?',
            'clip': r'clip\s+(?:layer\s+)?["\']?([^"\']+)["\']?\s+(?:with\s+)?["\']?([^"\']+)["\']?',
            'select': r'select\s+(?:from\s+)?["\']?([^"\']+)["\']?\s+(?:where\s+)?(.+)',
            'export': r'export\s+(?:layer\s+)?["\']?([^"\']+)["\']?\s+(?:to\s+)?["\']?([^"\']+)["\']?',
            'calculate': r'calculate\s+(?:field\s+)?["\']?([^"\']+)["\']?\s+(?:as\s+)?(.+)',
        }
    
    def parse_command(self, text):
        """
        Analyser une commande à partir d'un texte.
        
        Args:
            text: Le texte à analyser.
        
        Returns:
            Dictionnaire avec les informations de commande analysées.
        """
        import re
        
        text_lower = text.lower()
        
        for command, pattern in self.command_patterns.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return {
                    'command': command,
                    'parameters': match.groups(),
                    'original_text': text
                }
        
        # Si aucun modèle ne correspond, retourner le texte comme une commande générique
        return {
            'command': 'custom',
            'parameters': [text],
            'original_text': text
        }
    
    def extract_qgis_commands(self, response):
        """
        Extraire les commandes QGIS d'une réponse IA.
        
        Args:
            response: Le texte de réponse IA.
        
        Returns:
            Liste des commandes extraites.
        """
        commands = []
        
        # Séparer par des délimiteurs communs
        parts = [response]
        
        # Essayer de séparer par des blocs de code
        if '```' in response:
            parts = response.split('```')
            # Garder seulement les parties qui sont entre les marqueurs ```
            parts = [p for i, p in enumerate(parts) if i % 2 == 1]
        
        # Analyser chaque partie
        for part in parts:
            command_info = self.parse_command(part.strip())
            if command_info['command'] != 'custom' or len(part.strip()) > 0:
                commands.append(command_info)
        
        return commands

"""
Module de ressources pour l'Assistant IA QGIS.

Ce module gère le chargement et la gestion des ressources.
"""

import os
from qgis.PyQt.QtGui import QIcon


class ResourceManager:
    """
    Gestionnaire des ressources du plugin.
    """
    
    def __init__(self, plugin_dir):
        """
        Initialiser le gestionnaire de ressources.
        
        Args:
            plugin_dir: Le répertoire du plugin.
        """
        self.plugin_dir = plugin_dir
        self.icon_dir = os.path.join(plugin_dir, 'icons')
        
        # Cache pour les icônes chargées
        self.icon_cache = {}
    
    def get_icon(self, icon_name, default=None):
        """
        Obtenir une icône par son nom.
        
        Args:
            icon_name: Le nom du fichier d'icône (sans extension).
            default: Icône par défaut à retourner si non trouvée.
        
        Returns:
            Objet QIcon, ou la valeur par défaut si non trouvée.
        """
        # Vérifier le cache en premier
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]
        
        # Essayer différentes extensions
        extensions = ['.png', '.svg', '.jpg', '.jpeg']
        
        for ext in extensions:
            icon_path = os.path.join(self.icon_dir, f"{icon_name}{ext}")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.icon_cache[icon_name] = icon
                return icon
        
        # Retourner la valeur par défaut ou créer une icône vide
        if default:
            return default
        
        empty_icon = QIcon()
        self.icon_cache[icon_name] = empty_icon
        return empty_icon
    
    def get_icon_path(self, icon_name):
        """
        Obtenir le chemin vers un fichier d'icône.
        
        Args:
            icon_name: Le nom du fichier d'icône (sans extension).
        
        Returns:
            Le chemin complet vers le fichier d'icône, ou None si non trouvé.
        """
        extensions = ['.png', '.svg', '.jpg', '.jpeg']
        
        for ext in extensions:
            icon_path = os.path.join(self.icon_dir, f"{icon_name}{ext}")
            if os.path.exists(icon_path):
                return icon_path
        
        return None
    
    def get_plugin_dir(self):
        """Obtenir le répertoire du plugin."""
        return self.plugin_dir
    
    def get_icon_dir(self):
        """Obtenir le répertoire des icônes."""
        return self.icon_dir


class IconProvider:
    """
    Fournisseur d'icônes standard utilisées dans le plugin.
    """
    
    STANDARD_ICONS = {
        'plugin': 'icon',
        'send': 'send',
        'settings': 'settings',
        'analyze': 'analyze',
        'tools': 'tools',
        'clear': 'clear',
        'save': 'save',
        'cancel': 'cancel',
        'test': 'test'
    }
    
    def __init__(self, resource_manager):
        """
        Initialiser le fournisseur d'icônes.
        
        Args:
            resource_manager: L'instance du gestionnaire de ressources.
        """
        self.resource_manager = resource_manager
    
    def get_standard_icon(self, icon_key):
        """
        Obtenir une icône standard par clé.
        
        Args:
            icon_key: La clé pour l'icône standard.
        
        Returns:
            Objet QIcon.
        """
        icon_name = self.STANDARD_ICONS.get(icon_key, 'icon')
        return self.resource_manager.get_icon(icon_name)

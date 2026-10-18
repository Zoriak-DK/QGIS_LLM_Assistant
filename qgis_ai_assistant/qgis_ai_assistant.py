"""
Classe principale du plugin Assistant IA QGIS.

Cette classe gère le cycle de vie du plugin, l'intégration des menus et les fonctionnalités principales.
"""

import os
from qgis.PyQt.QtCore import QCoreApplication, Qt, QTranslator, QSettings
from qgis.PyQt.QtWidgets import (
    QAction, QMenu, QMessageBox, QToolBar, QDockWidget
)
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsApplication, Qgis
from .main_dialog import AIAssistantDialog
from .settings_dialog import AISettingsDialog


class QGISAIAssistant:
    """
    Plugin principal Assistant IA QGIS.
    
    Ce plugin fournit un assistant IA qui peut :
    - Analyser le projet QGIS actuel
    - Exécuter des outils et algorithmes de traitement QGIS
    - Répondre aux questions des utilisateurs sur les SIG et QGIS
    - Être configuré avec des paramètres d'API personnalisés
    """
    
    def __init__(self, iface):
        """
        Initialiser le plugin.
        
        Args:
            iface: L'instance de l'interface QGIS.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Vérifier la version de QGIS pour la compatibilité
        qgis_version = Qgis.QGIS_VERSION.split('.')
        major_version = int(qgis_version[0]) if qgis_version else 0
        minor_version = int(qgis_version[1]) if len(qgis_version) > 1 else 0
        
        # Exiger QGIS 4.2 ou version supérieure
        if major_version < 4 or (major_version == 4 and minor_version < 2):
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr("Assistant IA QGIS"),
                self.tr("Ce plugin nécessite QGIS 4.2 ou une version supérieure. Version actuelle : {}").format(
                    Qgis.QGIS_VERSION
                )
            )
            # Toujours initialiser pour éviter les erreurs, mais avertir l'utilisateur
        
        # Initialiser les paramètres
        self.settings = QSettings("QGIS_AI_Assistant", "Settings")
        
        # État du plugin
        self.dialog = None
        self.settings_dialog = None
        self.dock_widget = None
        
        # Traducteur pour l'internationalisation
        self.translator = None
        
        # Initialiser les ressources
        self._init_resources()
        
    def _init_resources(self):
        """Initialiser les ressources et traductions du plugin."""
        # Charger les traductions si disponibles
        try:
            # Essayer d'obtenir la locale depuis QCoreApplication
            qapp = QCoreApplication.instance()
            if hasattr(qapp, 'locale') and callable(qapp.locale):
                locale_obj = qapp.locale()
                # Gérer les deux cas : QLocale object ou string
                if hasattr(locale_obj, 'name'):
                    locale = locale_obj.name()
                else:
                    locale = str(locale_obj)
            else:
                # Solution de repli : utiliser QSettings ou une valeur par défaut
                from qgis.core import QgsApplication
                locale = QgsApplication.instance().locale()
        except Exception:
            # Valeur par défaut
            locale = "fr_FR"
        
        if locale:
            locale_path = os.path.join(
                self.plugin_dir, 
                'i18n',
                f'qgis_ai_assistant_{locale}.qm'
            )
            if os.path.exists(locale_path):
                self.translator = QTranslator()
                self.translator.load(locale_path)
                QCoreApplication.installTranslator(self.translator)
    
    def initGui(self):
        """
        Initialiser l'interface graphique du plugin.
        
        Cette méthode est appelée lorsque le plugin est chargé.
        """
        # Créer le chemin de l'icône
        icon_path = os.path.join(self.plugin_dir, 'icons', 'icon.svg')
        
        # Créer l'action principale pour ouvrir l'assistant IA
        self.open_assistant_action = QAction(
            QIcon(icon_path),
            self.tr("Ouvrir l'Assistant IA"),
            self.iface.mainWindow()
        )
        self.open_assistant_action.setObjectName("QGISAIAssistantOpenAction")
        self.open_assistant_action.triggered.connect(self.open_assistant)
        
        # Créer l'action des paramètres
        self.settings_action = QAction(
            QIcon(icon_path),
            self.tr("Paramètres de l'Assistant IA"),
            self.iface.mainWindow()
        )
        self.settings_action.setObjectName("QGISAIAssistantSettingsAction")
        self.settings_action.triggered.connect(self.open_settings)
        
        # Ajouter les actions à la barre d'outils et au menu
        self.toolbar = self.iface.addToolBar(self.tr("Assistant IA"))
        self.toolbar.setObjectName("QGISAIAssistantToolBar")
        self.toolbar.addAction(self.open_assistant_action)
        
        # Créer le menu principal dans la barre de menus QGIS
        # Pour QGIS 4.2, on crée le menu manuellement
        self.menu = QMenu(self.tr("&Assistant IA"))
        self.menu.setIcon(QIcon(icon_path))
        self.menu.setObjectName("QGISAIAssistantMenu")
        
        # Ajouter les actions au menu
        self.menu.addAction(self.open_assistant_action)
        self.menu.addSeparator()
        self.menu.addAction(self.settings_action)
        
        # Ajouter le menu à la barre de menus principale
        menu_bar = self.iface.mainWindow().menuBar()
        menu_bar.addMenu(self.menu)
        
        # Note: Dans QGIS 4.2, addPluginTo*Menu() ne fonctionne plus avec un QMenu
        # On laisse simplement le menu dans la barre principale pour l'instant
        
        # Stocker la référence au menu pour le déchargement
        self.parent_menu = menu_bar
        
    def unload(self):
        """
        Désinstaller le plugin.
        
        Cette méthode est appelée lorsque le plugin est déchargé.
        """
        # Supprimer la barre d'outils
        if self.toolbar:
            # QGIS 4.2: removeToolBar n'existe plus, utiliser deleteLater
            self.toolbar.deleteLater()
            self.toolbar = None
        
        # Supprimer le menu
        if self.menu and self.parent_menu:
            try:
                self.parent_menu.removeAction(self.menu.menuAction())
            except Exception:
                pass
            self.menu = None
        
        # Supprimer les actions
        if self.open_assistant_action:
            del self.open_assistant_action
        if self.settings_action:
            del self.settings_action
        
        # Supprimer le traducteur
        if self.translator:
            QCoreApplication.removeTranslator(self.translator)
            self.translator = None
        
        # Fermer les dialogues
        if self.dialog:
            self.dialog.close()
            self.dialog = None
        
        if self.settings_dialog:
            self.settings_dialog.close()
            self.settings_dialog = None
        
        # Supprimer le widget dock si il existe
        if self.dock_widget:
            self.dock_widget.close()
            self.dock_widget = None
    
    def open_assistant(self):
        """
        Ouvrir le dialogue de l'assistant IA.
        """
        if not self.dialog:
            self.dialog = AIAssistantDialog(
                self.iface,
                self.settings,
                parent=self.iface.mainWindow()
            )
            self.dialog.setWindowTitle(self.tr("Assistant IA QGIS"))
            
            # Connecter l'événement de fermeture
            self.dialog.destroyed.connect(self._on_dialog_destroyed)
        
        # Afficher le dialogue
        self.dialog.show()
        self.dialog.activateWindow()
        self.dialog.raise_()
    
    def open_settings(self):
        """
        Ouvrir le dialogue des paramètres de l'assistant IA.
        """
        if not self.settings_dialog:
            self.settings_dialog = AISettingsDialog(
                self.iface,
                self.settings,
                parent=self.iface.mainWindow()
            )
            self.settings_dialog.setWindowTitle(self.tr("Paramètres de l'Assistant IA"))
            
            # Connecter l'événement de fermeture
            self.settings_dialog.destroyed.connect(self._on_settings_dialog_destroyed)
        
        # Afficher le dialogue
        self.settings_dialog.show()
        self.settings_dialog.activateWindow()
        self.settings_dialog.raise_()
    
    def _on_dialog_destroyed(self):
        """Gérer la destruction du dialogue principal."""
        self.dialog = None
    
    def _on_settings_dialog_destroyed(self):
        """Gérer la destruction du dialogue des paramètres."""
        self.settings_dialog = None
    
    def tr(self, message):
        """
        Obtenir la traduction pour un message.
        
        Args:
            message: Le message à traduire.
        
        Returns:
            Le message traduit.
        """
        return QCoreApplication.translate('QGISAIAssistant', message)
    
    def run(self):
        """
        Méthode run qui effectue toute la configuration du plugin.
        
        Cela est appelé lorsque le plugin est chargé.
        """
        self.initGui()


def classFactory(iface):
    """
    Fonction factory pour créer une instance du plugin.
    
    Cette fonction est requise par QGIS pour charger le plugin.
    
    Args:
        iface: L'instance de l'interface QGIS.
    
    Returns:
        Une instance du plugin QGISAIAssistant.
    """
    return QGISAIAssistant(iface)

"""
Package du plugin Assistant IA QGIS

Ce package contient tous les modules pour le plugin Assistant IA QGIS.
"""

# Importer les classes principales pour un accès plus facile
from .qgis_ai_assistant import QGISAIAssistant, classFactory
from .main_dialog import AIAssistantDialog
from .settings_dialog import AISettingsDialog
from .ai_engine import AIEngine, AIResponseProcessor
from .project_analyzer import ProjectAnalyzer, LayerInfoProvider
from .qgis_tools import QGISToolsExecutor, ToolCommandParser
from .resources import ResourceManager, IconProvider
from .conversation_manager import ConversationManager, Conversation
from .http_client import HTTPClient, StreamingHTTPClient

__version__ = "1.0.0"
__author__ = "Équipe Assistant IA QGIS"
__description__ = "Un assistant IA pour QGIS qui peut analyser des projets, exécuter des outils et répondre aux questions des utilisateurs"

# Métadonnées du plugin
PLUGIN_NAME = "Assistant IA QGIS"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = __description__

"""
Gestionnaire de conversations pour l'Assistant IA QGIS.

Ce module fournit des fonctionnalités pour :
- Gérer plusieurs conversations simultanément
- Sauvegarder et charger l'historique des conversations
- Changer entre différentes conversations
- Conserver les conversations entre les sessions
"""

import os
import json
from datetime import datetime
from qgis.PyQt.QtCore import QObject, pyqtSignal, QSettings, QCoreApplication
from qgis.core import QgsProject


class Conversation:
    """
    Représente une seule conversation avec l'IA.
    
    Attributs:
        id: Identifiant unique pour la conversation
        title: Titre d'affichage pour la conversation
        messages: Liste de dictionnaires de messages
        created_at: Horodatage de la création de la conversation
        updated_at: Horodatage de la dernière mise à jour
        is_active: Si cette conversation est la conversation active actuelle
    """
    
    def __init__(self, conv_id=None, title="Nouvelle conversation"):
        """
        Initialiser une nouvelle conversation.
        
        Args:
            conv_id: Identifiant unique (en génère un si non fourni)
            title: Titre d'affichage pour la conversation
        """
        self.id = conv_id or self._generate_id()
        self.title = title
        self.messages = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.is_active = False
    
    def _generate_id(self):
        """Générer un identifiant de conversation unique."""
        return f"conv_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    def add_message(self, content, is_user=False):
        """
        Ajouter un message à la conversation.
        
        Args:
            content: Le contenu du message
            is_user: Si le message vient de l'utilisateur
        """
        message = {
            'id': self._generate_message_id(),
            'content': content,
            'is_user': is_user,
            'timestamp': datetime.now(),
            'role': 'user' if is_user else 'assistant'
        }
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def _generate_message_id(self):
        """Générer un identifiant de message unique."""
        return f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    def to_dict(self):
        """Convertir la conversation en dictionnaire pour la sérialisation."""
        return {
            'id': self.id,
            'title': self.title,
            'messages': [
                {
                    'id': msg['id'],
                    'content': msg['content'],
                    'is_user': msg['is_user'],
                    'timestamp': msg['timestamp'].isoformat(),
                    'role': msg['role']
                }
                for msg in self.messages
            ],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Créer une conversation à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire avec les données de la conversation
        
        Returns:
            Objet Conversation
        """
        conv = cls(data.get('id'), data.get('title', "Conversation"))
        conv.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        conv.updated_at = datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        conv.is_active = data.get('is_active', False)
        
        for msg_data in data.get('messages', []):
            msg = {
                'id': msg_data.get('id'),
                'content': msg_data.get('content'),
                'is_user': msg_data.get('is_user', False),
                'timestamp': datetime.fromisoformat(msg_data.get('timestamp', datetime.now().isoformat())),
                'role': msg_data.get('role', 'assistant')
            }
            conv.messages.append(msg)
        
        return conv


class ConversationManager(QObject):
    """
    Gestionnaire pour les conversations IA multiples.
    
    Cette classe gère :
    - La création et la gestion de plusieurs conversations
    - La sauvegarde et le chargement des conversations dans/es le stockage
    - Le changement entre les conversations
    - La conservation de l'historique des conversations
    """
    
    # Signaux
    conversation_created = pyqtSignal(Conversation)
    conversation_switched = pyqtSignal(Conversation)
    conversation_deleted = pyqtSignal(str)
    conversation_updated = pyqtSignal(Conversation)
    conversations_loaded = pyqtSignal(list)
    
    def __init__(self, settings=None, storage_dir=None):
        """
        Initialiser le gestionnaire de conversations.
        
        Args:
            settings: Objet QSettings pour stocker les préférences
            storage_dir: Répertoire pour stocker les données de conversation
        """
        super().__init__()
        self.settings = settings or QSettings("QGIS_AI_Assistant", "Settings")
        self.storage_dir = storage_dir
        
        # Initialiser la liste des conversations
        self.conversations = []
        
        # Conversation actuelle
        self.current_conversation = None
        
        # Initialiser le stockage
        if not self.storage_dir:
            self.storage_dir = self._get_default_storage_dir()
        
        # S'assurer que le répertoire de stockage existe
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Charger les conversations existantes
        self._load_conversations()
        
        # Créer une nouvelle conversation si aucune n'existe
        if not self.conversations:
            self.create_conversation()
    
    def _get_default_storage_dir(self):
        """Obtenir le répertoire de stockage par défaut."""
        # Essayer d'utiliser le répertoire du projet QGIS si disponible
        try:
            from qgis.core import QgsProject
            project = QgsProject.instance()
            project_path = project.fileName()
            if project_path:
                return os.path.join(os.path.dirname(project_path), "ai_assistant_conversations")
        except Exception:
            pass
        
        # Utiliser le répertoire personnel de l'utilisateur
        home_dir = os.path.expanduser("~")
        return os.path.join(home_dir, ".qgis_ai_assistant", "conversations")
    
    def create_conversation(self, title="Nouvelle conversation"):
        """
        Créer une nouvelle conversation.
        
        Args:
            title: Titre pour la nouvelle conversation
        
        Returns:
            Le nouvel objet Conversation
        """
        # Désactiver la conversation actuelle si elle existe
        if self.current_conversation:
            self.current_conversation.is_active = False
        
        # Créer une nouvelle conversation
        new_conv = Conversation(title=title)
        new_conv.is_active = True
        self.conversations.insert(0, new_conv)
        self.current_conversation = new_conv
        
        # Émettre le signal
        self.conversation_created.emit(new_conv)
        self.conversation_switched.emit(new_conv)
        
        # Sauvegarder les conversations
        self._save_conversations()
        
        return new_conv
    
    def switch_conversation(self, conv_id):
        """
        Changer vers une autre conversation.
        
        Args:
            conv_id: ID de la conversation vers laquelle changer
        
        Returns:
            True si la conversation a été trouvée et changée, False sinon
        """
        for conv in self.conversations:
            if conv.id == conv_id:
                # Désactiver la conversation actuelle
                if self.current_conversation:
                    self.current_conversation.is_active = False
                
                # Activer la nouvelle conversation
                conv.is_active = True
                self.current_conversation = conv
                
                # Émettre le signal
                self.conversation_switched.emit(conv)
                
                # Sauvegarder les conversations
                self._save_conversations()
                
                return True
        
        return False
    
    def delete_conversation(self, conv_id):
        """
        Supprimer une conversation.
        
        Args:
            conv_id: ID de la conversation à supprimer
        
        Returns:
            True si la conversation a été trouvée et supprimée, False sinon
        """
        for i, conv in enumerate(self.conversations):
            if conv.id == conv_id:
                # Ne pas supprimer si c'est la dernière conversation
                if len(self.conversations) <= 1:
                    # Juste la vider
                    conv.messages = []
                    conv.title = self.tr("Nouvelle conversation")
                    conv.updated_at = datetime.now()
                    self.conversation_updated.emit(conv)
                    self._save_conversations()
                    return True
                
                # Supprimer la conversation
                del self.conversations[i]
                
                # Si c'était la conversation actuelle, changer vers une autre
                if self.current_conversation and self.current_conversation.id == conv_id:
                    if self.conversations:
                        self.current_conversation = self.conversations[0]
                        self.current_conversation.is_active = True
                    else:
                        self.current_conversation = None
                
                # Émettre le signal
                self.conversation_deleted.emit(conv_id)
                
                # Sauvegarder les conversations
                self._save_conversations()
                
                return True
        
        return False
    
    def get_conversation(self, conv_id):
        """
        Obtenir une conversation par son ID.
        
        Args:
            conv_id: ID de la conversation à obtenir
        
        Returns:
            Objet Conversation ou None si non trouvé
        """
        for conv in self.conversations:
            if conv.id == conv_id:
                return conv
        return None
    
    def get_all_conversations(self):
        """Obtenir toutes les conversations."""
        return self.conversations
    
    def get_current_conversation(self):
        """Obtenir la conversation active actuelle."""
        return self.current_conversation
    
    def add_message_to_current(self, content, is_user=False):
        """
        Ajouter un message à la conversation actuelle.
        
        Args:
            content: Contenu du message
            is_user: Si le message vient de l'utilisateur
        
        Returns:
            Le message ajouté ou None s'il n'y a pas de conversation actuelle
        """
        if not self.current_conversation:
            # Créer une nouvelle conversation si aucune n'existe
            self.create_conversation()
        
        message = self.current_conversation.add_message(content, is_user)
        self.conversation_updated.emit(self.current_conversation)
        self._save_conversations()
        return message
    
    def rename_conversation(self, conv_id, new_title):
        """
        Renommer une conversation.
        
        Args:
            conv_id: ID de la conversation à renommer
            new_title: Nouveau titre pour la conversation
        
        Returns:
            True si la conversation a été trouvée et renommée, False sinon
        """
        for conv in self.conversations:
            if conv.id == conv_id:
                conv.title = new_title
                conv.updated_at = datetime.now()
                self.conversation_updated.emit(conv)
                self._save_conversations()
                return True
        return False
    
    def clear_all_conversations(self):
        """Effacer toutes les conversations."""
        confirm = True  # Dans une utilisation réelle, cela viendrait de la confirmation de l'utilisateur
        
        if confirm:
            self.conversations = []
            self.current_conversation = None
            
            # Sauvegarder la liste vide
            self._save_conversations()
            
            # Créer une nouvelle conversation vide
            self.create_conversation()
            
            return True
        return False
    
    def _save_conversations(self):
        """Sauvegarder toutes les conversations dans le stockage."""
        try:
            data = {
                'conversations': [conv.to_dict() for conv in self.conversations],
                'saved_at': datetime.now().isoformat()
            }
            
            filepath = os.path.join(self.storage_dir, 'conversations.json')
            
            # Créer le répertoire parent s'il n'existe pas
            os.makedirs(self.storage_dir, exist_ok=True)
            
            # Écrire dans le fichier
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Sauvegarder aussi une copie de secours
            backup_filepath = os.path.join(self.storage_dir, 'conversations_backup.json')
            with open(backup_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            self._log_error(f"Erreur lors de la sauvegarde des conversations : {str(e)}")
    
    def _load_conversations(self):
        """Charger les conversations depuis le stockage."""
        try:
            filepath = os.path.join(self.storage_dir, 'conversations.json')
            
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.conversations = []
                
                for conv_data in data.get('conversations', []):
                    conv = Conversation.from_dict(conv_data)
                    self.conversations.append(conv)
                    
                    # Définir la première conversation comme active si aucune n'est active
                    if conv.is_active and not self.current_conversation:
                        self.current_conversation = conv
                
                # Si aucune conversation n'existe, en créer une par défaut
                if not self.conversations:
                    self.create_conversation()
                else:
                    # Émettre le signal que les conversations ont été chargées
                    self.conversations_loaded.emit(self.conversations)
        
        except Exception as e:
            self._log_error(f"Erreur lors du chargement des conversations : {str(e)}")
            # Créer une conversation par défaut si le chargement échoue
            self.create_conversation()
    
    def export_conversation(self, conv_id, filepath=None):
        """
        Exporter une conversation vers un fichier.
        
        Args:
            conv_id: ID de la conversation à exporter
            filepath: Chemin vers lequel exporter (optionnel)
        
        Returns:
            Chemin vers le fichier exporté ou None en cas d'échec
        """
        conv = self.get_conversation(conv_id)
        if not conv:
            return None
        
        if not filepath:
            # Générer un chemin de fichier par défaut
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = conv.title.replace('/', '_').replace('\\', '_')
            filename = f"{safe_title}_{timestamp}.json"
            filepath = os.path.join(self.storage_dir, 'exports', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            data = {
                'conversation': conv.to_dict(),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return filepath
        
        except Exception as e:
            self._log_error(f"Erreur lors de l'export de la conversation : {str(e)}")
            return None
    
    def import_conversation(self, filepath):
        """
        Importer une conversation depuis un fichier.
        
        Args:
            filepath: Chemin vers le fichier à importer
        
        Returns:
            Objet Conversation ou None en cas d'échec de l'import
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conv_data = data.get('conversation', {})
            conv = Conversation.from_dict(conv_data)
            
            # Ajouter aux conversations
            conv.is_active = False
            self.conversations.append(conv)
            
            # Sauvegarder toutes les conversations
            self._save_conversations()
            
            return conv
        
        except Exception as e:
            self._log_error(f"Erreur lors de l'import de la conversation : {str(e)}")
            return None
    
    def _log_error(self, message):
        """Journaliser un message d'erreur."""
        try:
            from qgis.core import QgsMessageLog, Qgis
            message_log = QgsMessageLog.getInstance()
            if message_log:
                message_log.logMessage(
                    f"[QGIS AI Assistant Conversation Manager] {message}",
                    level=Qgis.Critical
                )
        except Exception:
            pass
    
    def tr(self, message):
        """Traduction d'un message."""
        return QCoreApplication.translate('ConversationManager', message)

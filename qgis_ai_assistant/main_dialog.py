"""
Dialogue principal pour l'Assistant IA QGIS.

Ce dialogue fournit l'interface de chat où les utilisateurs peuvent interagir avec l'IA.
"""

import os
import json
from datetime import datetime
from qgis.PyQt.QtCore import (
    Qt, QSize, pyqtSignal, QThread, QObject, QSettings, QCoreApplication
)
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QSplitter,
    QWidget, QScrollArea, QFrame, QMenu, QMessageBox,
    QComboBox, QToolButton, QSizePolicy, QTabWidget, QTabBar,
    QInputDialog, QFileDialog
)
from qgis.PyQt.QtGui import (
    QFont, QTextCursor, QTextCharFormat, QColor, 
    QIcon, QPalette, QTextOption
)
from qgis.core import QgsProject, QgsMapLayer
from .ai_engine import AIEngine
from .project_analyzer import ProjectAnalyzer
from .qgis_tools import QGISToolsExecutor
from .conversation_manager import ConversationManager


class ChatMessageWidget(QWidget):
    """Widget pour afficher un message de chat."""
    
    def __init__(self, message, is_user=False, timestamp=None, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()
        self.message = message
        
        # Set up layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Message content
        self.content_label = QLabel(message)
        self.content_label.setWordWrap(True)
        self.content_label.setTextFormat(Qt.TextFormat.RichText)
        
        # Set message styling based on sender
        if is_user:
            # User message styling
            self.content_label.setStyleSheet("""
                QLabel {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    padding: 10px;
                    border-radius: 15px;
                    margin: 0px;
                }
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            # AI message styling
            self.content_label.setStyleSheet("""
                QLabel {
                    background-color: #f5f5f5;
                    color: #424242;
                    padding: 10px;
                    border-radius: 15px;
                    margin: 0px;
                }
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Add timestamp
        timestamp_str = self.timestamp.strftime("%H:%M:%S")
        timestamp_label = QLabel(timestamp_str)
        timestamp_label.setStyleSheet("color: #9e9e9e; font-size: 10px;")
        
        # Vertical layout for content and timestamp
        v_layout = QVBoxLayout()
        v_layout.addWidget(self.content_label)
        v_layout.addWidget(timestamp_label)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_layout.setSpacing(2)
        v_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add to main layout
        layout.addLayout(v_layout)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)


class ChatArea(QScrollArea):
    """Zone de chat défilable pour les messages."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.addStretch()
        
        self.setWidget(self.content_widget)
        
        # Messages list
        self.messages = []
    
    def add_message(self, message, is_user=False, timestamp=None):
        """Ajouter un message au chat."""
        message_widget = ChatMessageWidget(message, is_user, timestamp)
        self.content_layout.insertWidget(
            self.content_layout.count() - 1, 
            message_widget
        )
        self.messages.append({
            'message': message,
            'is_user': is_user,
            'timestamp': timestamp or datetime.now(),
            'widget': message_widget
        })
        
        # Auto-scroll to bottom
        self.ensureVisible(0, self.widget().height(), 0, 0)
    
    def clear_messages(self):
        """Effacer tous les messages du chat."""
        # Remove all widgets except the stretch
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self.messages = []
    
    def load_conversation(self, conversation):
        """Charger une conversation existante."""
        self.clear_messages()
        
        for msg in conversation.messages:
            self.add_message(
                msg['content'],
                msg['is_user'],
                msg['timestamp']
            )


class ConversationTabWidget(QTabWidget):
    """Widget d'onglets pour gérer plusieurs conversations."""
    
    def __init__(self, conversation_manager, parent=None):
        super().__init__(parent)
        self.conversation_manager = conversation_manager
        self.tab_data = {}  # Map tab index to conversation ID
        
        # Custom tab bar for better styling
        self.setTabBar(ConversationTabBar(self))
        
        # Connect signals
        self.conversation_manager.conversation_created.connect(
            self._on_conversation_created
        )
        self.conversation_manager.conversation_switched.connect(
            self._on_conversation_switched
        )
        self.conversation_manager.conversation_deleted.connect(
            self._on_conversation_deleted
        )
        self.conversation_manager.conversation_updated.connect(
            self._on_conversation_updated
        )
        
        # Create initial tabs
        self._update_tabs()
        
        # Set tabs closable
        self.setTabsClosable(True)
        self.setMovable(True)
        
        # Connect tab signals
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_tab_changed)
    
    def _update_tabs(self):
        """Mettre à jour les onglets en fonction des conversations."""
        # Block signals to prevent multiple updates
        self.blockSignals(True)
        
        # Clear existing tabs
        self.clear()
        self.tab_data = {}
        
        # Create tabs for each conversation
        for i, conv in enumerate(self.conversation_manager.get_all_conversations()):
            self._add_tab_for_conversation(conv, i)
        
        # Set current tab based on active conversation
        if self.conversation_manager.current_conversation:
            for i, conv in enumerate(self.conversation_manager.get_all_conversations()):
                if conv.id == self.conversation_manager.current_conversation.id:
                    self.setCurrentIndex(i)
                    break
        
        self.blockSignals(False)
    
    def _add_tab_for_conversation(self, conv, index):
        """Ajouter un onglet pour une conversation."""
        # Create chat area for this conversation
        chat_area = ChatArea()
        
        # Load conversation messages
        chat_area.load_conversation(conv)
        
        # Add tab
        self.addTab(chat_area, conv.title)
        self.tab_data[index] = conv.id
        
        # Set tab tooltip
        self.setTabToolTip(index, f"Conversation: {conv.title}\nCréée: {conv.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    def _on_conversation_created(self, conv):
        """Handler pour la création d'une nouvelle conversation."""
        self._update_tabs()
        
        # Switch to the new conversation
        for i, c in enumerate(self.conversation_manager.get_all_conversations()):
            if c.id == conv.id:
                self.setCurrentIndex(i)
                break
    
    def _on_conversation_switched(self, conv):
        """Handler pour le changement de conversation."""
        # Update tabs
        self._update_tabs()
    
    def _on_conversation_deleted(self, conv_id):
        """Handler pour la suppression d'une conversation."""
        self._update_tabs()
    
    def _on_conversation_updated(self, conv):
        """Handler pour la mise à jour d'une conversation."""
        # Find the tab for this conversation and update it
        for i in range(self.count()):
            tab_conv_id = self.tab_data.get(i)
            if tab_conv_id == conv.id:
                # Update tab title if changed
                if self.tabText(i) != conv.title:
                    self.setTabText(i, conv.title)
                break
    
    def _on_tab_close_requested(self, index):
        """Handler pour la fermeture d'un onglet."""
        conv_id = self.tab_data.get(index)
        if conv_id:
            # Confirm deletion if it's not the only conversation
            if len(self.conversation_manager.get_all_conversations()) > 1:
                reply = QMessageBox.question(
                    self,
                    self.tr("Supprimer la conversation"),
                    self.tr("Voulez-vous vraiment supprimer cette conversation ?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.conversation_manager.delete_conversation(conv_id)
            else:
                # Just clear the conversation
                self.conversation_manager.clear_all_conversations()
    
    def _on_tab_changed(self, index):
        """Handler pour le changement d'onglet."""
        conv_id = self.tab_data.get(index)
        if conv_id:
            self.conversation_manager.switch_conversation(conv_id)
    
    def get_current_chat_area(self):
        """Obtenir la zone de chat de l'onglet actuel."""
        return self.currentWidget()
    
    def get_current_conversation_id(self):
        """Obtenir l'ID de la conversation actuelle."""
        return self.tab_data.get(self.currentIndex())
    
    def tr(self, message):
        """Traduction d'un message."""
        return QCoreApplication.translate('ConversationTabWidget', message)


class ConversationTabBar(QTabBar):
    """Barre d'onglets personnalisée pour les conversations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_tab_widget = parent
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, pos):
        """Afficher le menu contextuel."""
        tab_index = self.tabAt(pos)
        if tab_index < 0:
            return
        
        menu = QMenu(self)
        
        # Rename action
        rename_action = menu.addAction(self.tr("Renommer la conversation"))
        rename_action.triggered.connect(lambda: self._rename_tab(tab_index))
        
        # Export action
        export_action = menu.addAction(self.tr("Exporter la conversation"))
        export_action.triggered.connect(lambda: self._export_tab(tab_index))
        
        # Close action
        close_action = menu.addAction(self.tr("Fermer la conversation"))
        close_action.triggered.connect(lambda: self.parent_tab_widget._on_tab_close_requested(tab_index))
        
        # Show menu
        menu.exec_(self.viewport().mapToGlobal(pos))
    
    def _rename_tab(self, index):
        """Renommer un onglet."""
        conv_id = self.parent_tab_widget.tab_data.get(index)
        if conv_id:
            new_title, ok = QInputDialog.getText(
                self,
                self.tr("Renommer la conversation"),
                self.tr("Nouveau titre :"),
                text=self.parent_tab_widget.tabText(index)
            )
            if ok and new_title:
                self.parent_tab_widget.conversation_manager.rename_conversation(
                    conv_id, new_title
                )
    
    def _export_tab(self, index):
        """Exporter une conversation."""
        conv_id = self.parent_tab_widget.tab_data.get(index)
        if conv_id:
            # Get filepath for export
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Exporter la conversation"),
                "",
                self.tr("Fichiers JSON (*.json)")
            )
            
            if filepath:
                self.parent_tab_widget.conversation_manager.export_conversation(
                    conv_id, filepath
                )
                QMessageBox.information(
                    self,
                    self.tr("Export successful"),
                    self.tr("La conversation a été exportée avec succès.")
                )
    
    def tr(self, message):
        """Traduction d'un message."""
        return QCoreApplication.translate('ConversationTabBar', message)


class AIResponseWorker(QObject):
    """Thread worker pour la génération de réponses IA."""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    partial_response = pyqtSignal(str)
    
    def __init__(self, prompt, settings):
        super().__init__()
        self.prompt = prompt
        self.settings = settings
    
    def run(self):
        """Exécuter la génération de réponse IA."""
        try:
            # Initialize AI engine
            ai_engine = AIEngine(self.settings)
            
            # Get response from AI
            response = ai_engine.get_response(self.prompt)
            
            self.finished.emit(response)
            
        except Exception as e:
            self.error.emit(str(e))


class AIAssistantDialog(QDialog):
    """
    Dialogue principal pour l'Assistant IA QGIS.
    
    Ce dialogue fournit une interface de chat où les utilisateurs peuvent :
    - Envoyer des messages à l'IA
    - Recevoir des réponses de l'IA
    - Exécuter des outils QGIS via l'IA
    - Analyser le projet QGIS actuel
    - Gérer plusieurs conversations simultanément
    """
    
    def __init__(self, iface, settings, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.settings = settings
        self.project = QgsProject.instance()
        
        # Initialize components
        self.ai_engine = AIEngine(settings)
        self.project_analyzer = ProjectAnalyzer(iface)
        self.tools_executor = QGISToolsExecutor(iface)
        
        # Initialize conversation manager
        self.conversation_manager = ConversationManager(settings)
        
        # Setup UI
        self._setup_ui()
        self._setup_connections()
        
        # Worker thread
        self.worker_thread = None
        self.worker = None
        
        # Load window state
        self._load_window_state()
    
    def _setup_ui(self):
        """Configurer l'interface utilisateur."""
        self.setMinimumSize(900, 700)
        self.setWindowTitle(self.tr("Assistant IA QGIS"))
        self.setWindowIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'icon.svg'
            )
        ))
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Conversation tabs
        self.conversation_tabs = ConversationTabWidget(
            self.conversation_manager,
            parent=self
        )
        
        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.tr("Tapez votre message ici..."))
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_field.setMinimumHeight(40)
        
        # Send button
        self.send_button = QPushButton(self.tr("Envoyer"))
        self.send_button.setIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'send.svg'
            )
        ))
        self.send_button.setFixedSize(100, 40)
        
        # Action buttons
        self.new_conv_button = QPushButton(self.tr("Nouvelle conversation"))
        self.new_conv_button.setIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'tools.svg'
            )
        ))
        self.new_conv_button.setToolTip(self.tr("Créer une nouvelle conversation"))
        
        self.analyze_button = QPushButton(self.tr("Analyser le projet"))
        self.analyze_button.setIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'analyze.svg'
            )
        ))
        self.analyze_button.setToolTip(self.tr("Analyser le projet QGIS actuel"))
        
        self.tools_button = QPushButton(self.tr("Outils disponibles"))
        self.tools_button.setIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'tools.svg'
            )
        ))
        self.tools_button.setToolTip(self.tr("Afficher les outils QGIS disponibles"))
        
        self.clear_button = QPushButton(self.tr("Effacer"))
        self.clear_button.setIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'clear.svg'
            )
        ))
        self.clear_button.setToolTip(self.tr("Effacer l'historique de la conversation actuelle"))
        
        # Add widgets to input layout
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        # Action buttons layout
        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.new_conv_button)
        actions_layout.addWidget(self.analyze_button)
        actions_layout.addWidget(self.tools_button)
        actions_layout.addWidget(self.clear_button)
        actions_layout.addStretch()
        
        # Add to main layout
        main_layout.addWidget(self.conversation_tabs, 1)
        main_layout.addLayout(actions_layout)
        main_layout.addWidget(input_widget)
        
        # Add welcome message to current conversation
        self._add_welcome_message()
    
    def _add_welcome_message(self):
        """Ajouter un message de bienvenue."""
        if self.conversation_manager.current_conversation:
            welcome_msg = self.tr("""
            <h2>Bienvenue dans l'Assistant IA QGIS !</h2>
            <p>Je peux vous aider avec :</p>
            <ul>
                <li>Analyser votre projet QGIS</li>
                <li>Exécuter des outils et algorithmes de traitement QGIS</li>
                <li>Répondre à vos questions sur les SIG et QGIS</li>
                <li>Fournir des conseils sur l'analyse spatiales</li>
            </ul>
            <p><em>Tapez votre question ou demande ci-dessous, ou utilisez les boutons pour analyser votre projet ou voir les outils disponibles.</em></p>
            """)
            self.conversation_manager.add_message_to_current(welcome_msg, is_user=False)
    
    def _setup_connections(self):
        """Configurer les connexions des signaux."""
        self.send_button.clicked.connect(self._send_message)
        self.input_field.returnPressed.connect(self._send_message)
        self.analyze_button.clicked.connect(self._analyze_project)
        self.tools_button.clicked.connect(self._show_available_tools)
        self.clear_button.clicked.connect(self._clear_current_conversation)
        self.new_conv_button.clicked.connect(self._create_new_conversation)
        
        # Connect to conversation manager signals
        self.conversation_manager.conversation_switched.connect(
            self._on_conversation_switched
        )
        self.conversation_manager.conversation_updated.connect(
            self._update_current_chat_area
        )
    
    def _send_message(self):
        """Envoyer un message à l'IA."""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Clear input
        self.input_field.clear()
        
        # Add user message to current conversation
        self.conversation_manager.add_message_to_current(text, is_user=True)
        
        # Update chat area
        
        # Disable input while processing
        self._set_processing_state(True)
        
        # Create worker thread
        self._create_worker_thread(text)
    
    def _create_worker_thread(self, prompt):
        """Créer un thread worker pour la réponse IA."""
        # Clean up existing thread if any
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        # Create new worker
        self.worker = AIResponseWorker(prompt, self.settings)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.finished.connect(self._on_response_received)
        self.worker.error.connect(self._on_response_error)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.finished.connect(self._cleanup_worker)
        
        # Start thread
        self.worker_thread.start()
    
    def _on_response_received(self, response):
        """Gérer la réponse IA reçue."""
        # Add AI response to current conversation
        self.conversation_manager.add_message_to_current(response, is_user=False)
        
        # Update chat area
        
        # Enable input
        self._set_processing_state(False)
    
    def _on_response_error(self, error):
        """Gérer l'erreur de réponse IA."""
        error_msg = self.tr("Erreur : {}").format(error)
        self.conversation_manager.add_message_to_current(error_msg, is_user=False)
        
        # Update chat area
        
        # Enable input
        self._set_processing_state(False)
        
        # Show error message
        QMessageBox.critical(
            self,
            self.tr("Erreur de réponse IA"),
            self.tr("Une erreur est survenue lors de la réception de la réponse IA : {}").format(error)
        )
    
    def _cleanup_worker(self):
        """Nettoyer le thread worker."""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None
    
    def _set_processing_state(self, processing):
        """Définir l'état de traitement de l'UI."""
        self.input_field.setEnabled(not processing)
        self.send_button.setEnabled(not processing)
        self.analyze_button.setEnabled(not processing)
        self.tools_button.setEnabled(not processing)
        self.clear_button.setEnabled(not processing)
        
        if processing:
            self.send_button.setText(self.tr("Traitement..."))
        else:
            self.send_button.setText(self.tr("Envoyer"))
    
    def _analyze_project(self):
        """Analyser le projet QGIS actuel."""
        # Disable buttons while analyzing
        self._set_processing_state(True)
        self.analyze_button.setText(self.tr("Analyse en cours..."))
        
        try:
            # Get project analysis
            analysis = self.project_analyzer.analyze_project()
            
            # Format the analysis as a message
            analysis_msg = self._format_project_analysis(analysis)
            self.conversation_manager.add_message_to_current(analysis_msg, is_user=False)
            
            # Update chat area
            
        except Exception as e:
            error_msg = self.tr("Erreur lors de l'analyse du projet : {}").format(str(e))
            self.conversation_manager.add_message_to_current(error_msg, is_user=False)
        finally:
            self._set_processing_state(False)
            self.analyze_button.setText(self.tr("Analyser le projet"))
    
    def _show_available_tools(self):
        """Afficher les outils QGIS disponibles."""
        try:
            tools = self.tools_executor.get_available_tools()
            
            tools_msg = self.tr("<h3>Outils QGIS disponibles :</h3>")
            tools_msg += self.tr("<p>Les outils et algorithmes suivants sont disponibles :</p>")
            tools_msg += self.tr("<ul>")
            
            for category, category_tools in tools.items():
                tools_msg += self.tr(f"<li><strong>{category} :</strong>")
                tools_msg += self.tr("<ul>")
                
                for tool in category_tools[:5]:  # Show first 5 tools per category
                    tools_msg += self.tr(f"<li>{tool}</li>")
                
                if len(category_tools) > 5:
                    tools_msg += self.tr(f"<li><em>... et {len(category_tools) - 5} autres</em></li>")
                
                tools_msg += self.tr("</ul>")
                tools_msg += self.tr("</li>")
            
            tools_msg += self.tr("</ul>")
            tools_msg += self.tr("<p><em>Vous pouvez me demander d'exécuter des outils spécifiques par leur nom.</em></p>")
            
            self.conversation_manager.add_message_to_current(tools_msg, is_user=False)
            
        except Exception as e:
            error_msg = self.tr("Erreur lors de la récupération des outils disponibles : {}").format(str(e))
            self.conversation_manager.add_message_to_current(error_msg, is_user=False)
    
    def _clear_current_conversation(self):
        """Effacer la conversation actuelle."""
        confirm = QMessageBox.question(
            self,
            self.tr("Effacer la conversation"),
            self.tr("Êtes-vous sûr de vouloir effacer l'historique de cette conversation ?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            current_conv = self.conversation_manager.current_conversation
            if current_conv:
                current_conv.messages = []
                current_conv.updated_at = datetime.now()
                self.conversation_manager.conversation_updated.emit(current_conv)
                
                # Add welcome message again
                self._add_welcome_message()
    
    def _create_new_conversation(self):
        """Créer une nouvelle conversation."""
        title, ok = QInputDialog.getText(
            self,
            self.tr("Nouvelle conversation"),
            self.tr("Titre de la nouvelle conversation :")
        )
        
        if ok and title:
            self.conversation_manager.create_conversation(title)
        elif ok:  # User pressed OK but didn't enter title
            self.conversation_manager.create_conversation()
    
    def _on_conversation_switched(self, conv):
        """Gérer le changement de conversation."""
        self._update_current_chat_area()
    
    def _update_current_chat_area(self):
        """Mettre à jour la zone de chat actuelle."""
        # Get current chat area
        chat_area = self.conversation_tabs.get_current_chat_area()
        if chat_area:
            # Clear and reload current conversation
            chat_area.clear_messages()
            current_conv = self.conversation_manager.current_conversation
            if current_conv:
                chat_area.load_conversation(current_conv)
    
    def _format_project_analysis(self, analysis):
        """Formater l'analyse du projet pour l'affichage."""
        html = self.tr("<h3>Analyse du projet</h3>")
        
        html += self.tr("<h4>Informations sur le projet :</h4>")
        html += self.tr(f"<p><strong>Nom du projet :</strong> {analysis.get('project_name', 'Inconnu')}</p>")
        html += self.tr(f"<p><strong>Chemin du projet :</strong> {analysis.get('project_path', 'Non enregistré')}</p>")
        html += self.tr(f"<p><strong>SCR :</strong> {analysis.get('crs', 'Inconnu')}</p>")
        
        html += self.tr("<h4>Couches :</h4>")
        layers = analysis.get('layers', [])
        html += self.tr(f"<p><strong>Nombre total de couches :</strong> {len(layers)}</p>")
        
        if layers:
            html += self.tr("<table border='1' cellpadding='5' style='border-collapse: collapse;'>")
            html += self.tr("<tr><th>Nom de la couche</th><th>Type</th><th>SCR</th><th>Fonctionnalités/Géométrie</th></tr>")
            
            for layer in layers:
                layer_name = layer.get('name', 'Inconnu')
                layer_type = layer.get('type', 'Inconnu')
                layer_crs = layer.get('crs', 'Inconnu')
                layer_info = layer.get('info', '')
                
                html += self.tr(f"<tr><td>{layer_name}</td><td>{layer_type}</td><td>{layer_crs}</td><td>{layer_info}</td></tr>")
            
            html += self.tr("</table>")
        
        html += self.tr("<h4>Étendue du projet :</h4>")
        extent = analysis.get('extent', {})
        if extent:
            html += self.tr("<p>")
            html += self.tr(f"X Min : {extent.get('x_min', 'N/D')}, ")
            html += self.tr(f"Y Min : {extent.get('y_min', 'N/D')}<br/>")
            html += self.tr(f"X Max : {extent.get('x_max', 'N/D')}, ")
            html += self.tr(f"Y Max : {extent.get('y_max', 'N/D')}")
            html += self.tr("</p>")
        
        return html
    
    def _load_window_state(self):
        """Charger l'état de la fenêtre depuis les paramètres."""
        geometry = self.settings.value("assistant_dialog_geometry", None)
        if geometry and isinstance(geometry, (bytes, bytearray, memoryview)):
            self.restoreGeometry(geometry)
    
    def _save_window_state(self):
        """Sauvegarder l'état de la fenêtre dans les paramètres."""
        self.settings.setValue(
            "assistant_dialog_geometry",
            self.saveGeometry()
        )
    
    def closeEvent(self, event):
        """Gérer l'événement de fermeture."""
        self._save_window_state()
        
        # Clean up worker thread
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        # Save conversations
        self.conversation_manager._save_conversations()
        
        super().closeEvent(event)
    
    def tr(self, message):
        """Traduction d'un message."""
        return QCoreApplication.translate('AIAssistantDialog', message)

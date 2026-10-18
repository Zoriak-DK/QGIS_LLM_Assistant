"""
Dialogue de configuration pour l'Assistant IA QGIS.

Ce dialogue permet aux utilisateurs de configurer les paramètres de l'API :
- URL de l'API
- Clé API
- Modèle utilisé
"""

import os
from qgis.PyQt.QtCore import Qt, QCoreApplication, QSettings
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QFormLayout,
    QMessageBox, QGroupBox, QTextEdit, QCheckBox,
    QFrame, QSizePolicy
)
from qgis.PyQt.QtGui import QFont, QIcon, QDoubleValidator, QIntValidator
from .ai_engine import AIEngine


class AISettingsDialog(QDialog):
    """
    Dialogue de configuration des paramètres de l'API IA.
    
    Ce dialogue permet de configurer :
    - URL de l'API
    - Clé API
    - Modèle utilisé
    - Paramètres avancés
    """
    
    def __init__(self, iface, settings, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.settings = settings
        
        # Available models (can be extended)
        self.available_models = [
            {
                'id': 'gpt-4',
                'name': 'GPT-4',
                'provider': 'OpenAI',
                'description': 'Modèle le plus performant pour les tâches complexes'
            },
            {
                'id': 'gpt-3.5-turbo',
                'name': 'GPT-3.5 Turbo',
                'provider': 'OpenAI',
                'description': 'Modèle rapide et économique'
            },
            {
                'id': 'mistral-large',
                'name': 'Mistral Large',
                'provider': 'Mistral AI',
                'description': 'Alternative open-source avec de bonnes performances'
            },
            {
                'id': 'llama-3-70b',
                'name': 'Llama 3 70B',
                'provider': 'Meta',
                'description': 'Modèle open-source avancé'
            },
            {
                'id': 'claude-3-sonnet',
                'name': 'Claude 3 Sonnet',
                'provider': 'Anthropic',
                'description': 'Équilibre entre performance et vitesse'
            },
            {
                'id': 'claude-3-haiku',
                'name': 'Claude 3 Haiku',
                'provider': 'Anthropic',
                'description': 'Modèle rapide et efficace'
            },
            {
                'id': 'gemini-1.5-pro',
                'name': 'Gemini 1.5 Pro',
                'provider': 'Google',
                'description': 'Modèle multimodal avancé de Google'
            }
        ]
        
        # Setup UI
        self._setup_ui()
        self._load_settings()
        self._setup_connections()
    
    def _setup_ui(self):
        """Configurer l'interface utilisateur."""
        self.setMinimumSize(600, 400)
        self.setWindowIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'settings.svg'
            )
        ))
        
        self.setWindowTitle(self.tr("Paramètres de l'Assistant IA"))
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Configuration de l'API - Groupe
        api_group = QGroupBox(self.tr("Configuration de l'API"))
        api_layout = QFormLayout(api_group)
        api_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        api_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        api_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Champ URL de l'API
        self.api_url_label = QLabel(self.tr("URL de l'API :"))
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText(
            self.tr("https://api.openai.com/v1 ou https://api.mistral.ai/v1")
        )
        self.api_url_input.setToolTip(
            self.tr("URL de base pour le point de terminaison de l'API")
        )
        
        # Champ Clé API
        self.api_key_label = QLabel(self.tr("Clé API :"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText(self.tr("Entrez votre clé API"))
        self.api_key_input.setToolTip(
            self.tr("Votre clé API pour l'authentification")
        )
        
        # Case à cocher pour afficher la clé API
        self.show_api_key_checkbox = QCheckBox(self.tr("Afficher la clé API"))
        self.show_api_key_checkbox.setToolTip(
            self.tr("Cocher pour afficher/masquer la clé API")
        )
        
        # Sélection du modèle
        self.model_label = QLabel(self.tr("Modèle :"))
        self.model_combo = QComboBox()
        self.model_combo.setToolTip(
            self.tr("Sélectionnez le modèle IA à utiliser")
        )
        
        # Add models to combo box
        for model in self.available_models:
            model_text = f"{model['name']} ({model['provider']}) - {model['description']}"
            self.model_combo.addItem(model_text, model['id'])
        
        # Add fields to API layout
        api_layout.addRow(self.api_url_label, self.api_url_input)
        api_layout.addRow(self.api_key_label, self.api_key_input)
        api_layout.addRow(self.model_label, self.model_combo)
        
        # Add show key checkbox
        key_layout = QHBoxLayout()
        key_layout.addWidget(self.show_api_key_checkbox)
        key_layout.addStretch()
        api_layout.addRow("", key_layout)
        
        # Paramètres avancés - Groupe
        advanced_group = QGroupBox(self.tr("Paramètres avancés"))
        advanced_layout = QFormLayout(advanced_group)
        advanced_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        advanced_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        advanced_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Température
        self.temperature_label = QLabel(self.tr("Température :"))
        self.temperature_input = QLineEdit()
        self.temperature_input.setPlaceholderText("0.7")
        self.temperature_input.setToolTip(
            self.tr("Contrôle l'aléatoire dans les réponses IA (0.0 à 2.0)")
        )
        self.temperature_input.setValidator(
            self._create_double_validator(0.0, 2.0)
        )
        
        # Max tokens
        self.max_tokens_label = QLabel(self.tr("Tokens maximum :"))
        self.max_tokens_input = QLineEdit()
        self.max_tokens_input.setPlaceholderText("4096")
        self.max_tokens_input.setToolTip(
            self.tr("Nombre maximum de tokens dans la réponse")
        )
        self.max_tokens_input.setValidator(
            self._create_int_validator(1, 32768)
        )
        
        # Invite système
        self.system_prompt_label = QLabel(self.tr("Invite système :"))
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setPlaceholderText(
            self.tr("Vous êtes un assistant IA utile pour QGIS...")
        )
        self.system_prompt_input.setToolTip(
            self.tr("Invite système personnalisée pour guider le comportement de l'IA")
        )
        self.system_prompt_input.setMaximumHeight(100)
        
        # Add advanced fields
        advanced_layout.addRow(self.temperature_label, self.temperature_input)
        advanced_layout.addRow(self.max_tokens_label, self.max_tokens_input)
        advanced_layout.addRow(self.system_prompt_label, self.system_prompt_input)
        
        # Bouton Tester la connexion
        self.test_connection_button = QPushButton(
            self.tr("Tester la connexion")
        )
        self.test_connection_button.setIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'test.svg'
            )
        ))
        self.test_connection_button.setToolTip(
            self.tr("Tester la connexion à l'API avec les paramètres actuels")
        )
        
        # Bouton Sauvegarder
        self.save_button = QPushButton(self.tr("Sauvegarder les paramètres"))
        self.save_button.setIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'save.svg'
            )
        ))
        self.save_button.setToolTip(
            self.tr("Sauvegarder les paramètres actuels")
        )
        
        # Bouton Annuler
        self.cancel_button = QPushButton(self.tr("Annuler"))
        self.cancel_button.setIcon(QIcon(
            os.path.join(
                os.path.dirname(__file__), 
                'icons', 
                'cancel.svg'
            )
        ))
        self.cancel_button.setToolTip(
            self.tr("Annuler et fermer la fenêtre")
        )
        
        # Layout des boutons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.test_connection_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        # Add groups to main layout
        main_layout.addWidget(api_group)
        main_layout.addWidget(advanced_group)
        main_layout.addLayout(button_layout)
        
        # Label de statut
        self.status_label = QLabel()
        self.status_label.setTextFormat(Qt.TextFormat.RichText)
        self.status_label.setStyleSheet("color: #666;")
        main_layout.addWidget(self.status_label)
    
    def _setup_connections(self):
        """Configurer les connexions des signaux."""
        self.show_api_key_checkbox.stateChanged.connect(
            self._toggle_api_key_visibility
        )
        self.test_connection_button.clicked.connect(
            self._test_connection
        )
        self.save_button.clicked.connect(self._save_settings)
        self.cancel_button.clicked.connect(self.close)
    
    def _create_double_validator(self, minimum, maximum):
        """Créer un validateur pour les valeurs décimales."""
        validator = QDoubleValidator()
        validator.setRange(minimum, maximum, 2)  # 2 décimales
        return validator
    
    def _create_int_validator(self, minimum, maximum):
        """Créer un validateur pour les valeurs entières."""
        validator = QIntValidator()
        validator.setRange(minimum, maximum)
        return validator
    
    def _toggle_api_key_visibility(self, state):
        """Basculer la visibilité de la clé API."""
        if state == Qt.CheckState.Checked:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _load_settings(self):
        """Charger les paramètres depuis l'objet settings."""
        # Charger les paramètres de l'API
        api_url = self.settings.value("api_url", "https://api.openai.com/v1")
        api_key = self.settings.value("api_key", "")
        model_id = self.settings.value("model_id", "gpt-3.5-turbo")
        
        self.api_url_input.setText(api_url)
        self.api_key_input.setText(api_key)
        
        # Trouver et sélectionner le modèle
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == model_id:
                self.model_combo.setCurrentIndex(i)
                break
        
        # Charger les paramètres avancés
        temperature = self.settings.value("temperature", 0.7)
        max_tokens = self.settings.value("max_tokens", 4096)
        system_prompt = self.settings.value(
            "system_prompt",
            self.tr("Vous êtes un assistant IA utile pour QGIS. Vous pouvez analyser des projets QGIS, exécuter des outils, et répondre à des questions sur les SIG et l'analyse géospatiale. Fournissez toujours des réponses utiles, précises et claires.")
        )
        
        self.temperature_input.setText(str(temperature))
        self.max_tokens_input.setText(str(max_tokens))
        self.system_prompt_input.setText(system_prompt)
        
        # Mettre à jour le statut
        self._update_status_message()
    
    def _save_settings(self):
        """Sauvegarder les paramètres dans l'objet settings."""
        # Sauvegarder les paramètres de l'API
        self.settings.setValue("api_url", self.api_url_input.text())
        self.settings.setValue("api_key", self.api_key_input.text())
        self.settings.setValue(
            "model_id",
            self.model_combo.currentData()
        )
        
        # Sauvegarder les paramètres avancés
        try:
            temperature = float(self.temperature_input.text() or "0.7")
            self.settings.setValue("temperature", temperature)
        except ValueError:
            self.settings.setValue("temperature", 0.7)
        
        try:
            max_tokens = int(self.max_tokens_input.text() or "4096")
            self.settings.setValue("max_tokens", max_tokens)
        except ValueError:
            self.settings.setValue("max_tokens", 4096)
        
        self.settings.setValue("system_prompt", self.system_prompt_input.toPlainText())
        
        # Synchroniser les paramètres
        self.settings.sync()
        
        # Afficher le message de succès
        self._show_status_message(
            self.tr("Paramètres sauvegardés avec succès !"),
            "success"
        )
        
        # Fermer le dialogue après un court délai
        self._close_after_delay(1000)
    
    def _test_connection(self):
        """Tester la connexion à l'API."""
        self._show_status_message(
            self.tr("Test de connexion en cours..."),
            "info"
        )
        
        # Récupérer les paramètres actuels
        api_url = self.api_url_input.text()
        api_key = self.api_key_input.text()
        model_id = self.model_combo.currentData()
        
        # Créer un objet settings temporaire
        test_settings = QSettings("QGIS_AI_Assistant", "Settings")
        test_settings.setValue("api_url", api_url)
        test_settings.setValue("api_key", api_key)
        test_settings.setValue("model_id", model_id)
        
        try:
            # Créer le moteur IA et tester la connexion
            ai_engine = AIEngine(test_settings)
            test_prompt = self.tr("Dis 'test réussi'")
            response = ai_engine.get_response(test_prompt)
            
            if "test réussi" in response.lower() or "test successful" in response.lower():
                self._show_status_message(
                    self.tr("Test de connexion réussi !"),
                    "success"
                )
            else:
                self._show_status_message(
                    self.tr("Test de connexion échoué. Réponse inattendue : {}").format(
                        response[:100]
                    ),
                    "error"
                )
        
        except Exception as e:
            self._show_status_message(
                self.tr("Test de connexion échoué : {}").format(str(e)),
                "error"
            )
        
        finally:
            # Nettoyer
            del test_settings
    
    def _show_status_message(self, message, message_type="info"):
        """Afficher un message de statut."""
        colors = {
            "success": "#4caf50",
            "error": "#f44336",
            "info": "#2196f3"
        }
        color = colors.get(message_type, "#666")
        
        self.status_label.setText(
            f'<span style="color: {color};">{message}</span>'
        )
    
    def _update_status_message(self):
        """Mettre à jour le message de statut en fonction des paramètres actuels."""
        if self.api_url_input.text() and self.api_key_input.text():
            self._show_status_message(
                self.tr("Paramètres configurés. Prêt à se connecter."),
                "info"
            )
        else:
            self._show_status_message(
                self.tr("Veuillez configurer l'URL de l'API et la clé API."),
                "info"
            )
    
    def _close_after_delay(self, delay_ms):
        """Fermer le dialogue après un délai."""
        from qgis.PyQt.QtCore import QTimer
        QTimer.singleShot(delay_ms, self.close)
    
    def closeEvent(self, event):
        """Gérer l'événement de fermeture."""
        # Sauvegarder l'état de la fenêtre
        self.settings.setValue(
            "settings_dialog_geometry",
            self.saveGeometry()
        )
        
        super().closeEvent(event)
    
    def tr(self, message):
        """Traduction d'un message."""
        return QCoreApplication.translate('AISettingsDialog', message)

"""
Moteur IA pour l'Assistant IA QGIS.

Ce module gère toute la fonctionnalité liée à l'IA, y compris :
- La communication avec l'API des fournisseurs LLM
- La génération de réponses
- L'ingénierie des invites pour les tâches spécifiques à QGIS
"""

import json
import requests
from datetime import datetime
from qgis.PyQt.QtCore import QSettings, QCoreApplication
from qgis.core import QgsProject, QgsMessageLog, Qgis


class AIEngine:
    """
    Moteur IA pour communiquer avec les API LLM.
    
    Prend en charge plusieurs fournisseurs, notamment :
    - OpenAI
    - Mistral AI
    - Anthropic (Claude)
    - Google (Gemini)
    - Points de terminaison personnalisés
    """
    
    def __init__(self, settings):
        """
        Initialiser le moteur IA.
        
        Args:
            settings: Objet QSettings avec la configuration.
        """
        self.settings = settings
        self._load_settings()
        
        # Configurer la journalisation des messages
        try:
            self.message_log = QgsMessageLog.getInstance()
        except Exception:
            # Solution de repli pour les versions de QGIS où getInstance() n'est pas disponible
            self.message_log = None
    
    def _load_settings(self):
        """Charger les paramètres depuis l'objet settings."""
        self.api_url = self.settings.value("api_url", "https://api.openai.com/v1")
        self.api_key = self.settings.value("api_key", "")
        self.model_id = self.settings.value("model_id", "gpt-3.5-turbo")
        self.temperature = float(
            self.settings.value("temperature", 0.7)
        )
        self.max_tokens = int(
            self.settings.value("max_tokens", 4096)
        )
        self.system_prompt = self.settings.value(
            "system_prompt",
            "Vous êtes un assistant IA utile pour QGIS. Vous pouvez analyser des projets QGIS, "
            "exécuter des outils, et répondre à des questions sur les SIG et l'analyse géospatiale. "
            "Fournissez toujours des réponses utiles, précises et claires."
        )
        
        # Déterminer le fournisseur à partir de l'URL de l'API ou de l'ID du modèle
        self.provider = self._determine_provider()
    
    def _determine_provider(self):
        """Déterminer le fournisseur IA en fonction de l'URL de l'API ou de l'ID du modèle."""
        # Vérifier pour Mistral AI
        if "mistral" in self.api_url.lower() or "mistral" in self.model_id.lower():
            return "mistral"
        
        # Vérifier pour Anthropic (Claude)
        if "anthropic" in self.api_url.lower() or "claude" in self.model_id.lower():
            return "anthropic"
        
        # Vérifier pour Google (Gemini)
        if "google" in self.api_url.lower() or "gemini" in self.model_id.lower():
            return "google"
        
        # Vérifier les points de terminaison personnalisés
        if "api/v1" not in self.api_url.lower():
            return "custom"
        
        # Par défaut, OpenAI
        return "openai"
    
    def _get_endpoint(self):
        """Obtenir le point de terminaison de l'API en fonction du fournisseur."""
        if self.provider == "openai":
            return f"{self.api_url}/chat/completions"
        elif self.provider == "mistral":
            return f"{self.api_url}/chat/completions"
        elif self.provider == "anthropic":
            return f"{self.api_url}/messages"
        elif self.provider == "google":
            return f"{self.api_url}/models/{self.model_id}:generateContent"
        else:
            # Point de terminaison personnalisé - suppose qu'il s'agit d'un point de terminaison chat/completions
            return f"{self.api_url}/chat/completions"
    
    def _get_headers(self):
        """Obtenir les en-têtes pour la requête API."""
        headers = {
            "Content-Type": "application/json",
        }
        
        # Ajouter l'en-tête d'autorisation
        if self.provider in ["openai", "mistral"]:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == "anthropic":
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["x-api-key"] = self.api_key
        elif self.provider == "google":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            # Point de terminaison personnalisé
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _prepare_openai_payload(self, prompt):
        """Préparer la charge utile pour les API OpenAI et Mistral."""
        return {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def _prepare_anthropic_payload(self, prompt):
        """Préparer la charge utile pour l'API Anthropic (Claude)."""
        return {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": f"{self.system_prompt}\n\n{prompt}"
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
    
    def _prepare_google_payload(self, prompt):
        """Préparer la charge utile pour l'API Google (Gemini)."""
        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{self.system_prompt}\n\n{prompt}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            }
        }
    
    def _prepare_custom_payload(self, prompt):
        """Préparer la charge utile pour les points de terminaison personnalisés."""
        # Essayez le format OpenAI en premier
        return self._prepare_openai_payload(prompt)
    
    def _extract_openai_response(self, response_data):
        """Extraire le texte de réponse du format OpenAI/Mistral."""
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return str(response_data)
    
    def _extract_anthropic_response(self, response_data):
        """Extraire le texte de réponse du format Anthropic."""
        try:
            return response_data["content"][0]["text"]
        except (KeyError, IndexError):
            return str(response_data)
    
    def _extract_google_response(self, response_data):
        """Extraire le texte de réponse du format Google."""
        try:
            return response_data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return str(response_data)
    
    def _make_api_request(self, payload):
        """
        Effectuer la requête API vers le fournisseur LLM.
        
        Args:
            payload: La charge utile de la requête.
        
        Returns:
            Le texte de réponse de l'IA.
        
        Raises:
            Exception: Si la requête API échoue.
        """
        endpoint = self._get_endpoint()
        headers = self._get_headers()
        
        try:
            # Journaliser la requête
            self._log_message(
                f"Effectuer une requête API vers {endpoint}",
                level=Qgis.Info
            )
            
            # Effectuer la requête
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=120  # Délai d'attente de 120 secondes
            )
            
            # Vérifier les erreurs
            response.raise_for_status()
            
            # Analyser la réponse
            response_data = response.json()
            
            # Journaliser la réponse
            self._log_message(
                f"Réponse API reçue",
                level=Qgis.Info
            )
            
            # Extraire et retourner le texte de réponse
            if self.provider in ["openai", "mistral", "custom"]:
                return self._extract_openai_response(response_data)
            elif self.provider == "anthropic":
                return self._extract_anthropic_response(response_data)
            elif self.provider == "google":
                return self._extract_google_response(response_data)
            else:
                return str(response_data)
        
        except requests.exceptions.Timeout:
            self._log_message(
                "La requête API a expiré",
                level=Qgis.Critical
            )
            raise Exception(self.tr("La requête API a expiré. Veuillez réessayer."))
        
        except requests.exceptions.RequestException as e:
            self._log_message(
                f"La requête API a échoué : {str(e)}",
                level=Qgis.Critical
            )
            raise Exception(self.tr("La requête API a échoué : {}").format(str(e)))
        
        except json.JSONDecodeError as e:
            self._log_message(
                f"Réponse JSON invalide : {str(e)}",
                level=Qgis.Critical
            )
            raise Exception(self.tr("Réponse JSON invalide de l'API : {}").format(str(e)))
        
        except Exception as e:
            self._log_message(
                f"Erreur inattendue : {str(e)}",
                level=Qgis.Critical
            )
            raise Exception(self.tr("Erreur inattendue : {}").format(str(e)))
    
    def get_response(self, prompt):
        """
        Obtenir une réponse de l'IA pour l'invite donnée.
        
        Args:
            prompt: L'invite ou la question de l'utilisateur.
        
        Returns:
            La réponse de l'IA sous forme de chaîne de caractères.
        
        Raises:
            Exception: Si la requête API échoue ou si les paramètres sont invalides.
        """
        # Vérifier les paramètres requis
        if not self.api_key:
            raise Exception(
                self.tr("La clé API n'est pas configurée. Veuillez la définir dans les paramètres.")
            )
        
        if not self.api_url:
            raise Exception(
                self.tr("L'URL de l'API n'est pas configurée. Veuillez la définir dans les paramètres.")
            )
        
        # Journaliser l'invite
        self._log_message(f"Traitement de l'invite : {prompt[:100]}...")
        
        # Préparer la charge utile en fonction du fournisseur
        if self.provider in ["openai", "mistral", "custom"]:
            payload = self._prepare_openai_payload(prompt)
        elif self.provider == "anthropic":
            payload = self._prepare_anthropic_payload(prompt)
        elif self.provider == "google":
            payload = self._prepare_google_payload(prompt)
        else:
            payload = self._prepare_custom_payload(prompt)
        
        # Effectuer la requête API
        try:
            response = self._make_api_request(payload)
            
            # Journaliser la réponse
            self._log_message(f"Réponse IA : {response[:100]}...")
            
            return response
        
        except Exception as e:
            # Journaliser l'erreur
            self._log_message(
                f"Erreur lors de l'obtention de la réponse IA : {str(e)}",
                level=Qgis.Critical
            )
            raise
    
    def _log_message(self, message, level=Qgis.Info):
        """
        Journaliser un message dans le journal QGIS.
        
        Args:
            message: Le message à journaliser.
            level: Le niveau de journalisation (Qgis.Info, Qgis.Warning, Qgis.Critical).
        """
        try:
            if self.message_log:
                self.message_log.logMessage(
                    f"[QGIS AI Assistant] {message}",
                    level=level
                )
        except Exception:
            # Si la journalisation échoue, simplement l'ignorer
            pass
    
    def tr(self, message):
        """Traduction d'un message."""
        return QCoreApplication.translate('AIEngine', message)


class AIResponseProcessor:
    """
    Processeur pour gérer les réponses IA et extraire des informations actionnables.
    """
    
    def __init__(self):
        """Initialiser le processeur de réponses."""
        pass
    
    def extract_tool_calls(self, response):
        """
        Extraire les appels d'outils de la réponse IA.
        
        Args:
            response: Le texte de réponse IA.
        
        Returns:
            Liste des appels d'outils extraits.
        """
        # ceci est un espace réservé pour une extraction plus sophistiquée des appels d'outils
        # Dans une implémentation complète, cela analyserait les appels d'outils structurés
        # de la réponse IA
        
        tool_calls = []
        
        # Rechercher des modèles communs
        if "execute tool:" in response.lower():
            # Extraire le nom de l'outil et les paramètres
            parts = response.split("execute tool:", 1)
            if len(parts) > 1:
                tool_info = parts[1].split("\n", 1)[0]
                tool_calls.append({
                    'tool': tool_info,
                    'parameters': {}
                })
        
        return tool_calls
    
    def extract_qgis_commands(self, response):
        """
        Extraire les commandes spécifiques à QGIS de la réponse.
        
        Args:
            response: Le texte de réponse IA.
        
        Returns:
            Liste des commandes QGIS extraites.
        """
        commands = []
        
        # Rechercher les mentions d'outils QGIS
        qgis_tools = [
            "buffer", "intersection", "clip", "merge", "dissolve",
            "reproject", "export", "import", "calculate", "select"
        ]
        
        for tool in qgis_tools:
            if tool.lower() in response.lower():
                commands.append({
                    'command': tool,
                    'context': response
                })
        
        return commands
    
    def format_project_analysis(self, project_info):
        """
        Formater les informations d'analyse de projet pour l'IA.
        
        Args:
            project_info: Dictionnaire avec les informations du projet.
        
        Returns:
            Chaîne formatée avec les informations du projet.
        """
        formatted = "Analyse du projet QGIS:\n\n"
        
        formatted += f"Nom du projet : {project_info.get('name', 'Inconnu')}\n"
        formatted += f"Chemin du projet : {project_info.get('path', 'Non enregistré')}\n"
        formatted += f"SCR : {project_info.get('crs', 'Inconnu')}\n\n"
        
        layers = project_info.get('layers', [])
        formatted += f"Couches ({len(layers)}):\n"
        
        for layer in layers:
            formatted += f"  - {layer.get('name', 'Inconnu')} "
            formatted += f"({layer.get('type', 'Inconnu')}) "
            formatted += f"[{layer.get('feature_count', 'N/D')} fonctionnalités]\n"
        
        formatted += f"\nÉtendue du projet:\n"
        extent = project_info.get('extent', {})
        formatted += f"  X : {extent.get('x_min', 'N/D')} à {extent.get('x_max', 'N/D')}\n"
        formatted += f"  Y : {extent.get('y_min', 'N/D')} à {extent.get('y_max', 'N/D')}\n"
        
        return formatted

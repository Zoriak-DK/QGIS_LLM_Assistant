"""
Client HTTP pour l'Assistant IA QGIS.

Ce module fournit des fonctionnalités de client HTTP avec :
- Gestion des délais d'attente
- Logique de nouvelle tentative
- Gestion des erreurs
- Options de vérification SSL
"""

import requests
import time
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsMessageLog, Qgis


class HTTPClient:
    """
    Client HTTP avec support des nouvelles tentatives et des délais d'attente.
    """
    
    DEFAULT_TIMEOUT = 120  # 120 secondes
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # 1 seconde
    
    def __init__(self, timeout=None, max_retries=None, retry_delay=None):
        """
        Initialiser le client HTTP.
        
        Args:
            timeout: Délai d'attente de la connexion en secondes.
            max_retries: Nombre maximum de nouvelles tentatives pour les requêtes échouées.
            retry_delay: Délai entre les nouvelles tentatives en secondes.
        """
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES
        self.retry_delay = retry_delay or self.RETRY_DELAY
        
        # Journal des messages pour le débogage
        try:
            self.message_log = QgsMessageLog.getInstance()
        except Exception:
            self.message_log = None
    
    def request(self, method, url, **kwargs):
        """
        Effectuer une requête HTTP avec support des nouvelles tentatives.
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE, etc.)
            url: L'URL à requêter.
            **kwargs: Arguments supplémentaires pour requests.request().
        
        Returns:
            Objet requests.Response.
        
        Raises:
            requests.exceptions.RequestException: Si toutes les nouvelles tentatives échouent.
        """
        retries = 0
        last_exception = None
        
        while retries <= self.max_retries:
            try:
                # Effectuer la requête
                response = requests.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Vérifier une réponse réussie
                if response.status_code < 500:
                    return response
                
                # Erreur du serveur, nouvelle tentative
                last_exception = Exception(
                    f"Erreur serveur {response.status_code}: {response.reason}"
                )
                self._log_message(
                    f"Requête échouée avec le statut {response.status_code}, "
                    f"nouvelle tentative {retries + 1}/{self.max_retries}"
                )
            
            except requests.exceptions.Timeout:
                last_exception = requests.exceptions.Timeout(
                    f"Délai d'attente de la requête dépassé après {self.timeout} secondes"
                )
                self._log_message(
                    f"Délai d'attente dépassé, nouvelle tentative {retries + 1}/{self.max_retries}"
                )
            
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self._log_message(
                    f"Erreur de connexion: {str(e)}, nouvelle tentative {retries + 1}/{self.max_retries}"
                )
            
            except requests.exceptions.RequestException as e:
                last_exception = e
                self._log_message(
                    f"Exception de requête: {str(e)}, nouvelle tentative {retries + 1}/{self.max_retries}"
                )
            
            # Incrémenter le compteur de nouvelles tentatives
            retries += 1
            
            # Attendre avant de réessayer
            if retries <= self.max_retries:
                time.sleep(self.retry_delay)
        
        # Toutes les nouvelles tentatives ont échoué
        raise last_exception
    
    def get(self, url, **kwargs):
        """Effectuer une requête GET."""
        return self.request('GET', url, **kwargs)
    
    def post(self, url, **kwargs):
        """Effectuer une requête POST."""
        return self.request('POST', url, **kwargs)
    
    def put(self, url, **kwargs):
        """Effectuer une requête PUT."""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url, **kwargs):
        """Effectuer une requête DELETE."""
        return self.request('DELETE', url, **kwargs)
    
    def patch(self, url, **kwargs):
        """Effectuer une requête PATCH."""
        return self.request('PATCH', url, **kwargs)
    
    def get_json(self, url, **kwargs):
        """
        Effectuer une requête GET et analyser la réponse en JSON.
        
        Args:
            url: L'URL à requêter.
            **kwargs: Arguments supplémentaires.
        
        Returns:
            Données JSON analysées.
        
        Raises:
            requests.exceptions.RequestException: Si la requête échoue.
            ValueError: Si la réponse ne peut pas être analysée en JSON.
        """
        response = self.get(url, **kwargs)
        return response.json()
    
    def post_json(self, url, data=None, json=None, **kwargs):
        """
        Effectuer une requête POST avec des données JSON.
        
        Args:
            url: L'URL à requêter.
            data: Données de formulaire (mutuellement exclusif avec json).
            json: Données JSON (mutuellement exclusif avec data).
            **kwargs: Arguments supplémentaires.
        
        Returns:
            Objet requests.Response.
        
        Raises:
            requests.exceptions.RequestException: Si la requête échoue.
        """
        kwargs.setdefault('headers', {})
        kwargs['headers']['Content-Type'] = 'application/json'
        return self.post(url, data=data, json=json, **kwargs)
    
    def get_json_with_retry(self, url, max_retries=None, **kwargs):
        """
        Effectuer une requête GET avec réponse JSON et logique de nouvelle tentative.
        
        Args:
            url: L'URL à requêter.
            max_retries: Nouvelles tentatives maximales (remplace le défaut de l'instance).
            **kwargs: Arguments supplémentaires.
        
        Returns:
            Données JSON analysées.
        """
        if max_retries is not None:
            original_retries = self.max_retries
            self.max_retries = max_retries
        
        try:
            return self.get_json(url, **kwargs)
        finally:
            if max_retries is not None:
                self.max_retries = original_retries
    
    def _log_message(self, message, level=Qgis.Info):
        """Journaliser un message dans le journal QGIS."""
        try:
            if self.message_log:
                self.message_log.logMessage(
                    f"[QGIS AI Assistant HTTP] {message}",
                    level=level
                )
        except Exception:
            pass
    
    def tr(self, message):
        """Traduction d'un message."""
        return QCoreApplication.translate('HTTPClient', message)


class StreamingHTTPClient(HTTPClient):
    """
    Client HTTP avec support des réponses en streaming.
    """
    
    def __init__(self, **kwargs):
        """Initialiser le client HTTP en streaming."""
        super().__init__(**kwargs)
    
    def post_streaming(self, url, data=None, json=None, **kwargs):
        """
        Effectuer une requête POST avec réponse en streaming.
        
        Args:
            url: L'URL à requêter.
            data: Données de formulaire.
            json: Données JSON.
            **kwargs: Arguments supplémentaires.
        
        Returns:
            Objet requests.Response avec streaming activé.
        """
        kwargs.setdefault('headers', {})
        kwargs['headers']['Content-Type'] = 'application/json'
        kwargs['stream'] = True
        
        return self.post(url, data=data, json=json, **kwargs)
    
    def get_streaming(self, url, **kwargs):
        """
        Effectuer une requête GET avec réponse en streaming.
        
        Args:
            url: L'URL à requêter.
            **kwargs: Arguments supplémentaires.
        
        Returns:
            Objet requests.Response avec streaming activé.
        """
        kwargs['stream'] = True
        return self.get(url, **kwargs)
    
    def read_stream_chunk(self, response, chunk_size=1024):
        """
        Lire un bloc d'une réponse en streaming.
        
        Args:
            response: L'objet de réponse en streaming.
            chunk_size: Taille du bloc à lire.
        
        Returns:
            Le prochain bloc de données, ou None s'il n'y a plus de données.
        """
        try:
            return response.raw.read(chunk_size)
        except Exception:
            return None

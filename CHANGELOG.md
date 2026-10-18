# Journal des modifications

Toutes les modifications notables du plugin Assistant IA QGIS seront documentées dans ce fichier.

## [1.0.0] - 2026-10-16

### Ajouté
- Version initiale du plugin Assistant IA QGIS
- Interface de chat pour interagir avec les modèles IA
- Fonctionnalité d'analyse de projet
- Capacités d'exécution d'outils QGIS
- Dialogue des paramètres pour la configuration de l'API
- Support de plusieurs fournisseurs d'IA (OpenAI, Mistral AI, Anthropic, Google)
- Support des points de terminaison personnalisés

### Exigences
- **QGIS** : 4.2 ou supérieur (testé avec QGIS 4.2)
- **Python** : 3.9 ou supérieur
- **requests** : 2.25.0 ou supérieur

### Notes de compatibilité
- Conçu spécifiquement pour QGIS 4.2
- Utilise l'API Processing Framework de QGIS 4.2
- Compatible avec PyQt6 (utilisé dans QGIS 4.x)

## [Non publié]

### Modifications
- Mise à jour de metadata.txt pour spécifier QGIS 4.2 comme version minimale
- Ajout de la vérification de version dans l'initialisation du plugin
- Amélioration de la gestion des erreurs pour QgsMessageLog
- Amélioration du calcul de l'étendue du projet pour l'API QGIS 4.x
- Mise à jour de l'intégration Processing Framework pour QGIS 4.x

### Corrigé
- Compatibilité avec les algorithmes Processing de QGIS 4.2
- Accès à l'étendue de l'arbre des couches dans QGIS 4.x
- Initialisation de QSettings pour QGIS 4.2

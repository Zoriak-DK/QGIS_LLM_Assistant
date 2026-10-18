# Assistant IA QGIS (pour QGIS 4.2+)

Un plugin **Assistant IA pour QGIS** qui peut analyser des projets, exécuter des outils et répondre aux questions des utilisateurs.

> **Note**: Ce plugin est conçu spécifiquement pour QGIS 4.2 et peut ne pas fonctionner avec les versions antérieures.

## 🌟 Fonctionnalités

- **💬 Interface de chat en français**: Interagissez avec l'IA via une interface conviviale entièrement traduite en français
- **📊 Analyse du projet**: Analyse automatique de votre projet QGIS (couches, SCR, étendue, etc.)
- **🔧 Exécution d'outils**: Exécutez des outils et algorithmes de traitement QGIS via des commandes IA
- **⚙️ Configuration des paramètres**: Configurez l'URL de l'API, la clé API et le modèle dans les paramètres
- **🌐 Multi-fournisseurs**: Support de plusieurs fournisseurs d'IA (OpenAI, Mistral AI, Anthropic, Google)
- **💾 Gestion de l'historique**: Conservation de l'historique des conversations
- **📑 Conversations multiples**: Créez et gérez plusieurs conversations simultanément avec des onglets
- **💾 Sauvegarde automatique**: Les conversations sont automatiquement sauvegardées et restaurées

## 📋 Fonctionnalités avancées

### Gestion des conversations
- **Onglets multiples**: Basculer facilement entre plusieurs conversations
- **Historique persistant**: Les conversations sont sauvegardées entre les sessions
- **Renommer les conversations**: Personnalisez les titres des conversations
- **Exporter/Importer**: Partagez vos conversations en les exportant/important
- **Effacer les conversations**: Supprimez les conversations individuelles ou effacez toutes les conversations

### Interface utilisateur
- **Message de bienvenue**: Guide l'utilisateur lors de la première utilisation
- **Messages formatés**: Affichage clair des messages utilisateur et IA
- **Horodatages**: Chaque message est horodaté
- **Boutons d'action rapides**: Analyser le projet, voir les outils disponibles, créer de nouvelles conversations

## 📥 Installation

### Méthode 1: Utilisation du Gestionnaire de plugins QGIS (Recommandé)

1. Ouvrez QGIS
2. Allez dans **Plugins > Gérer et installer des plugins**
3. Cliquez sur **Installer depuis un fichier ZIP**
4. Sélectionnez le fichier ZIP du plugin
5. Cliquez sur **Installer le plugin**

### Méthode 2: Installation manuelle

1. Fermez QGIS s'il est ouvert
2. Copiez le dossier `qgis_ai_assistant` dans votre répertoire de plugins QGIS :
   - **Windows**: `C:\Users\<VotreUtilisateur>\AppData\Roaming\QGIS\QGIS4\profiles\default\python\plugins\`
   - **Linux**: `~/.local/share/QGIS/QGIS4/profiles/default/python/plugins/`
   - **macOS**: `/Users/<VotreUtilisateur>/Library/Application Support/QGIS/QGIS4/profiles/default/python/plugins/`
3. Redémarrez QGIS
4. Activez le plugin dans **Plugins > Gérer et installer des plugins**

### Télécharger le ZIP depuis GitHub Actions

À chaque push ou pull request, GitHub Actions construit le ZIP installable du plugin. Pour le récupérer :

1. Ouvrez l'onglet **Actions** du dépôt et sélectionnez la dernière exécution réussie de **Build QGIS plugin ZIP**
2. Téléchargez l'artefact `Assistant_IA_QGIS_v<version>`
3. Installez le fichier ZIP téléchargé depuis le gestionnaire de plugins QGIS

## 🚀 Utilisation

### Ouvrir l'Assistant IA

1. Après l'installation, démarrez QGIS
2. Recherchez le menu **Assistant IA** dans la barre de menus
3. Cliquez sur **Ouvrir l'Assistant IA** pour lancer l'interface de chat

### Configurer les paramètres de l'API

Avant d'utiliser l'assistant IA, vous devez configurer vos paramètres API :

1. Cliquez sur **Paramètres de l'Assistant IA** dans le menu Assistant IA
2. Entrez les informations suivantes :
   - **URL de l'API**: L'URL de base du point de terminaison de votre fournisseur d'IA (ex. : `https://api.openai.com/v1` pour OpenAI)
   - **Clé API**: Votre clé API du fournisseur
   - **Modèle**: Sélectionnez le modèle que vous souhaitez utiliser
3. Optionnellement, configurez les paramètres avancés :
   - **Température**: Contrôle l'aléatoire dans les réponses (0.0 à 2.0)
   - **Tokens maximum**: Nombre maximum de tokens dans la réponse
   - **Invite système**: Invite système personnalisée pour guider le comportement de l'IA
4. Cliquez sur **Tester la connexion** pour vérifier vos paramètres
5. Cliquez sur **Sauvegarder les paramètres** pour enregistrer votre configuration

### Utiliser l'Assistant IA

1. **Tapez votre question ou demande** dans le champ de saisie en bas
2. **Appuyez sur Entrée ou cliquez sur Envoyer** pour envoyer votre message
3. L'IA répondra avec :
   - Des réponses à vos questions
   - Une analyse de votre projet
   - L'exécution d'outils QGIS lorsque demandé

### Gérer les conversations

- **Nouvelle conversation**: Cliquez sur le bouton "Nouvelle conversation" ou utilisez le menu contextuel
- **Changer de conversation**: Cliquez sur l'onglet de la conversation souhaitée
- **Renommer une conversation**: Faites un clic droit sur l'onglet et sélectionnez "Renommer la conversation"
- **Exporter une conversation**: Faites un clic droit sur l'onglet et sélectionnez "Exporter la conversation"
- **Fermer une conversation**: Faites un clic droit sur l'onglet et sélectionnez "Fermer la conversation", ou cliquez sur la croix de l'onglet
- **Effacer une conversation**: Utilisez le bouton "Effacer" pour vider la conversation actuelle

### Commandes disponibles

Vous pouvez demander à l'IA d'effectuer diverses tâches :

- **Analyse du projet**: "Analyse mon projet", "Dis-moi quelles sont mes couches", "Quel est le SCR de mon projet ?"
- **Exécution d'outils**: "Crée un tampon de 100m", "Découpe la couche A avec la couche B", "Calcule les statistiques"
- **Questions générales**: "Comment faire X dans QGIS ?", "Quelle est la différence entre Y et Z ?"

### Utiliser les boutons

- **Nouvelle conversation**: Crée une nouvelle conversation vierge
- **Analyser le projet**: Analyse automatiquement le projet QGIS actuel
- **Outils disponibles**: Affiche une liste des outils de traitement QGIS disponibles
- **Effacer**: Efface l'historique de la conversation actuelle
- **Envoyer**: Envoyez votre message à l'IA

## 🤖 Fournisseurs d'IA supportés

Le plugin supporte plusieurs fournisseurs d'IA :

### OpenAI
- **URL de l'API**: `https://api.openai.com/v1`
- **Modèles**: GPT-4, GPT-3.5 Turbo
- **Clé API**: Obtenez-la depuis le [Tableau de bord OpenAI](https://platform.openai.com/account/api-keys)

### Mistral AI
- **URL de l'API**: `https://api.mistral.ai/v1`
- **Modèles**: Mistral Large, Mistral Small
- **Clé API**: Obtenez-la depuis le [Tableau de bord Mistral AI](https://console.mistral.ai/)

### Anthropic (Claude)
- **URL de l'API**: `https://api.anthropic.com/v1`
- **Modèles**: Claude 3 Sonnet, Claude 3 Haiku
- **Clé API**: Obtenez-la depuis le [Tableau de bord Anthropic](https://console.anthropic.com/)

### Google (Gemini)
- **URL de l'API**: `https://generativelanguage.googleapis.com/v1`
- **Modèles**: Gemini 1.5 Pro
- **Clé API**: Obtenez-la depuis la [Console Cloud Google](https://console.cloud.google.com/)

### Points de terminaison personnalisés
Vous pouvez également utiliser des points de terminaison personnalisés qui implémentent le format d'API compatible avec OpenAI.

## ⚙️ Options de configuration

Les options de configuration suivantes sont disponibles dans les paramètres :

| Option | Description | Valeur par défaut |
|--------|-------------|-----------------|
| URL de l'API | URL de base pour le point de terminaison de l'API | `https://api.openai.com/v1` |
| Clé API | Votre clé API pour l'authentification | (vide) |
| Modèle | Le modèle IA à utiliser | `gpt-3.5-turbo` |
| Température | Contrôle l'aléatoire (0.0-2.0) | 0.7 |
| Tokens maximum | Nombre maximum de tokens dans la réponse | 4096 |
| Invite système | Invite système personnalisée | Invite par défaut |

## 📋 Stockage et sécurité

### Stockage des conversations
- Les conversations sont automatiquement sauvegardées dans un fichier JSON
- Par défaut, elles sont stockées dans :
  - `~/.qgis_ai_assistant/conversations/` (Linux/macOS)
  - `%USERPROFILE%\.qgis_ai_assistant\conversations\` (Windows)
- Vous pouvez exporter manuellement des conversations vers des fichiers individuels

### Sécurité
- **Clés API**: Les clés API sont stockées localement dans les paramètres QGIS. Soyez prudent et ne partagez pas vos fichiers de configuration QGIS.
- **Données**: Vos invites et les réponses de l'IA sont envoyées au fournisseur d'IA. N'incluez pas de données sensibles dans vos invites.
- **Réseau**: Toute la communication se fait par HTTPS (en supposant que vous utilisez des URL d'API HTTPS).

## 🛠️ Exigences

- **QGIS**: Version 4.2 ou supérieure (testé avec QGIS 4.2)
- **Python**: 3.9 ou supérieur (inclus avec QGIS)
- **requests**: Bibliothèque Python pour les requêtes HTTP (généralement incluse avec QGIS)
- **Connexion Internet**: Requise pour communiquer avec les API d'IA

## 🐛 Dépannage

### Problèmes de connexion

1. **Clé API invalide**: Vérifiez que votre clé API est correcte
2. **URL de l'API incorrecte**: Vérifiez l'URL de l'API pour votre fournisseur
3. **Problèmes réseau**: Assurez-vous d'avoir une connexion Internet active
4. **Pare-feu/Proxy**: Si vous êtes derrière un proxy, configurez les paramètres du proxy de votre système

### Problèmes de performance

1. **Réponses lentes**: Essayez de réduire le paramètre Tokens maximum
2. **Erreurs de délai d'attente**: Augmentez le délai d'attente dans les paramètres ou essayez avec une requête plus petite
3. **Limitation du débit**: Si vous obtenez des erreurs de limitation du débit, attendez et réessayez

### Problèmes de plugin

1. **Plugin non chargé**: Assurez-vous que le nom du dossier est exactement `qgis_ai_assistant`
2. **Dépendances manquantes**: Vérifiez que toutes les bibliothèques Python requises sont disponibles
3. **Problèmes de permissions**: Sur Linux/macOS, assurez-vous d'avoir les permissions de fichiers appropriées

## 📝 Historique des versions

### Version 1.0.0 (2026-10-16)
- Version initiale
- Interface de chat de base
- Analyse de projet
- Exécution d'outils
- Support de plusieurs fournisseurs d'IA
- Configuration des paramètres
- **NOUVEAU**: Interface complètement traduite en français
- **NOUVEAU**: Gestion de l'historique des conversations
- **NOUVEAU**: Support des conversations multiples avec onglets
- **NOUVEAU**: Sauvegarde automatique des conversations
- **NOUVEAU**: Export/Import de conversations

---

**Note**: Il s'agit d'un plugin communautaire et il n'est pas officiellement supporté par le projet QGIS.

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez suivre ces étapes :

1. Forker le dépôt
2. Créer une branche de fonctionnalité
3. Effectuer vos modifications
4. Tester soigneusement
5. Soumettre une pull request

## 📄 Licence

Ce plugin est publié sous la licence GNU General Public License (GPL) version 3 ou supérieure.

## 🆘 Support

Pour le support, veuillez :

1. Consulter la page [Problèmes](https://github.com/Zoriak-DK/QGIS_LLM_Assistant/issues) pour les problèmes connus
2. Créer un nouveau problème si votre problème n'est pas déjà signalé
3. Inclure autant de détails que possible (version de QGIS, étapes pour reproduire, messages d'erreur)

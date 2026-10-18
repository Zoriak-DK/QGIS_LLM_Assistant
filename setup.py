#!/usr/bin/env python
"""
Script d'installation pour le plugin Assistant IA QGIS

Ce script peut être utilisé pour :
- Construire un package distribuable
- Installer le plugin pour le développement
"""

import os
import sys
from setuptools import setup, find_packages

# Métadonnées du plugin
NAME = "Assistant IA QGIS"
VERSION = "1.0.0"
DESCRIPTION = "Un assistant IA pour QGIS qui peut analyser des projets, exécuter des outils et répondre aux questions des utilisateurs"
AUTHOR = "Équipe Assistant IA QGIS"
AUTHOR_EMAIL = "support@qgis-ai-assistant.example.com"
URL = "https://github.com/Zoriak-DK/QGIS_LLM_Assistant"
LICENSE = "GPLv3"

# Classifieurs
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering :: GIS",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Framework :: QGIS",
]

# Données du package
PACKAGE_DATA = {
    "qgis_ai_assistant": [
        "metadata.txt",
        "icons/*.svg",
        "resources/*",
    ],
}

# Paquets requis
INSTALL_REQUIRES = [
    "requests>=2.25.0",
]


def read_me():
    """Lire le fichier README."""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return DESCRIPTION


def get_package_dir():
    """Obtenir le répertoire du package."""
    return os.path.dirname(os.path.abspath(__file__))


# Configuration de l'installation
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=read_me(),
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license=LICENSE,
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    package_data=PACKAGE_DATA,
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    python_requires=">=3.9",
    qgis_minimum_version="4.2",
    zip_safe=False,
    entry_points={
        "qgis.plugins": [
            f"{NAME.lower().replace(' ', '_')} = qgis_ai_assistant:classFactory",
        ],
    },
)

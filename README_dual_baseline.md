# Traitement GNSS - Deux Lignes de Base

## Vue d'ensemble

Ce module implémente le traitement complet de deux lignes de base GNSS en parallèle avec RTKLIB, suivi de la préparation des données pour les calculs d'attitude. Le système est intégré avec la gestion de projet existante pour éviter les recalculs inutiles.

## Fonctionnalités

### 1. Traitement RTKLIB en parallèle
- **Deux lignes de base simultanées** : Base-Port et Base-Stbd
- **Barre de progression globale** avec suivi en temps réel
- **Diagrammes circulaires** pour la qualité des données
- **Monitoring individuel** de chaque ligne de base

### 2. Préparation des données
- **Chargement des fichiers .pos** RTKLIB
- **Filtrage par qualité** (seuil configurable)
- **Synchronisation avec données Octans** (optionnelle)
- **Reconstruction des positions ENH** absolues
- **Calcul d'attitude** par analyse Procrustes
- **Analyse des biais géométriques** théoriques

### 3. Gestion de projet
- **Cache de traitement** pour éviter les recalculs
- **Persistance des résultats** dans le projet
- **Vérification automatique** des étapes terminées
- **Sauvegarde automatique** des métadonnées

## Architecture

### Composants principaux

1. **`DualBaselineProcessor`** : Processeur principal pour les deux lignes de base
2. **`BaselineProcessor`** : Processeur individuel pour une ligne de base
3. **`DataPreparationWorker`** : Worker pour la préparation des données
4. **`DualBaselineIntegrationWidget`** : Interface utilisateur intégrée

### Fichiers créés

- `src/core/calculations/dual_baseline_processor.py` : Processeur RTKLIB
- `src/core/calculations/data_preparation.py` : Préparation des données
- `src/app/gui/dual_baseline_integration.py` : Interface d'intégration
- `test_dual_baseline_integration.py` : Script de test

## Utilisation

### 1. Via l'interface d'intégration

```python
from src.app.gui.dual_baseline_integration import DualBaselineIntegrationWidget
from src.core.project_manager import ProjectManager

# Créer les gestionnaires
project_manager = ProjectManager.instance()

# Créer le widget d'intégration
widget = DualBaselineIntegrationWidget(project_manager)
widget.show()
```

### 2. Via les composants individuels

```python
from src.core.calculations.dual_baseline_processor import DualBaselineConfig, DualBaselineProcessor

# Configuration
config = DualBaselineConfig(project_manager)
config.set_project_paths(project_data)

# Processeur
processor = DualBaselineProcessor(config)
processor.start()
```

### 3. Test d'intégration

```bash
python test_dual_baseline_integration.py
```

## Configuration

### Structure du projet

Le système utilise la structure de projet existante avec les sections suivantes :

```json
{
  "gnss_config": {
    "metadata": {
      "rinex_files": {
        "files_by_position": {
          "base": {"obs": "path", "nav": "path", "gnav": "path"},
          "rover1": {"obs": "path", "nav": "path", "gnav": "path"},
          "rover2": {"obs": "path", "nav": "path", "gnav": "path"}
        }
      }
    },
    "processing_cache": {
      "rtk_processing": {
        "completed": false,
        "output_files": {},
        "quality_stats": {}
      },
      "data_preparation": {
        "completed": false,
        "attitudes_count": 0,
        "geometric_biases": {}
      }
    }
  }
}
```

### Paramètres configurables

- **Seuil de qualité** : Filtrage des points par écart-type 3D (défaut: 0.1m)
- **Géométrie du bateau** : Positions relatives des antennes GPS
- **Tolérance de synchronisation** : Pour la fusion avec les données Octans
- **Chemins RTKLIB** : Exécutable et fichiers de configuration

## Workflow

### Étape 1 : Traitement RTKLIB
1. Vérification des fichiers d'entrée
2. Lancement des deux processeurs en parallèle
3. Monitoring de la progression et qualité
4. Sauvegarde des résultats dans le cache

### Étape 2 : Préparation des données
1. Chargement des fichiers .pos générés
2. Filtrage par qualité
3. Synchronisation avec données Octans (si disponibles)
4. Reconstruction des positions absolues
5. Calcul d'attitude par Procrustes
6. Analyse des biais géométriques

### Étape 3 : Sauvegarde
1. Mise à jour du cache de projet
2. Persistance des métadonnées
3. Marquage des étapes comme terminées

## Intégration avec l'existant

### ProjectManager
- Nouvelles méthodes pour la gestion du cache
- Vérification des étapes terminées
- Sauvegarde automatique des résultats

### ProgressManager
- Suivi de la progression globale
- Validation des étapes du workflow
- Notifications de completion

### Interface utilisateur
- Onglets pour les différentes étapes
- Barres de progression détaillées
- Affichage des résultats en temps réel
- Gestion des erreurs et logs

## Avantages

1. **Performance** : Traitement parallèle des deux lignes de base
2. **Robustesse** : Gestion d'erreurs et validation des fichiers
3. **Persistance** : Évite les recalculs inutiles
4. **Flexibilité** : Configuration adaptable selon le projet
5. **Monitoring** : Suivi en temps réel avec diagrammes
6. **Intégration** : Compatible avec l'architecture existante

## Dépendances

- PyQt5 pour l'interface utilisateur
- pandas et numpy pour le traitement des données
- RTKLIB pour les calculs GNSS
- Modules existants du projet (ProjectManager, ProgressManager)

## Notes techniques

- Le traitement RTKLIB s'exécute dans des threads séparés
- Les diagrammes circulaires utilisent QPainter pour le rendu
- Le cache est sauvegardé automatiquement dans le projet
- La géométrie du bateau est configurable par projet
- Les biais géométriques sont calculés par la méthode du tilt du plan

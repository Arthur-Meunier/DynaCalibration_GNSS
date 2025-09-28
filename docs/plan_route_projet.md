# Plan de Route - Application de Calibration des Capteurs

## 📋 État Actuel et Objectifs
L'application dispose déjà de 5 pages fonctionnelles (Accueil, Dimcon, GNSS, Observation, Résultats). Le plan ci-dessous détaille les améliorations et nouvelles fonctionnalités à implémenter.

---

## 🏠 **PAGE ACCUEIL - Améliorations**

### Fonctionnalités de Gestion de Projet
- [ ] **Choix initial** : Nouveau projet vs Charger un projet existant
- [ ] **Informations projet** :
  - Nom de la compagnie
  - Nom du bateau
  - Nom de l'ingénieur responsable du traitement
- [ ] **Texte de description** du projet
- [ ] **Menu Options** (accessible depuis toute l'application) :
  - Modification des paramètres projet
  - Gestion du token EarthData
  - Configuration générale

### Architecture Fichier Projet (JSON)
- [ ] **Structure projet hybride** :
  - `projet.json` principal (métadonnées, chemins, stats)
  - Dossiers séparés pour gros volumes (`data/`, `reports/`, `logs/`)
- [ ] **Classe ProjectManager** pour gestion centralisée
- [ ] **Sauvegarde automatique** à chaque étape de validation
- [ ] **Système de versioning** des projets
- [ ] **Extension custom** (.calibration) pour identification
- [ ] **Validation schéma JSON** pour intégrité des données

### Système de Rapport QC
- [ ] **Log centralisé** qui compile les informations essentielles de chaque étape
- [ ] **Historique des opérations** dans le fichier projet
- [ ] **Rapport de contrôle qualité** automatique
- [ ] **Export** du rapport selon template prédéfini

---

## 🔧 **PAGE DIMCON - Améliorations**

### Interface Utilisateur
- [ ] **Bouton toggle** : Afficher/masquer le bateau dans la vue 3D
- [ ] **Gestion optimisée** de l'affichage des points DIMCON
- [ ] **Fenêtre flottante** pour saisie des coordonnées (plus esthétique)
- [ ] **Amélioration visuelle** de l'interface de saisie

### Intégration Fichier Projet
- [ ] **Sauvegarde automatique** des points DIMCON validés dans projet.json
- [ ] **Indicateur visuel** de l'état de validation (sauvegardé/modifié)

---

## 🛰️ **PAGE GNSS - Refonte Complète de la Logique**

### Nouvelle Approche Basée Projet
- [ ] **Référencement par chemin projet** (fini les imports manuels isolés)
- [ ] **Chargement des chemins** depuis projet.json
- [ ] **Case à cocher par défaut** : "Utilisation SP3" 
  - Message explicatif sur l'impact temps de calcul
- [ ] **Sélection de fichiers structurée** :
  - Choix du répertoire contenant les fichiers
  - Sélection des 2 rovers + station de base
  - Fichiers .o25 pour chaque point
  - Bouton "Valider" la sélection
  - **Sauvegarde des chemins** dans projet.json

### Traitement SP3 Automatisé
- [ ] **Moulinette SP3** :
  - Vérification et récupération automatique des fichiers SP3
  - Téléchargement des fichiers CLK
  - Récupération des fichiers .n et .g depuis la base
  - **Indicateur visuel** : Roue qui tourne en haut à gauche du menu
  - **Validation visuelle** : Émoji ✅ quand terminé
- [ ] **Stockage métadonnées SP3** dans projet.json (URLs, dates, statut)

### Inspection des Données (Pendant les Téléchargements)
- [ ] **Multitâche non-bloquant** : Interface reste responsive pendant SP3
- [ ] **Intégration rtkplot** pour inspection des données :
  - Visualisation des fichiers .obs disponibles
  - Analyse de la qualité des observations
  - Détection des interruptions de signal
  - Graphiques SNR, multipath, cycle slips
- [ ] **Onglet d'inspection** temporaire pendant les téléchargements
- [ ] **Pré-analyse des données** : 
  - Durée de session
  - Nombre de satellites
  - Qualité globale des observations

### Interface de Calcul en Temps Réel
- [ ] **Masquage de la latence** pendant récupération SP3/CLK
- [ ] **Affichage qualité préliminaire** avec rtkpost
- [ ] **Détection des sauts de cycles**
- [ ] **Zone "Calcul en cours"** (masquée par défaut) :
  - Deux barres de progression (une par ligne de base)
  - Suivi en temps réel : défilement des heures + indicateur Q=
  - Positionnée en haut à gauche
- [ ] **Logs de traitement** en temps réel dans processing.log

### Logique de Traitement et Sauvegarde
- [ ] **Sans SP3** : Calculs lancés immédiatement
- [ ] **Avec SP3** : Attente des fichiers puis lancement automatique
- [ ] **Continuité workflow** : Possibilité de passer à l'étape suivante pendant les calculs
- [ ] **Sauvegarde automatique statistiques GNSS** :
  - Pourcentages Q1, Q2, Q5
  - RMS horizontal/vertical
  - Temps de traitement
  - Longueur ligne de base
- [ ] **État de traitement** persistant dans projet.json

---

## 📊 **PAGE OBSERVATION - Restructuration**

### Interface Simplifiée
- [ ] **Suppression onglet** en bas à droite (inutile)
- [ ] **Suppression section** "conventions d'angle" (bas gauche)
- [ ] **Fonctionnalité renommage** des capteurs dans le tableau

### Workflow de Traitement et Persistance
- [ ] **Configuration** : Nombre de capteurs → Création tableau automatique
- [ ] **Configuration capteurs** : Conventions de signe + Import
- [ ] **Sauvegarde config capteurs** dans projet.json :
  - Conventions de signe par capteur
  - Chemins des fichiers importés
  - Noms personnalisés des capteurs
  - Métadonnées d'import (nombre de points, colonnes)
- [ ] **Bouton "Lancer les traitements"** centralisé
- [ ] **Gestion des dépendances** :
  - Si calcul GNSS terminé → Lancement immédiat du 1er capteur
  - Sinon → Mise en attente
  - Autres capteurs en liste d'attente (onglet gauche)

### Suivi des Traitements et Résultats
- [ ] **Barre de progression** pour chaque traitement
- [ ] **Création automatique** du rapport formaté avec template
- [ ] **Queue de traitement** visible
- [ ] **Sauvegarde statistiques traitements** :
  - Statistiques d'alignement données (écarts temporels, gaps)
  - Statistiques de filtrage (points supprimés, outliers)
  - Résultats calibration (matrices rotation, C-O mean/std)
  - Scores de qualité par capteur
- [ ] **Logs détaillés** de chaque étape de traitement

---

## 📈 **PAGE RÉSULTATS - Interface Simplifiée**

### Organisation en 3 Zones Principales
- [ ] **Zone Gauche** - Sélecteur de Données :
  - Arbre hiérarchique : GNSS / Capteurs MRU / Capteurs Compas / Capteurs Octans
  - Indicateurs de statut (✅ traité, ⏳ en cours, ❌ erreur)
  - Métriques de qualité en un coup d'œil (score global)

- [ ] **Zone Centrale** - Visualisation Dynamique :
  - Graphiques interactifs selon la sélection
  - GNSS → Trajectoires ENH, precision plots, sky plots
  - Capteurs → Séries temporelles, histogrammes C-O, matrices de rotation
  - **Onglets contextuels** : Données / Graphiques / Statistiques

- [ ] **Zone Droite** - Actions et Export :
  - Panneau d'actions selon l'élément sélectionné
  - Boutons export ciblés (PNG, CSV, JSON)
  - **Bouton "Rapport Complet"** → Lance la page QC

### Navigation Simplifiée
- [ ] **Un clic = Un affichage** : Éviter les menus déroulants complexes
- [ ] **Breadcrumb** : Indication claire de ce qui est affiché
- [ ] **Raccourcis clavier** : Navigation rapide entre éléments

---

## 📋 **NOUVELLE PAGE QC (Contrôle Qualité)**

### Vue d'Ensemble Executive
- [ ] **Dashboard principal** avec métriques clés :
  - Score global du projet (0-100)
  - Statut par phase (DIMCON ✅, GNSS ✅, Capteurs ⏳)
  - Alertes et recommandations automatiques

### Section GNSS - Analyse Détaillée
- [ ] **Métriques de qualité** :
  - Pourcentages Q1/Q2/Q5 avec graphiques circulaires
  - RMS horizontal/vertical avec seuils colorés
  - Analyse de l'en-tête .pos (configuration respectée)
  - Détection automatique des anomalies

- [ ] **Visualisations spécialisées** :
  - Carte de précision 2D (heat map)
  - Évolution temporelle de la précision
  - Distribution des erreurs (histogrammes)
  - Skyplot avec masques d'élévation

### Section Capteurs - Synthèse par Type
- [ ] **Tableau de bord capteurs** :
  - Grille avec tous les capteurs et leurs métriques
  - Codes couleur pour qualité (Vert/Orange/Rouge)
  - Tri et filtrage par performance

- [ ] **Analyses comparatives** :
  - Comparaison inter-capteurs (même type)
  - Détection des capteurs aberrants
  - Recommandations de filtrage/exclusion

### Rapport Final Automatisé
- [ ] **Génération intelligente** :
  - Template adaptatif selon les données disponibles
  - Inclusion automatique des graphiques pertinents
  - Commentaires auto-générés selon les seuils
  - Export PDF professionnel avec logo/en-tête

- [ ] **Personnalisation** :
  - Sélection des sections à inclure
  - Niveau de détail (Exécutif / Technique / Complet)
  - Ajout de commentaires manuels

---

## 🎯 **MENU VERTICAL - Ajout Page QC**

### Nouvelle Structure à 6 Pages
- [ ] **Accueil** : Gestion projet et informations générales
- [ ] **Dimcon** : Configuration des points de référence
- [ ] **GNSS** : Traitement des données satellite
- [ ] **Observation** : Import et traitement capteurs
- [ ] **Résultats** : Visualisation et analyse des données *(simplifiée)*
- [ ] **QC** : Contrôle qualité et rapport final *(nouveau)*

### Logique de Navigation
- [ ] **Résultats** = Exploration interactive des données
- [ ] **QC** = Validation, métriques et rapport final
- [ ] **Workflow naturel** : Les utilisateurs finissent par la QC

---

## 🔄 **Architecture Générale - Améliorations**

### Gestion des États et Persistance
- [ ] **State management** amélioré pour les calculs en arrière-plan
- [ ] **Synchronisation** entre les différentes pages via projet.json
- [ ] **Auto-sauvegarde** à intervalles réguliers
- [ ] **Détection de modifications** non sauvegardées
- [ ] **Système de backup** automatique (copies horodatées)
- [ ] **Récupération après crash** basée sur dernière sauvegarde

### Classe ProjectManager Centrale
- [ ] **Singleton pattern** pour accès global aux données projet
- [ ] **API unifiée** pour lecture/écriture dans projet.json
- [ ] **Validation automatique** des données (schéma JSON)
- [ ] **Gestion des chemins relatifs** pour portabilité
- [ ] **Migration automatique** entre versions de format
- [ ] **Compression optionnelle** pour gros projets

### Interface Utilisateur
- [ ] **Feedback visuel** permanent sur l'état des traitements
- [ ] **Indicateur "projet modifié"** dans la barre de titre
- [ ] **Messages d'erreur** contextuels et informatifs
- [ ] **Aide contextuelle** pour chaque section
- [ ] **Barre de statut** avec informations projet courantes

### Performance et Optimisation
- [ ] **Calculs asynchrones** pour maintenir la réactivité
- [ ] **Cache intelligent** des résultats intermédiaires
- [ ] **Chargement paresseux** des gros datasets
- [ ] **Optimisation** des affichages graphiques
- [ ] **Nettoyage automatique** des fichiers temporaires

---

## 📅 **Priorités de Développement**

### Phase 1 - Fondations et Architecture JSON
1. **Classe ProjectManager** et structure hybride
2. Gestion de projet (Accueil) avec création/chargement
3. Menu Options et configuration globale
4. Système de logs/rapport QC intégré au JSON
5. **Validation et sauvegarde automatique** à chaque étape

### Phase 2 - GNSS avec Persistance
1. Refonte logique fichiers basée projet
2. Intégration SP3 avec métadonnées dans JSON
3. Interface temps réel avec logs de progression
4. **Sauvegarde automatique** des statistiques GNSS

### Phase 3 - Observation et Traitement
1. Simplification interface et configuration capteurs
2. Workflow de traitement avec queue management
3. **Persistance complète** des résultats dans JSON
4. Gestion des états de traitement entre sessions

### Phase 4 - Résultats et QC
1. **Page Résultats** simplifiée avec interface 3 zones
2. **Nouvelle page QC** avec dashboard et métriques
3. Visualisations avancées avec chargement paresseux
4. **Export/rapport final** avec templates configurables
5. Archive complète du projet

### Phase 5 - Polish et Robustesse
1. Optimisations performance avec cache intelligent
2. Interface utilisateur finale avec indicateurs d'état
3. **Système de backup** et récupération après crash
4. Documentation et tests complets
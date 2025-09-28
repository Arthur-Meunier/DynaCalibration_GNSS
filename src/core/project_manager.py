# src/core/project_manager.py

import os
import json
import shutil
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
import jsonschema
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Ajouter ceci:
try:
    from simple_sp3_checker import SimpleSP3Checker
except ImportError:
    SimpleSP3Checker = None
    logger.warning("SimpleSP3Checker non disponible")
@dataclass
class ProjectMetadata:
    """Métadonnées d'un projet de calibration"""
    version: str = "1.0"
    created: str = ""
    last_modified: str = ""
    company: str = ""
    vessel: str = ""
    engineer: str = ""
    description: str = ""
    
    def __post_init__(self):
        if not self.created:
            self.created = datetime.now(timezone.utc).isoformat()
        self.last_modified = datetime.now(timezone.utc).isoformat()

@dataclass
class ProjectStructure:
    """Structure des répertoires du projet"""
    base_path: str = ""
    data_dir: str = "data"
    reports_dir: str = "reports"
    logs_dir: str = "logs"
    cache_dir: str = "cache"
    backup_dir: str = "backups"
    
    def get_full_paths(self, base_path: str) -> Dict[str, Path]:
        """Retourne les chemins complets des répertoires"""
        base = Path(base_path)
        return {
            'base': base,
            'data': base / self.data_dir,
            'reports': base / self.reports_dir,
            'logs': base / self.logs_dir,
            'cache': base / self.cache_dir,
            'backup': base / self.backup_dir
        }

@dataclass
class WorkflowStatus:
    """État d'avancement du workflow"""
    dimcon: Dict[str, Any] = field(default_factory=lambda: {"completed": False, "timestamp": None, "progress": 0})
    gnss: Dict[str, Any] = field(default_factory=lambda: {"completed": False, "timestamp": None, "progress": 0, "pos_files": []})
    observation: Dict[str, Any] = field(default_factory=lambda: {"completed": False, "timestamp": None, "progress": 0})
    qc: Dict[str, Any] = field(default_factory=lambda: {"completed": False, "timestamp": None, "progress": 0})


class ProjectManager(QObject):
    """
    Gestionnaire centralisé des projets de calibration
    Gère la persistance, le versioning et le contrôle qualité
    """
    
    # Signaux PyQt pour synchronisation inter-pages
    project_loaded = pyqtSignal(dict)
    project_saved = pyqtSignal(str)
    workflow_step_completed = pyqtSignal(str, bool)
    qc_score_updated = pyqtSignal(float)
    auto_save_triggered = pyqtSignal()
    
    # Instance singleton
    _instance = None
    
    # Schéma JSON pour validation
    PROJECT_SCHEMA = {
        "type": "object",
        "required": ["metadata", "project_structure", "workflow_status"],
        "properties": {
            "metadata": {
                "type": "object",
                "required": ["version", "created", "company", "vessel", "engineer"],
            },
            "project_structure": {
                "type": "object",
                "required": ["base_path"],
            },
            "workflow_status": {"type": "object"},
            "dimcon_data": {"type": "object"},
            "gnss_config": {"type": "object"},
            "observation_sensors": {"type": "array"},
            "qc_metrics": {"type": "object"}
        }
    }
    
    def __init__(self):
        super().__init__()
        
        # Éviter la double initialisation pour le singleton
        if hasattr(self, '_initialized'):
            return
        
        self.current_project = None
        self.project_path = None
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 5 minutes
        self.backup_versions = 5
        
        # Timer pour auto-sauvegarde
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        
        # Marquer comme initialisé
        self._initialized = True
        
        logger.info("✓ ProjectManager initialisé")
    
    @classmethod
    def instance(cls):
        """Retourne l'instance singleton"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    def create_project(self, name: str, company: str, vessel: str, 
                   engineer: str, description: str = "", 
                   base_path: str = None) -> Tuple[bool, str]:
        """
        Crée un nouveau projet de calibration avec la structure de base
        
        Args:
            name: Nom du projet
            company: Nom de la société
            vessel: Nom du navire
            engineer: Nom de l'ingénieur responsable
            description: Description optionnelle
            base_path: Répertoire de base (optionnel)
        
        Returns:
            Tuple[bool, str]: (succès, message/chemin du projet)
        """
        try:
            # Validation des paramètres
            if not all([name, company, vessel, engineer]):
                return False, "Tous les champs obligatoires doivent être remplis"
            
            # Déterminer le répertoire de base
            if base_path:
                project_dir = Path(base_path) / self._sanitize_filename(name)
            else:
                # Répertoire par défaut dans le dossier utilisateur
                default_projects_dir = Path.home() / "CalibrationGNSS" / "Projets"
                project_dir = default_projects_dir / self._sanitize_filename(name)
            
            # Vérifier si le projet existe déjà
            if project_dir.exists():
                return False, f"Un projet avec ce nom existe déjà: {project_dir}"
            
            # Créer la structure des répertoires
            project_structure = ProjectStructure()
            paths = project_structure.get_full_paths(str(project_dir))
            
            try:
                for path in paths.values():
                    path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✓ Structure créée: {project_dir}")
            except Exception as e:
                return False, f"Impossible de créer la structure: {e}"
            
            # Créer les métadonnées du projet
            metadata = ProjectMetadata(
                company=company,
                vessel=vessel,
                engineer=engineer,
                description=description
            )
            
            # Initialiser la structure du projet
            project_structure.base_path = str(project_dir)
            
            # Initialiser le statut du workflow
            workflow_status = WorkflowStatus()
            
            # Créer les données du projet
            project_data = {
                "metadata": asdict(metadata),
                "project_structure": asdict(project_structure),
                "workflow_status": asdict(workflow_status),
                "dimcon_data": {
                    "points": {},
                    "validated": False
                },
                "gnss_config": {
                    "use_sp3": True,
                    "base_station": {
                        "position_name": "",
                        "coordinates_xyz": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "coordinates_source": "",
                        "obs_file": "",
                        "nav_file": ""
                    },
                    "rovers": [],
                    "file_paths": {},
                    "sp3_clk_status": {},
                    "processing_ready": False,
                    "import_timestamp": ""
                },
                "observation_sensors": [],
                "qc_metrics": {
                    "global_score": 0.0,
                    "last_updated": metadata.last_modified
                }
            }
            
            # Valider les données
            self._validate_project_data(project_data)
            
            # Créer le fichier projet
            project_file = project_dir / f"{self._sanitize_filename(name)}.json"
            self._save_project_file(project_file, project_data)
            
            # Charger le projet créé
            self.current_project = project_data
            self.project_path = project_file
            
            # Démarrer l'auto-sauvegarde
            self._start_auto_save()
            
            # Émettre le signal de projet chargé
            self.project_loaded.emit(project_data)
            
            # Émettre le signal workflow_step_completed pour PROJECT_LOADED
            if hasattr(self, 'workflow_step_completed'):
                self.workflow_step_completed.emit("project_loaded", True)
                logger.info("✓ Signal workflow_step_completed émis pour PROJECT_LOADED")
            
            logger.info(f"✓ Projet créé: {name}")
            return True, str(project_file)
            
        except jsonschema.ValidationError as e:
            logger.error(f"✗ Erreur validation: {e.message}")
            return False, f"Données du projet invalides: {e.message}"
        except Exception as e:
            logger.error(f"✗ Erreur création projet: {e}")
            return False, f"Erreur lors de la création: {str(e)}"
    
    def get_current_project(self):
        """Retourne le projet actuellement chargé"""
        return self.current_project

    def update_gnss_files_and_coordinates(self, rinex_data: Dict[str, Any]) -> bool:
        """
        Met à jour les fichiers RINEX et coordonnées dans le projet
        
        Args:
            rinex_data: {
                'bow_stern': {'obs_file': path, 'nav_file': path, 'approx_xyz': dict},
                'port': {'obs_file': path, 'nav_file': path},
                'starboard': {'obs_file': path, 'nav_file': path},
                'sp3_clk_status': dict
            }
        """
        if not self.current_project:
            return False
        
        try:
            gnss_config = self.current_project.setdefault("gnss_config", {})
            
            # Station de base (Bow/Stern)
            bow_stern = rinex_data.get('bow_stern', {})
            if bow_stern:
                gnss_config['base_station'] = {
                    "position_name": "Bow/Stern",
                    "coordinates_xyz": bow_stern.get('approx_xyz', {"x": 0.0, "y": 0.0, "z": 0.0}),
                    "coordinates_source": "rinex_approx" if bow_stern.get('approx_xyz') else "default",
                    "obs_file": bow_stern.get('obs_file', ''),
                    "nav_file": bow_stern.get('nav_file', '')
                }
            
            # Rovers
            gnss_config['rovers'] = []
            for position in ['port', 'starboard']:
                rover_data = rinex_data.get(position, {})
                if rover_data.get('obs_file'):
                    gnss_config['rovers'].append({
                        "position_name": position.capitalize(),
                        "obs_file": rover_data.get('obs_file', ''),
                        "nav_file": rover_data.get('nav_file', ''),
                        "rover_index": len(gnss_config['rovers'])
                    })
            
            # Chemins pour traitement
            gnss_config['file_paths'] = {
                pos: {
                    'obs_file': data.get('obs_file', ''),
                    'nav_file': data.get('nav_file', '')
                }
                for pos, data in rinex_data.items() 
                if pos != 'sp3_clk_status'
            }
            
            # Ajouter la section de cache pour éviter les recalculs
            gnss_config['processing_cache'] = {
                'rtk_processing': {
                    'completed': False,
                    'timestamp': None,
                    'output_files': {},
                    'quality_stats': {}
                },
                'data_preparation': {
                    'completed': False,
                    'timestamp': None,
                    'attitudes_count': 0,
                    'geometric_biases': {},
                    'quality_threshold': 0.1
                },
                'file_hashes': {}  # Pour détecter les changements de fichiers
            }
            
            # SP3/CLK status
            if 'sp3_clk_status' in rinex_data:
                gnss_config['sp3_clk_status'] = rinex_data['sp3_clk_status']
            
            # Sauvegarder les modifications
            self.save_project(auto=True)
            logger.info("✅ Fichiers GNSS et coordonnées mis à jour avec cache")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour GNSS: {e}")
            return False
    
    def update_rtk_processing_cache(self, baseline_results: Dict[str, Any], quality_stats: Dict[str, int]) -> bool:
        """
        Met à jour le cache de traitement RTK pour éviter les recalculs
        
        Args:
            baseline_results: Résultats des calculs RTK par ligne de base
            quality_stats: Statistiques de qualité globales
        """
        if not self.current_project:
            return False
        
        try:
            gnss_config = self.current_project.setdefault("gnss_config", {})
            processing_cache = gnss_config.setdefault("processing_cache", {})
            rtk_cache = processing_cache.setdefault("rtk_processing", {})
            
            # Mettre à jour le cache RTK
            rtk_cache.update({
                'completed': True,
                'timestamp': datetime.now().isoformat(),
                'output_files': baseline_results,
                'quality_stats': quality_stats
            })
            
            # Sauvegarder
            self.save_project(auto=True)
            logger.info("✅ Cache RTK mis à jour")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour cache RTK: {e}")
            return False
    
    def update_data_preparation_cache(self, preparation_results: Dict[str, Any]) -> bool:
        """
        Met à jour le cache de préparation des données
        
        Args:
            preparation_results: Résultats de la préparation des données
        """
        if not self.current_project:
            return False
        
        try:
            gnss_config = self.current_project.setdefault("gnss_config", {})
            processing_cache = gnss_config.setdefault("processing_cache", {})
            prep_cache = processing_cache.setdefault("data_preparation", {})
            
            # Mettre à jour le cache de préparation
            prep_cache.update({
                'completed': True,
                'timestamp': datetime.now().isoformat(),
                'attitudes_count': preparation_results.get('data_points', 0),
                'geometric_biases': preparation_results.get('biases', {}),
                'quality_threshold': preparation_results.get('quality_threshold', 0.1)
            })
            
            # Sauvegarder
            self.save_project(auto=True)
            logger.info("✅ Cache de préparation mis à jour")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour cache préparation: {e}")
            return False
    
    def is_rtk_processing_completed(self) -> bool:
        """Vérifie si le traitement RTK est déjà terminé"""
        if not self.current_project:
            return False
        
        gnss_config = self.current_project.get("gnss_config", {})
        processing_cache = gnss_config.get("processing_cache", {})
        rtk_cache = processing_cache.get("rtk_processing", {})
        
        return rtk_cache.get("completed", False)
    
    def is_data_preparation_completed(self) -> bool:
        """Vérifie si la préparation des données est déjà terminée"""
        if not self.current_project:
            return False
        
        gnss_config = self.current_project.get("gnss_config", {})
        processing_cache = gnss_config.get("processing_cache", {})
        prep_cache = processing_cache.get("data_preparation", {})
        
        return prep_cache.get("completed", False)
    
    def get_rtk_processing_results(self) -> Dict[str, Any]:
        """Récupère les résultats du traitement RTK depuis le cache"""
        if not self.current_project:
            return {}
        
        gnss_config = self.current_project.get("gnss_config", {})
        processing_cache = gnss_config.get("processing_cache", {})
        rtk_cache = processing_cache.get("rtk_processing", {})
        
        return rtk_cache.get("output_files", {})
    
    def get_data_preparation_results(self) -> Dict[str, Any]:
        """Récupère les résultats de la préparation des données depuis le cache"""
        if not self.current_project:
            return {}
        
        gnss_config = self.current_project.get("gnss_config", {})
        processing_cache = gnss_config.get("processing_cache", {})
        prep_cache = processing_cache.get("data_preparation", {})
        
        return {
            'attitudes_count': prep_cache.get('attitudes_count', 0),
            'geometric_biases': prep_cache.get('geometric_biases', {}),
            'quality_threshold': prep_cache.get('quality_threshold', 0.1),
            'timestamp': prep_cache.get('timestamp', None)
        }
    
    def clear_processing_cache(self) -> bool:
        """Efface le cache de traitement pour forcer un recalcul"""
        if not self.current_project:
            return False
        
        try:
            gnss_config = self.current_project.setdefault("gnss_config", {})
            processing_cache = gnss_config.setdefault("processing_cache", {})
            
            # Réinitialiser les caches
            processing_cache['rtk_processing'] = {
                'completed': False,
                'timestamp': None,
                'output_files': {},
                'quality_stats': {}
            }
            
            processing_cache['data_preparation'] = {
                'completed': False,
                'timestamp': None,
                'attitudes_count': 0,
                'geometric_biases': {},
                'quality_threshold': 0.1
            }
            
            # Sauvegarder
            self.save_project(auto=True)
            logger.info("✅ Cache de traitement effacé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur effacement cache: {e}")
            return False
            
            # Statuts
            has_base = bool(gnss_config['base_station'].get('obs_file'))
            has_rovers = len(gnss_config['rovers']) >= 1
            sp3_ok = gnss_config.get('sp3_clk_status', {}).get('sp3_available', False)
            clk_ok = gnss_config.get('sp3_clk_status', {}).get('clk_available', False)
            
            gnss_config['processing_ready'] = has_base and has_rovers
            gnss_config['sp3_processing_ready'] = gnss_config['processing_ready'] and sp3_ok and clk_ok
            gnss_config['import_timestamp'] = datetime.now().isoformat()
            
            # Mettre à jour workflow
            if gnss_config['processing_ready']:
                progress = 90 if gnss_config['sp3_processing_ready'] else 70
                self.update_workflow_status('gnss', gnss_config['sp3_processing_ready'], progress)
            
            # Auto-save
            if self.auto_save_enabled:
                self.save_project(auto=True)
            
            logger.info(f"✅ GNSS files updated - Base: {has_base}, Rovers: {len(gnss_config['rovers'])}, SP3/CLK: {sp3_ok}/{clk_ok}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour GNSS: {e}")
            return False
    # Modifier la méthode create_project existante pour intégrer GNSS
    def create_project_with_gnss_support(self, name: str, company: str, vessel: str, 
                                        engineer: str, description: str = "",
                                        base_path: str = None) -> Tuple[bool, str]:
        """Version enrichie de create_project avec support GNSS étendu"""
        
        # Appeler la méthode de base
        success, message = self.create_project(name, company, vessel, engineer, description, base_path)
        
        if success and self.current_project:
            # Enrichir la section gnss_config (code existant inchangé)
            enhanced_gnss_config = {
                "use_sp3": True,
                "meridian_convergence": 0.0,
                "scale_factor": 1.0,
                "time_offset": 0.0,
                "base_station": "",
                "rovers": [],
                
                # Structure pour métadonnées (code existant)
                "metadata": {
                    "metadata_version": "1.0",
                    "reference_station": {},
                    "session_info": {},
                    "rinex_files": {"files_by_position": {}, "total_files": 0},
                    "sp3_clk_summary": {"coverage_status": "unknown"},
                    "processing_parameters": {
                        "meridian_convergence": 0.0,
                        "scale_factor": 1.0,
                        "time_offset": 0.0,
                        "use_sp3": True
                    },
                    "completeness_check": {"is_complete": False, "completion_percentage": 0.0}
                },
                
                "sp3_metadata": {"downloaded": [], "status": "pending"},
                "processing_stats": {},
                "last_metadata_update": datetime.now(timezone.utc).isoformat()
            }
            
            self.current_project["gnss_config"] = enhanced_gnss_config
            
            # Sauvegarder les modifications
            self.save_project(auto=True)
            
            logger.info("✅ Projet créé avec support GNSS étendu")
        
        return success, message

    def load_project(self, project_file: str) -> Tuple[bool, str]:
        """Charge un projet existant avec validation"""
        try:
            project_path = Path(project_file)
            if not project_path.exists():
                return False, f"Le fichier {project_file} n'existe pas"
            
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            self._validate_project_data(project_data)
            
            base_path = project_data["project_structure"]["base_path"]
            if not Path(base_path).exists():
                return False, f"Le répertoire de base {base_path} n'existe pas"
            
            # Mettre à jour le timestamp
            project_data["metadata"]["last_modified"] = datetime.now(timezone.utc).isoformat()
            
            # Initialiser le workflow_status s'il n'existe pas (pour les projets existants)
            if "workflow_status" not in project_data:
                from dataclasses import asdict
                workflow_status = WorkflowStatus()
                project_data["workflow_status"] = asdict(workflow_status)
                logger.info("✓ Workflow_status initialisé pour projet existant")
            
            self.current_project = project_data
            self.project_path = project_path
            
            self._start_auto_save()
            self.project_loaded.emit(project_data)
            
            # Émettre le signal workflow_step_completed pour PROJECT_LOADED
            if hasattr(self, 'workflow_step_completed'):
                self.workflow_step_completed.emit("project_loaded", True)
                logger.info("✓ Signal workflow_step_completed émis pour PROJECT_LOADED")
            
            logger.info(f"✓ Projet chargé: {project_path}")
            return True, f"Projet chargé: {project_path.name}"
            
        except jsonschema.ValidationError as e:
            logger.error(f"✗ Erreur validation schéma: {e.message}")
            return False, f"Format de projet invalide: {e.message}"
        except Exception as e:
            logger.error(f"✗ Erreur chargement projet: {e}")
            return False, f"Erreur lors du chargement: {str(e)}"

    def save_project(self, auto: bool = False) -> Tuple[bool, str]:
        """Sauvegarde le projet avec versioning automatique"""
        try:
            if not self.current_project or not self.project_path:
                return False, "Aucun projet actuel à sauvegarder"
            
            # Mettre à jour le timestamp
            self.current_project["metadata"]["last_modified"] = datetime.now(timezone.utc).isoformat()
            
            # Créer un backup si ce n'est pas une auto-sauvegarde
            if not auto:
                self._create_backup()
            
            # Sauvegarder
            self._save_project_file(self.project_path, self.current_project)
            
            # Émettre signal si sauvegarde manuelle
            if not auto:
                self.project_saved.emit(str(self.project_path))
            
            action = "auto-sauvegardé" if auto else "sauvegardé"
            logger.info(f"✓ Projet {action}: {self.project_path.name}")
            return True, f"Projet {action} avec succès"
            
        except Exception as e:
            logger.error(f"✗ Erreur sauvegarde: {e}")
            return False, f"Erreur lors de la sauvegarde: {str(e)}"

    def save_current_project(self) -> Tuple[bool, str]:
        """Alias pour save_project pour compatibilité"""
        return self.save_project(auto=False)

    def update_workflow_status(self, step_name: str, completed: bool, progress: float = None) -> bool:
        """Met à jour l'état d'une étape du workflow"""
        if not self.current_project:
            return False
        
        workflow = self.current_project.setdefault("workflow_status", {})
        step_data = workflow.setdefault(step_name, {})
        
        step_data["completed"] = completed
        if completed:
            step_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            step_data["progress"] = 100.0
        elif progress is not None:
            step_data["progress"] = max(0.0, min(100.0, progress))
        
        self.workflow_step_completed.emit(step_name, completed)
        
        if completed:
            self._update_qc_score()
        
        if self.auto_save_enabled:
            self.save_project(auto=True)
        
        return True

    def update_dimcon_data(self, points_data: Dict[str, Dict[str, float]]) -> bool:
        """Met à jour les données DIMCON"""
        if not self.current_project:
            return False
        
        self.current_project.setdefault("dimcon_data", {})
        self.current_project["dimcon_data"]["points"] = points_data
        self.current_project["dimcon_data"]["validated"] = True
        
        self.update_workflow_status("dimcon", True)
        return True

    def update_gnss_config(self, gnss_config: Dict[str, Any]) -> bool:
        """Met à jour la configuration GNSS"""
        if not self.current_project:
            return False
        
        self.current_project["gnss_config"].update(gnss_config)
        return True

    def update_gnss_metadata_in_project(self, app_data_instance) -> bool:
        """
        Met à jour les métadonnées GNSS dans le projet actuel
        
        Args:
            app_data_instance: Instance d'ApplicationData avec les données GNSS
            
        Returns:
            True si mise à jour réussie
        """
        if not self.current_project:
            logger.warning("Aucun projet actuel pour mise à jour métadonnées GNSS")
            return False
        
        try:
            # Exporter les métadonnées GNSS depuis app_data
            if hasattr(app_data_instance, 'export_gnss_metadata_for_project'):
                gnss_metadata = app_data_instance.export_gnss_metadata_for_project()
                
                # Mettre à jour la section gnss_config du projet
                self.current_project.setdefault("gnss_config", {})
                self.current_project["gnss_config"].update({
                    # Conserver les paramètres existants de configuration
                    "use_sp3": self.current_project["gnss_config"].get("use_sp3", True),
                    "meridian_convergence": gnss_metadata['processing_parameters']['meridian_convergence'],
                    "scale_factor": gnss_metadata['processing_parameters']['scale_factor'],
                    "time_offset": gnss_metadata['processing_parameters']['time_offset'],
                    
                    # NOUVEAU: Ajouter les métadonnées enrichies
                    "metadata": gnss_metadata,
                    "last_metadata_update": datetime.now(timezone.utc).isoformat()
                })
                
                # Mettre à jour le statut workflow si complétude suffisante
                completeness = gnss_metadata.get('completeness_check', {})
                if completeness.get('completion_percentage', 0) >= 50:  # 50% minimum
                    workflow_progress = min(100, completeness['completion_percentage'])
                    self.update_workflow_status("gnss", 
                                              completeness['is_complete'], 
                                              workflow_progress)
                
                # Auto-sauvegarde
                if self.auto_save_enabled:
                    self.save_project(auto=True)
                
                logger.info(f"✅ Métadonnées GNSS mises à jour - Complétude: {completeness.get('completion_percentage', 0):.1f}%")
                return True
                
            else:
                logger.warning("app_data ne supporte pas l'export de métadonnées GNSS")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erreur mise à jour métadonnées GNSS: {e}")
            return False
    
    def load_gnss_metadata_to_app_data(self, app_data_instance) -> bool:
        """
        Charge les métadonnées GNSS du projet vers app_data
        
        Args:
            app_data_instance: Instance d'ApplicationData à alimenter
            
        Returns:
            True si chargement réussi
        """
        if not self.current_project:
            logger.warning("Aucun projet actuel pour chargement métadonnées GNSS")
            return False
        
        try:
            gnss_config = self.current_project.get("gnss_config", {})
            gnss_metadata = gnss_config.get("metadata", {})
            
            if not gnss_metadata:
                logger.info("Aucune métadonnée GNSS trouvée dans le projet")
                return True  # Pas une erreur, juste pas de données
            
            # Charger via la méthode d'import d'app_data
            if hasattr(app_data_instance, 'import_gnss_metadata_from_project'):
                app_data_instance.import_gnss_metadata_from_project(gnss_metadata)
                logger.info("✅ Métadonnées GNSS chargées depuis le projet")
                return True
            else:
                logger.warning("app_data ne supporte pas l'import de métadonnées GNSS")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erreur chargement métadonnées GNSS: {e}")
            return False
    
    def get_gnss_project_summary(self) -> Optional[Dict[str, Any]]:
        """
        Retourne un résumé des métadonnées GNSS du projet
        
        Returns:
            Résumé des données GNSS ou None si pas disponible
        """
        if not self.current_project:
            return None
        
        gnss_config = self.current_project.get("gnss_config", {})
        metadata = gnss_config.get("metadata", {})
        
        if not metadata:
            return {
                'status': 'no_metadata',
                'message': 'Aucune métadonnée GNSS disponible'
            }
        
        # Construire le résumé
        summary = {
            'status': 'available',
            'last_update': gnss_config.get('last_metadata_update', 'Unknown'),
            'reference_station': metadata.get('reference_station', {}),
            'session_summary': {},
            'files_summary': {},
            'sp3_clk_summary': metadata.get('sp3_clk_summary', {}),
            'completeness': metadata.get('completeness_check', {}),
            'processing_parameters': metadata.get('processing_parameters', {})
        }
        
        # Session info
        session_info = metadata.get('session_info', {})
        if session_info:
            summary['session_summary'] = {
                'start_time': session_info.get('start_time', 'N/A'),
                'end_time': session_info.get('end_time', 'N/A'),
                'duration_hours': session_info.get('duration_hours', 0),
                'observation_interval': session_info.get('observation_interval', 0)
            }
        
        # Files summary
        files_registry = metadata.get('rinex_files', {})
        if files_registry:
            summary['files_summary'] = {
                'total_files': files_registry.get('total_files', 0),
                'positions_count': len(files_registry.get('files_by_position', {})),
                'last_import': files_registry.get('last_updated', 'N/A')
            }
        
        return summary
    
    def validate_gnss_data_consistency(self) -> Dict[str, Any]:
        """
        Valide la cohérence des données GNSS du projet
        
        Returns:
            Rapport de validation avec erreurs/avertissements
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'validated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if not self.current_project:
            validation['is_valid'] = False
            validation['errors'].append("Aucun projet chargé")
            return validation
        
        gnss_config = self.current_project.get("gnss_config", {})
        metadata = gnss_config.get("metadata", {})
        
        if not metadata:
            validation['warnings'].append("Aucune métadonnée GNSS trouvée")
            return validation
        
        # Vérifier station de référence
        ref_station = metadata.get('reference_station', {})
        if not ref_station.get('coordinates_xyz'):
            validation['errors'].append("Coordonnées de la station de référence manquantes")
            validation['is_valid'] = False
        
        # Vérifier session
        session_info = metadata.get('session_info', {})
        if not session_info.get('start_time') or not session_info.get('end_time'):
            validation['errors'].append("Informations temporelles de session manquantes")
            validation['is_valid'] = False
        
        # Vérifier durée de session
        duration = session_info.get('duration_hours', 0)
        if duration < 0.5:  # Moins de 30 minutes
            validation['warnings'].append(f"Session très courte ({duration:.2f}h) - précision limitée")
        elif duration > 24:  # Plus de 24h
            validation['warnings'].append(f"Session très longue ({duration:.2f}h) - vérifier les données")
        
        # Vérifier fichiers RINEX
        files_registry = metadata.get('rinex_files', {})
        positions_count = len(files_registry.get('files_by_position', {}))
        if positions_count < 3:
            validation['errors'].append(f"Seulement {positions_count}/3 positions importées")
            validation['is_valid'] = False
        
        # Vérifier SP3/CLK si utilisation prévue
        if gnss_config.get('use_sp3', True):
            sp3_summary = metadata.get('sp3_clk_summary', {})
            coverage = sp3_summary.get('coverage_status', 'unknown')
            
            if coverage == 'insufficient':
                validation['warnings'].append("Couverture SP3/CLK insuffisante - considérer traitement sans SP3")
            elif coverage == 'unknown':
                validation['warnings'].append("Statut SP3/CLK non vérifié")
        
        # Recommandations
        completeness = metadata.get('completeness_check', {})
        completion_pct = completeness.get('completion_percentage', 0)
        
        if completion_pct < 80:
            validation['recommendations'].append("Compléter les données manquantes avant traitement")
        
        if validation['is_valid'] and completion_pct >= 90:
            validation['recommendations'].append("Données GNSS prêtes pour traitement")
        
        return validation
    
    def export_gnss_report(self, output_path: str = None) -> Tuple[bool, str]:
        """
        Exporte un rapport détaillé des métadonnées GNSS
        
        Args:
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            (success, message/path)
        """
        try:
            if not self.current_project:
                return False, "Aucun projet chargé"
            
            # Générer le rapport
            summary = self.get_gnss_project_summary()
            validation = self.validate_gnss_data_consistency()
            
            if not summary or summary.get('status') != 'available':
                return False, "Aucune donnée GNSS à exporter"
            
            # Chemin de sortie par défaut
            if not output_path:
                project_name = Path(self.project_path).stem if self.project_path else "projet"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"rapport_gnss_{project_name}_{timestamp}.json"
            
            # Construire le rapport complet
            report = {
                'rapport_info': {
                    'projet': Path(self.project_path).stem if self.project_path else "Unknown",
                    'genere_le': datetime.now(timezone.utc).isoformat(),
                    'version_rapport': '1.0'
                },
                'metadonnees_projet': self.current_project.get("metadata", {}),
                'resume_gnss': summary,
                'validation': validation,
                'donnees_completes': self.current_project.get("gnss_config", {})
            }
            
            # Sauvegarder
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Rapport GNSS exporté: {output_path}")
            return True, output_path
            
        except Exception as e:
            logger.error(f"✗ Erreur export rapport GNSS: {e}")
            return False, f"Erreur: {str(e)}"
    
    def update_workflow_gnss_progress(self, app_data_instance):
        """
        Met à jour automatiquement le progrès du workflow GNSS basé sur les données
        
        Args:
            app_data_instance: Instance d'ApplicationData
        """
        if not self.current_project or not app_data_instance:
            return
        
        try:
            # Calculer le progrès basé sur les données disponibles
            progress = 0
            completed = False
            
            # Vérifier complétude des données
            if hasattr(app_data_instance, 'check_gnss_data_completeness'):
                completeness = app_data_instance.check_gnss_data_completeness()
                progress = completeness.get('completion_percentage', 0)
                completed = completeness.get('is_complete', False)
            
            # Étapes spécifiques du workflow GNSS
            workflow_steps = {
                'gnss_import': 0,    # Import fichiers RINEX
                'gnss_metadata': 0,  # Extraction métadonnées
                'gnss_sp3_check': 0, # Vérification SP3/CLK
                'gnss_ready': 0      # Prêt pour traitement
            }
            
            # Évaluer chaque étape
            gnss_data = getattr(app_data_instance, 'gnss_data', {})
            
            # Import RINEX
            files_registry = getattr(app_data_instance, 'get_rinex_files_registry', lambda: {})()
            if files_registry.get('total_files', 0) >= 6:  # 3 positions × 2 fichiers minimum
                workflow_steps['gnss_import'] = 100
            elif files_registry.get('total_files', 0) > 0:
                workflow_steps['gnss_import'] = 50
            
            # Métadonnées
            if gnss_data.get('reference_station', {}).get('coordinates_xyz'):
                workflow_steps['gnss_metadata'] += 50
            if gnss_data.get('session_info', {}).get('start_time'):
                workflow_steps['gnss_metadata'] += 50
            
            # SP3/CLK
            sp3_status = gnss_data.get('sp3_clk_availability', {}).get('coverage_status')
            if sp3_status in ['complete', 'mostly_complete']:
                workflow_steps['gnss_sp3_check'] = 100
            elif sp3_status in ['partial']:
                workflow_steps['gnss_sp3_check'] = 60
            elif sp3_status:
                workflow_steps['gnss_sp3_check'] = 30
            
            # Prêt pour traitement
            if progress >= 80:
                workflow_steps['gnss_ready'] = 100
            elif progress >= 50:
                workflow_steps['gnss_ready'] = 70
            
            # Mettre à jour chaque étape
            for step_name, step_progress in workflow_steps.items():
                if step_progress > 0:
                    self.update_workflow_status(step_name, step_progress >= 100, step_progress)
            
            # Mettre à jour l'étape GNSS globale
            global_progress = sum(workflow_steps.values()) / len(workflow_steps)
            global_completed = global_progress >= 95
            
            self.update_workflow_status("gnss", global_completed, global_progress)
            
            logger.debug(f"Workflow GNSS mis à jour: {global_progress:.1f}% ({'✅' if global_completed else '⏳'})")
            
        except Exception as e:
            logger.warning(f"Erreur mise à jour workflow GNSS: {e}")
    
    def add_gnss_pos_files(self, pos_files: List[str]) -> bool:
        """
        Enregistre les chemins des fichiers .pos générés par RTKLIB
        
        Args:
            pos_files: Liste des chemins des fichiers .pos
            
        Returns:
            True si enregistrement réussi
        """
        if not self.current_project:
            logger.warning("Aucun projet actuel pour enregistrer les fichiers .pos")
            return False
        
        try:
            # Initialiser la section workflow_status si nécessaire
            if "workflow_status" not in self.current_project:
                self.current_project["workflow_status"] = {}
            
            # Initialiser la section GNSS si nécessaire
            if "gnss" not in self.current_project["workflow_status"]:
                self.current_project["workflow_status"]["gnss"] = {
                    "completed": False,
                    "timestamp": None,
                    "progress": 0,
                    "pos_files": []
                }
            
            # Ajouter les nouveaux fichiers .pos
            existing_files = self.current_project["workflow_status"]["gnss"].get("pos_files", [])
            for pos_file in pos_files:
                if pos_file not in existing_files:
                    existing_files.append(pos_file)
            
            # Mettre à jour la liste
            self.current_project["workflow_status"]["gnss"]["pos_files"] = existing_files
            self.current_project["workflow_status"]["gnss"]["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Marquer comme terminé si des fichiers .pos existent
            if existing_files:
                self.current_project["workflow_status"]["gnss"]["completed"] = True
                self.current_project["workflow_status"]["gnss"]["progress"] = 100
            
            logger.info(f"✅ Fichiers .pos enregistrés: {len(existing_files)} fichiers")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement fichiers .pos: {e}")
            return False
    
    def get_gnss_pos_files(self) -> List[str]:
        """
        Récupère la liste des fichiers .pos enregistrés dans le projet
        
        Returns:
            Liste des chemins des fichiers .pos
        """
        if not self.current_project:
            return []
        
        try:
            workflow_status = self.current_project.get("workflow_status", {})
            gnss_status = workflow_status.get("gnss", {})
            return gnss_status.get("pos_files", [])
        except Exception as e:
            logger.error(f"❌ Erreur récupération fichiers .pos: {e}")
            return []
    
    def check_gnss_pos_files_exist(self) -> Dict[str, Any]:
        """
        Vérifie si les fichiers .pos enregistrés existent encore
        
        Returns:
            Dictionnaire avec statut et détails
        """
        pos_files = self.get_gnss_pos_files()
        
        result = {
            "has_pos_files": len(pos_files) > 0,
            "existing_files": [],
            "missing_files": [],
            "all_exist": True
        }
        
        for pos_file in pos_files:
            if Path(pos_file).exists():
                result["existing_files"].append(pos_file)
            else:
                result["missing_files"].append(pos_file)
                result["all_exist"] = False
        
        return result
    
    def should_navigate_to_finalization(self) -> bool:
        """
        Détermine si l'application doit naviguer automatiquement vers la page de finalisation
        
        Returns:
            True si navigation automatique recommandée
        """
        try:
            # Vérifier si des fichiers .pos existent
            pos_status = self.check_gnss_pos_files_exist()
            
            # Navigation automatique si :
            # 1. Des fichiers .pos sont enregistrés dans le projet
            # 2. Au moins un fichier existe encore
            # 3. Le workflow GNSS est marqué comme terminé
            workflow_status = self.current_project.get("workflow_status", {})
            gnss_status = workflow_status.get("gnss", {})
            
            return (pos_status["has_pos_files"] and 
                    len(pos_status["existing_files"]) > 0 and
                    gnss_status.get("completed", False))
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification navigation automatique: {e}")
            return False

    def extract_approx_position_xyz(self, rinex_file: str) -> Dict[str, float]:
        """
        Extrait APPROX POSITION XYZ du header RINEX
        
        Returns:
            {'x': float, 'y': float, 'z': float} ou {'x': 0.0, 'y': 0.0, 'z': 0.0}
        """
        try:
            with open(rinex_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if line_num > 100:  # Header max 100 lignes
                        break
                    
                    if 'APPROX POSITION XYZ' in line:
                        # Pattern: APPROX POSITION XYZ    X.XXX    Y.YYY    Z.ZZZ
                        coords = line[:60].split()  # Prendre que les 60 premiers chars
                        if len(coords) >= 3:
                            try:
                                return {
                                    'x': float(coords[0]),
                                    'y': float(coords[1]), 
                                    'z': float(coords[2])
                                }
                            except ValueError:
                                pass
            
            logger.warning(f"APPROX POSITION non trouvé dans {Path(rinex_file).name}")
            return {'x': 0.0, 'y': 0.0, 'z': 0.0}
            
        except Exception as e:
            logger.error(f"Erreur lecture {rinex_file}: {e}")
            return {'x': 0.0, 'y': 0.0, 'z': 0.0}
    
    # === 4. FONCTION POUR VOTRE INTERFACE (bouton "Valider import") ===
    
    def valider_import_rinex_dans_projet(self, fichiers_selectionnes: Dict[str, str]) -> Tuple[bool, str]:
        """
        Fonction à appeler depuis votre interface quand user clique "Valider import"
        
        Args:
            fichiers_selectionnes: {
                'bow_stern_obs': 'chemin/vers/Bow-9205.25o',
                'bow_stern_nav': 'chemin/vers/BRDC.rnx',
                'port_obs': 'chemin/vers/Port-9205.25o', 
                'port_nav': 'chemin/vers/BRDC.rnx',
                'starboard_obs': 'chemin/vers/Stb-9205.25o',
                'starboard_nav': 'chemin/vers/BRDC.rnx'
            }
        
        Returns:
            (success: bool, message: str)
        """
        try:
            logger.info("🔍 Validation import RINEX démarrée")
            
            # 1. Vérifier que nous avons un projet actuel
            if not self.current_project:
                return False, "Aucun projet chargé"
            
            # 2. Extraire APPROX POSITION du Bow/Stern
            bow_obs = fichiers_selectionnes.get('bow_stern_obs')
            if not bow_obs or not Path(bow_obs).exists():
                return False, "Fichier Bow/Stern observation manquant"
            
            logger.info(f"📍 Extraction coordonnées de: {Path(bow_obs).name}")
            approx_xyz = self.extract_approx_position_xyz(bow_obs)
            
            # 3. Vérifier SP3/CLK dans répertoire Bow/Stern
            sp3_clk_status = {}
            if SimpleSP3Checker:
                logger.info("🔍 Vérification SP3/CLK...")
                sp3_check = SimpleSP3Checker.check_sp3_clk_in_directory(bow_obs)
                
                sp3_clk_status = {
                    'sp3_available': sp3_check['sp3_found'],
                    'clk_available': sp3_check['clk_found'],
                    'sp3_files_count': len(sp3_check['sp3_files']),
                    'clk_files_count': len(sp3_check['clk_files']),
                    'first_sp3_file': sp3_check['sp3_files'][0] if sp3_check['sp3_files'] else '',
                    'first_clk_file': sp3_check['clk_files'][0] if sp3_check['clk_files'] else '',
                    'message': sp3_check['message'],
                    'checked_at': sp3_check['checked_at']
                }
                logger.info(f"   {sp3_check['message']}")
            else:
                logger.warning("SimpleSP3Checker non disponible")
                sp3_clk_status = {
                    'sp3_available': False,
                    'clk_available': False,
                    'sp3_files_count': 0,
                    'clk_files_count': 0,
                    'first_sp3_file': '',
                    'first_clk_file': '',
                    'message': 'Vérification SP3/CLK non disponible',
                    'checked_at': datetime.now().isoformat()
                }
            
            # 4. Préparer données pour projet
            rinex_data = {
                'bow_stern': {
                    'obs_file': fichiers_selectionnes.get('bow_stern_obs', ''),
                    'nav_file': fichiers_selectionnes.get('bow_stern_nav', ''),
                    'approx_xyz': approx_xyz
                },
                'port': {
                    'obs_file': fichiers_selectionnes.get('port_obs', ''),
                    'nav_file': fichiers_selectionnes.get('port_nav', '')
                },
                'starboard': {
                    'obs_file': fichiers_selectionnes.get('starboard_obs', ''),
                    'nav_file': fichiers_selectionnes.get('starboard_nav', '')
                },
                'sp3_clk_status': sp3_clk_status
            }
            
            # 5. Mettre à jour le projet
            logger.info("💾 Mise à jour du projet...")
            success = self.update_gnss_files_and_coordinates(rinex_data)
            
            if success:
                # 6. Message de succès
                has_coords = any(approx_xyz[k] != 0.0 for k in ['x', 'y', 'z'])
                sp3_ok = sp3_clk_status['sp3_available'] and sp3_clk_status['clk_available']
                
                message = f"✅ Import RINEX validé et sauvegardé:\n"
                message += f"• Station base: Bow/Stern\n"
                message += f"• Coordonnées XYZ: {'✅ Extraites du RINEX' if has_coords else '⚠️ Par défaut'}\n"
                message += f"• Rovers: Port + Starboard\n" 
                message += f"• SP3/CLK: {'✅ Disponibles' if sp3_ok else '❌ Manquants'}\n"
                message += f"• Prêt traitement RTK: {'✅' if sp3_ok else '⚠️ Possible sans SP3'}"
                
                logger.info("✅ Import RINEX validé avec succès")
                return True, message
            else:
                return False, "Erreur sauvegarde dans le projet"
                
        except Exception as e:
            logger.error(f"Erreur validation import RINEX: {e}")
            return False, f"Erreur validation: {str(e)}"
    
    def get_rtk_file_paths(self) -> Dict[str, str]:
        """
        Récupère les chemins de fichiers pour l'étape RTK
        
        Returns:
            {
                'base_obs': path, 'base_nav': path,
                'rover1_obs': path, 'rover1_nav': path,
                'rover2_obs': path, 'rover2_nav': path,
                'sp3_file': path, 'clk_file': path
            }
        """
        if not self.current_project:
            return {}
        
        gnss_config = self.current_project.get('gnss_config', {})
        
        paths = {}
        
        # Base station
        base_station = gnss_config.get('base_station', {})
        paths['base_obs'] = base_station.get('obs_file', '')
        paths['base_nav'] = base_station.get('nav_file', '')
        
        # Rovers
        rovers = gnss_config.get('rovers', [])
        for i, rover in enumerate(rovers):
            paths[f'rover{i+1}_obs'] = rover.get('obs_file', '')
            paths[f'rover{i+1}_nav'] = rover.get('nav_file', '')
        
        # SP3/CLK
        sp3_status = gnss_config.get('sp3_clk_status', {})
        paths['sp3_file'] = sp3_status.get('first_sp3_file', '')
        paths['clk_file'] = sp3_status.get('first_clk_file', '')
        
        return paths
        
        
        
    
    def update_observation_sensors(self, sensors_data: List[Dict[str, Any]]) -> bool:
        """Met à jour les données des capteurs d'observation"""
        if not self.current_project:
            return False
        
        self.current_project["observation_sensors"] = sensors_data
        self.update_workflow_status("observation", len(sensors_data) > 0)
        return True

    def close_project(self) -> bool:
        """Ferme le projet actuel"""
        if self.current_project and self.auto_save_enabled:
            self.save_project(auto=True)
        
        self._stop_auto_save()
        self.current_project = None
        self.project_path = None
        
        logger.info("✓ Projet fermé")
        return True

    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """Retourne les informations du projet actuel"""
        if not self.current_project:
            return None
        
        return {
            "name": Path(self.project_path).stem if self.project_path else "Nouveau Projet",
            "path": str(self.project_path) if self.project_path else "",
            "metadata": self.current_project.get("metadata", {}),
            "workflow_status": self.current_project.get("workflow_status", {}),
            "qc_metrics": self.current_project.get("qc_metrics", {})
        }

    def get_recent_projects(self, max_count: int = 5) -> List[Dict[str, str]]:
        """Retourne la liste des projets récents"""
        # Cette fonctionnalité peut être étendue pour lire depuis un fichier de configuration
        recent_projects = []
        
        # Chercher dans le dossier projets
        projects_dir = Path.cwd() / "projets"
        if projects_dir.exists():
            for project_file in projects_dir.rglob("*.json"):
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                    
                    metadata = project_data.get("metadata", {})
                    recent_projects.append({
                        "name": project_file.stem,
                        "path": str(project_file),
                        "vessel": metadata.get("vessel", ""),
                        "company": metadata.get("company", ""),
                        "last_modified": metadata.get("last_modified", "")
                    })
                except Exception:
                    continue
        
        # Trier par date de modification
        recent_projects.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
        return recent_projects[:max_count]

    # === MÉTHODES PRIVÉES ===

    def _validate_project_data(self, project_data: Dict[str, Any]) -> None:
        """Valide les données du projet selon le schéma"""
        try:
            jsonschema.validate(project_data, self.PROJECT_SCHEMA)
        except jsonschema.ValidationError as e:
            logger.error(f"Erreur validation: {e.message}")
            raise

    def _save_project_file(self, file_path: Path, project_data: Dict[str, Any]) -> None:
        """Sauvegarde le fichier projet avec gestion d'erreurs"""
        # Utiliser un fichier temporaire pour éviter la corruption
        temp_file = file_path.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            # Déplacer le fichier temporaire vers le fichier final
            shutil.move(temp_file, file_path)
            
        except Exception as e:
            # Nettoyer le fichier temporaire en cas d'erreur
            if temp_file.exists():
                temp_file.unlink()
            raise e

    def _create_backup(self) -> None:
        """Crée une sauvegarde du projet"""
        if not self.project_path:
            return
        
        try:
            base_path = Path(self.current_project["project_structure"]["base_path"])
            backup_dir = base_path / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{self.project_path.stem}_backup_{timestamp}.json"
            
            shutil.copy2(self.project_path, backup_file)
            self._cleanup_old_backups(backup_dir)
            
            logger.info(f"✓ Backup créé: {backup_file.name}")
            
        except Exception as e:
            logger.warning(f"⚠ Erreur création backup: {e}")

    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """Nettoie les anciennes sauvegardes"""
        try:
            backup_files = sorted(backup_dir.glob("*_backup_*.json"))
            if len(backup_files) > self.backup_versions:
                for old_backup in backup_files[:-self.backup_versions]:
                    old_backup.unlink()
                    logger.info(f"✓ Ancien backup supprimé: {old_backup.name}")
        except Exception as e:
            logger.warning(f"⚠ Erreur nettoyage backups: {e}")

    def _update_qc_score(self) -> None:
        """Met à jour le score QC global"""
        if not self.current_project:
            return
        
        try:
            workflow = self.current_project.get("workflow_status", {})
            qc_metrics = self.current_project.setdefault("qc_metrics", {})
            
            # Calculer le score basé sur les étapes complétées
            completed_steps = sum(1 for step in workflow.values() if step.get("completed", False))
            total_steps = len(workflow)
            
            if total_steps > 0:
                global_score = (completed_steps / total_steps) * 100
                qc_metrics["global_score"] = global_score
                
                # Émettre le signal de mise à jour
                self.qc_score_updated.emit(global_score)
                
        except Exception as e:
            logger.warning(f"⚠ Erreur calcul QC score: {e}")

    def _start_auto_save(self) -> None:
        """Démarre l'auto-sauvegarde"""
        if self.auto_save_enabled and self.auto_save_interval > 0:
            self.auto_save_timer.start(self.auto_save_interval * 1000)  # Convertir en millisecondes

    def _stop_auto_save(self) -> None:
        """Arrête l'auto-sauvegarde"""
        self.auto_save_timer.stop()

    def _auto_save(self) -> None:
        """Effectue une auto-sauvegarde"""
        if self.current_project:
            success, message = self.save_project(auto=True)
            if success:
                self.auto_save_triggered.emit()
                logger.debug("✓ Auto-sauvegarde effectuée")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Nettoie un nom de fichier pour éviter les caractères invalides"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)

    def __del__(self):
        """Destructeur pour nettoyer les ressources"""
        try:
            if hasattr(self, 'auto_save_timer'):
                self.auto_save_timer.stop()
        except:
            pass




# -*- coding: utf-8 -*-
"""
Created on Sun Aug  3 21:22:18 2025

@author: a.meunier
"""

# progress_manager.py - Système de progression modulaire et extensible

from PyQt5.QtCore import QObject, pyqtSignal
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    """États possibles d'une tâche"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"

@dataclass
class Task:
    """Définition d'une tâche avec son poids dans le module"""
    id: str
    name: str
    description: str
    weight: float  # Poids dans le calcul de progression (0-1)
    status: TaskStatus = TaskStatus.NOT_STARTED
    progress: float = 0.0  # Progression de la tâche (0-100)
    validator_class: Optional[str] = None  # Nom de la classe de validation

class TaskValidator(ABC):
    """Interface pour les validateurs de tâches"""
    
    @abstractmethod
    def validate(self, app_data) -> Tuple[bool, float, str]:
        """
        Valide une tâche
        Returns: (is_valid, progress_percentage, message)
        """
        pass
    
    @abstractmethod
    def get_requirements(self) -> List[str]:
        """Retourne la liste des prérequis pour cette tâche"""
        pass

# ===== VALIDATEURS DIMCON =====

class DimconCoordinatesValidator(TaskValidator):
    """Validateur pour les coordonnées DIMCON"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not hasattr(app_data, 'dimcon') or not app_data.dimcon:
            return False, 0.0, "Aucune donnée DIMCON"
        
        points = app_data.dimcon
        required_points = ['Bow', 'Port', 'Stb']
        defined_points = 0
        
        for point in required_points:
            if point in points:
                coords = points[point]
                if any(abs(coords.get(coord, 0)) > 0.001 for coord in ['X', 'Y', 'Z']):
                    defined_points += 1
        
        progress = (defined_points / len(required_points)) * 100
        
        if defined_points == len(required_points):
            return True, progress, f"Tous les points définis ({defined_points}/{len(required_points)})"
        else:
            return False, progress, f"Points partiels ({defined_points}/{len(required_points)})"
    
    def get_requirements(self) -> List[str]:
        return ["Coordonnées X,Y,Z pour Bow, Port, Stb"]

# ===== VALIDATEURS GNSS =====

class GnssBaselineValidator(TaskValidator):
    """Validateur pour le calcul des lignes de base GNSS"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not hasattr(app_data, 'gnss_data'):
            return False, 0.0, "Aucune donnée GNSS"
        
        gnss_data = app_data.gnss_data
        mobile_points = gnss_data.get('mobile_points', {})
        
        if not mobile_points:
            return False, 0.0, "Aucun point mobile importé"
        
        # Compter les points avec données
        valid_points = 0
        for key, point_data in mobile_points.items():
            if isinstance(point_data, dict) and 'data' in point_data:
                data = point_data['data']
                if data is not None and hasattr(data, '__len__') and len(data) > 0:
                    valid_points += 1
        
        expected_points = 2  # Généralement 2 points mobiles
        progress = min(100, (valid_points / expected_points) * 100)
        
        if valid_points >= expected_points:
            return True, progress, f"Lignes de base calculées ({valid_points} points)"
        else:
            return False, progress, f"Données partielles ({valid_points}/{expected_points} points)"
    
    def get_requirements(self) -> List[str]:
        return ["Données des points mobiles", "Point de référence fixe"]

class GnssAlignmentValidator(TaskValidator):
    """Validateur pour l'alignement des données GNSS"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not hasattr(app_data, 'gnss_data'):
            return False, 0.0, "Aucune donnée GNSS"
        
        gnss_data = app_data.gnss_data
        
        # Vérifier les paramètres d'alignement
        alignment_params = [
            'meridian_convergence',
            'scale_factor', 
            'time_offset'
        ]
        
        configured_params = 0
        for param in alignment_params:
            value = gnss_data.get(param, 0)
            if param == 'scale_factor' and value != 1.0:
                configured_params += 1
            elif param != 'scale_factor' and value != 0.0:
                configured_params += 1
        
        progress = (configured_params / len(alignment_params)) * 100
        
        if configured_params > 0:
            return True, progress, f"Paramètres d'alignement configurés ({configured_params}/{len(alignment_params)})"
        else:
            return False, 0.0, "Aucun paramètre d'alignement configuré"
    
    def get_requirements(self) -> List[str]:
        return ["Convergence méridienne", "Facteur d'échelle", "Décalage temporel"]

# ===== VALIDATEURS OBSERVATION =====

class ObservationInstrumentsValidator(TaskValidator):
    """Validateur pour le nombre d'instruments"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not hasattr(app_data, 'observation_data'):
            return False, 0.0, "Aucune donnée d'observation"
        
        sensors = app_data.observation_data.get('sensors', {})
        
        if not sensors:
            return False, 0.0, "Aucun instrument configuré"
        
        total_sensors = len(sensors)
        progress = min(100, total_sensors * 25)  # 4 instruments max pour 100%
        
        return True, progress, f"{total_sensors} instrument(s) configuré(s)"
    
    def get_requirements(self) -> List[str]:
        return ["Configuration des types d'instruments"]

class ObservationImportValidator(TaskValidator):
    """Validateur pour l'import des données d'observation"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not hasattr(app_data, 'observation_data'):
            return False, 0.0, "Aucune donnée d'observation"
        
        sensors = app_data.observation_data.get('sensors', {})
        
        if not sensors:
            return False, 0.0, "Aucun capteur défini"
        
        imported_count = 0
        for sensor_id, sensor_data in sensors.items():
            if sensor_data is not None and hasattr(sensor_data, '__len__') and len(sensor_data) > 0:
                imported_count += 1
        
        total_sensors = len(sensors)
        progress = (imported_count / total_sensors) * 100 if total_sensors > 0 else 0
        
        if imported_count == total_sensors:
            return True, progress, f"Toutes les données importées ({imported_count}/{total_sensors})"
        else:
            return False, progress, f"Import partiel ({imported_count}/{total_sensors})"
    
    def get_requirements(self) -> List[str]:
        return ["Données de capteurs importées"]

class ObservationCalculationValidator(TaskValidator):
    """Validateur pour les calculs d'observation"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not hasattr(app_data, 'observation_data'):
            return False, 0.0, "Aucune donnée d'observation"
        
        calculations = app_data.observation_data.get('calculations', {})
        
        if not calculations:
            return False, 0.0, "Aucun calcul effectué"
        
        # Vérifier la qualité des calculs
        valid_calculations = 0
        total_calculations = len(calculations)
        
        for calc_id, calc_data in calculations.items():
            if isinstance(calc_data, dict) and 'statistics' in calc_data:
                valid_calculations += 1
        
        progress = (valid_calculations / total_calculations) * 100 if total_calculations > 0 else 0
        
        if valid_calculations == total_calculations:
            return True, progress, f"Tous les calculs terminés ({valid_calculations})"
        else:
            return False, progress, f"Calculs partiels ({valid_calculations}/{total_calculations})"
    
    def get_requirements(self) -> List[str]:
        return ["Données importées", "Matrices de rotation calculées"]

# ===== VALIDATEURS WORKFLOW (4 ÉTAPES) =====

class ProjectLoadedValidator(TaskValidator):
    """Validateur pour l'étape 1 : Chargement du projet"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not app_data:
            return False, 0.0, "Aucun projet chargé"
        
        # PRIORITÉ ABSOLUE: Vérifier si ProjectManager a un projet actuel ET un chemin de projet
        try:
            from core.project_manager import ProjectManager
            if ProjectManager and ProjectManager.instance():
                project_manager = ProjectManager.instance()
                if (hasattr(project_manager, 'current_project') and project_manager.current_project and
                    hasattr(project_manager, 'project_path') and project_manager.project_path):
                    
                    # Vérifier que le projet a un nom valide (pas juste des données par défaut)
                    project_name = project_manager.current_project.get('metadata', {}).get('vessel', '')
                    if project_name and project_name.strip():
                        # Vérifier que le projet a été explicitement ouvert (pas juste des données par défaut)
                        # Le projet doit avoir un workflow_status initialisé
                        workflow_status = project_manager.current_project.get('workflow_status', {})
                        if workflow_status and len(workflow_status) > 0:
                            return True, 100.0, f"Projet '{project_name}' chargé via ProjectManager"
                        else:
                            return False, 0.0, "Projet chargé mais pas encore initialisé"
                    else:
                        return False, 0.0, "Projet sans nom valide"
        except Exception as e:
            print(f"❌ Erreur vérification ProjectManager: {e}")
        
        # Si ProjectManager n'a pas de projet actuel, ne pas valider même avec des données DIMCON
        # Les données DIMCON peuvent être des valeurs par défaut de l'application
        return False, 0.0, "Aucun projet explicitement chargé"
    
    def get_requirements(self) -> List[str]:
        return ["Projet ouvert", "Métadonnées disponibles"]

class DimconValidatedValidator(TaskValidator):
    """Validateur pour l'étape 2 : Validation DIMCON"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not app_data:
            return False, 0.0, "Aucun projet chargé"
        
        # PRIORITÉ 1: Vérifier si DIMCON a été explicitement validé via ProjectManager
        try:
            from core.project_manager import ProjectManager
            if ProjectManager and ProjectManager.instance():
                project_manager = ProjectManager.instance()
                if (hasattr(project_manager, 'current_project') and project_manager.current_project and
                    hasattr(project_manager, 'project_path') and project_manager.project_path):
                    
                    # Vérifier que le projet a un nom valide
                    project_name = project_manager.current_project.get('metadata', {}).get('vessel', '')
                    if project_name and project_name.strip():
                        
                        # Vérifier le statut de workflow DIMCON dans le projet
                        workflow_status = project_manager.current_project.get('workflow_status', {})
                        dimcon_status = workflow_status.get('dimcon', {})
                        
                        # Si workflow_status est vide ou n'a pas de clés, c'est un projet existant sans workflow_status initialisé
                        if not workflow_status or len(workflow_status) == 0:
                            return False, 0.0, "Projet existant - Validation DIMCON requise"
                        
                        # Vérifier si DIMCON a été explicitement validé
                        if dimcon_status.get('completed', False):
                            return True, 100.0, "DIMCON validé explicitement par l'utilisateur"
                        
                        # Si pas encore validé, ne pas valider automatiquement même avec des données présentes
                        return False, 0.0, "DIMCON non validé - Cliquez sur Valider dans la page DIMCON"
        except Exception as e:
            print(f"❌ Erreur vérification ProjectManager: {e}")
        
        return False, 0.0, "Aucun projet explicitement chargé"
    
    def get_requirements(self) -> List[str]:
        return ["Coordonnées Bow définies", "Coordonnées Port définies", "Coordonnées Stb définies"]

class GnssFinalizedValidator(TaskValidator):
    """Validateur pour l'étape 3 : Finalisation des calculs GNSS"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not app_data:
            return False, 0.0, "Aucun projet chargé"
        
        # PRIORITÉ 1: Vérifier si GNSS a été finalisé via le workflow
        if hasattr(app_data, 'workflow_steps'):
            workflow = app_data.workflow_steps
            if workflow and workflow.get('gnss_finalized', False):
                return True, 100.0, "GNSS finalisé par workflow"
        
        # PRIORITÉ 2: Vérifier si un projet est réellement chargé via ProjectManager
        project_loaded = False
        try:
            from core.project_manager import ProjectManager
            if ProjectManager and ProjectManager.instance():
                project_manager = ProjectManager.instance()
                if (hasattr(project_manager, 'current_project') and project_manager.current_project and
                    hasattr(project_manager, 'project_path') and project_manager.project_path):
                    
                    # Vérifier que le projet a un nom valide
                    project_name = project_manager.current_project.get('metadata', {}).get('vessel', '')
                    if project_name and project_name.strip():
                        project_loaded = True
        except:
            pass
        
        # Si aucun projet n'est explicitement chargé, ne pas valider GNSS
        if not project_loaded:
            return False, 0.0, "Aucun projet explicitement chargé"
        
        # Vérifier si les données GNSS sont présentes
        if not hasattr(app_data, 'gnss_data') or not app_data.gnss_data or len(app_data.gnss_data) == 0:
            return False, 0.0, "Aucune donnée GNSS"
        
        gnss_data = app_data.gnss_data
        progress = 0
        completed_checks = 0
        total_checks = 4
        
        # Vérifier la station de base
        if gnss_data.get('base_station'):
            progress += 25
            completed_checks += 1
        
        # Vérifier les points mobiles
        mobile_points = gnss_data.get('mobile_points', {})
        if mobile_points and len(mobile_points) >= 2:
            progress += 25
            completed_checks += 1
        
        # Vérifier les paramètres d'alignement
        if gnss_data.get('meridian_convergence', 0) != 0:
            progress += 25
            completed_checks += 1
        
        # Vérifier les calculs effectués
        if gnss_data.get('calculations_completed', False):
            progress += 25
            completed_checks += 1
        
        if completed_checks == total_checks:
            return True, progress, f"GNSS finalisé ({completed_checks}/{total_checks} étapes)"
        else:
            return False, progress, f"GNSS en cours ({completed_checks}/{total_checks} étapes)"
    
    def get_requirements(self) -> List[str]:
        return ["Station de base configurée", "Points mobiles importés", "Paramètres d'alignement", "Calculs terminés"]

class ComparisonFinishedValidator(TaskValidator):
    """Validateur pour l'étape 4 : Comparaison terminée"""
    
    def validate(self, app_data) -> Tuple[bool, float, str]:
        if not app_data:
            return False, 0.0, "Aucun projet chargé"
        
        # PRIORITÉ 1: Vérifier si la comparaison a été terminée via le workflow
        if hasattr(app_data, 'workflow_steps'):
            workflow = app_data.workflow_steps
            if workflow and workflow.get('comparison_finished', False):
                return True, 100.0, "Comparaison terminée par workflow"
        
        # PRIORITÉ 2: Vérifier si un projet est réellement chargé via ProjectManager
        project_loaded = False
        try:
            from core.project_manager import ProjectManager
            if ProjectManager and ProjectManager.instance():
                project_manager = ProjectManager.instance()
                if (hasattr(project_manager, 'current_project') and project_manager.current_project and
                    hasattr(project_manager, 'project_path') and project_manager.project_path):
                    
                    # Vérifier que le projet a un nom valide
                    project_name = project_manager.current_project.get('metadata', {}).get('vessel', '')
                    if project_name and project_name.strip():
                        project_loaded = True
        except:
            pass
        
        # Si aucun projet n'est explicitement chargé, ne pas valider la comparaison
        if not project_loaded:
            return False, 0.0, "Aucun projet explicitement chargé"
        
        # Vérifier que DIMCON et GNSS sont validés
        dimcon_valid, dimcon_progress, _ = DimconValidatedValidator().validate(app_data)
        gnss_valid, gnss_progress, _ = GnssFinalizedValidator().validate(app_data)
        
        if not dimcon_valid:
            return False, 0.0, "DIMCON requis pour comparaison"
        
        if not gnss_valid:
            return False, 25.0, "GNSS requis pour comparaison"
        
        # Vérifier si la comparaison a été effectuée
        if hasattr(app_data, 'comparison_results'):
            comparison = app_data.comparison_results
            if comparison and comparison.get('completed', False):
                return True, 100.0, "Comparaison terminée"
        
        # Vérifier les métriques de qualité
        if hasattr(app_data, 'qc_metrics'):
            qc = app_data.qc_metrics
            if qc and qc.get('global_score', 0) > 0:
                return True, 100.0, f"Comparaison terminée (Score: {qc.get('global_score', 0):.1f}%)"
        
        # Calculer la progression basée sur DIMCON + GNSS
        progress = (dimcon_progress + gnss_progress) / 2
        
        return False, progress, "Comparaison en cours"
    
    def get_requirements(self) -> List[str]:
        return ["DIMCON validé", "GNSS finalisé", "Comparaison effectuée", "Métriques QC calculées"]

class ProgressManager(QObject):
    """Gestionnaire central de progression avec système extensible"""
    
    # Signaux pour notifier les changements
    progress_updated = pyqtSignal(str, float)  # module, progress
    task_completed = pyqtSignal(str, str)      # module, task_id
    module_completed = pyqtSignal(str)         # module
    
    def __init__(self):
        super().__init__()
        
        # Définition des 4 étapes du workflow
        self.modules = {
            'PROJECT_LOADED': [
                Task('project_loaded', 'Chargement projet', 
                     'Projet chargé avec succès', 1.0,
                     validator_class='ProjectLoadedValidator')
            ],
            
            'DIMCON_VALIDATED': [
                Task('dimcon_validated', 'Validation DIMCON', 
                     'Coordonnées DIMCON validées', 1.0,
                     validator_class='DimconValidatedValidator')
            ],
            
            'GNSS_FINALIZED': [
                Task('gnss_finalized', 'Finalisation GNSS', 
                     'Calculs GNSS terminés', 1.0,
                     validator_class='GnssFinalizedValidator')
            ],
            
            'COMPARISON_FINISHED': [
                Task('comparison_finished', 'Comparaison terminée', 
                     'Comparaison DIMCON/GNSS terminée', 1.0,
                     validator_class='ComparisonFinishedValidator')
            ]
        }
        
        # Cache pour éviter les logs répétitifs
        self.last_progress_cache = {}
        
        # Registre des validateurs pour les 4 étapes du workflow
        self.validators = {
            'ProjectLoadedValidator': ProjectLoadedValidator(),
            'DimconValidatedValidator': DimconValidatedValidator(),
            'GnssFinalizedValidator': GnssFinalizedValidator(),
            'ComparisonFinishedValidator': ComparisonFinishedValidator()
        }
    
    def register_validator(self, name: str, validator: TaskValidator):
        """Ajoute un nouveau validateur (extensibilité)"""
        self.validators[name] = validator
    
    def calculate_module_progress(self, module_name: str, app_data) -> Dict[str, Any]:
        """Calcule la progression d'un module"""
        if module_name not in self.modules:
            return {'progress': 0.0, 'tasks': [], 'completed': False}
        
        tasks = self.modules[module_name]
        total_weight = sum(task.weight for task in tasks)
        weighted_progress = 0.0
        completed_tasks = 0
        
        task_results = []
        
        for task in tasks:
            if task.validator_class and task.validator_class in self.validators:
                validator = self.validators[task.validator_class]
                is_valid, progress, message = validator.validate(app_data)
                
                task.progress = progress
                task.status = TaskStatus.VALIDATED if is_valid and progress >= 100 else TaskStatus.IN_PROGRESS
                
                weighted_progress += (progress / 100.0) * task.weight
                
                if task.status == TaskStatus.VALIDATED:
                    completed_tasks += 1
                
                task_results.append({
                    'id': task.id,
                    'name': task.name,
                    'progress': progress,
                    'status': task.status.value,
                    'message': message
                })
        
        module_progress = (weighted_progress / total_weight) * 100 if total_weight > 0 else 0
        module_completed = completed_tasks == len(tasks)
        
        return {
            'progress': module_progress,
            'tasks': task_results,
            'completed': module_completed,
            'completed_tasks': completed_tasks,
            'total_tasks': len(tasks)
        }
    
    def calculate_all_progress(self, app_data) -> Dict[str, Any]:
        """Calcule la progression de tous les modules"""
        # Protection renforcée contre les appels trop fréquents
        import time
        current_time = time.time()
        if hasattr(self, '_last_calculate_time') and current_time - self._last_calculate_time < 1.0:
            return getattr(self, '_last_results', {})
        self._last_calculate_time = current_time
        
        # Protection contre les appels simultanés
        if hasattr(self, '_calculate_in_progress') and self._calculate_in_progress:
            return getattr(self, '_last_results', {})
        self._calculate_in_progress = True
        
        results = {}
        
        for module_name in self.modules:
            module_result = self.calculate_module_progress(module_name, app_data)
            results[module_name] = module_result
            
            # Vérifier si la progression a changé avant d'émettre le signal
            current_progress = module_result['progress']
            last_progress = self.last_progress_cache.get(module_name, -1)
            
            if current_progress != last_progress:
                # Émettre le signal de progression seulement si changement
                self.progress_updated.emit(module_name, current_progress)
                self.last_progress_cache[module_name] = current_progress
            
            if module_result['completed']:
                self.module_completed.emit(module_name)
        
        # Sauvegarder les résultats pour la protection
        self._last_results = results
        self._calculate_in_progress = False
        return results
    
    def get_task_requirements(self, module_name: str, task_id: str) -> List[str]:
        """Retourne les prérequis d'une tâche"""
        if module_name not in self.modules:
            return []
        
        for task in self.modules[module_name]:
            if task.id == task_id and task.validator_class:
                validator = self.validators.get(task.validator_class)
                if validator:
                    return validator.get_requirements()
        
        return []
    
    def add_custom_task(self, module_name: str, task: Task):
        """Ajoute une tâche personnalisée à un module (extensibilité)"""
        if module_name in self.modules:
            self.modules[module_name].append(task)
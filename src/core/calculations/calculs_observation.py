# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 01:46:03 2025

@author: a.meunier
"""

# calculs_observation.py
"""
Module de calculs pour les observations de capteurs.

Ce module implémente les algorithmes de traitement des données de capteurs
(MRU, Compas, Octans) et calcule les matrices de transformation selon
la convention ENU (East-North-Up).
"""

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObservationCalculator:
    """
    Calculateur pour les observations de capteurs de navigation.
    
    Implémente les algorithmes de traitement des données MRU, Compas et Octans
    avec conversion automatique vers les conventions du repère bateau ENU.
    """
    
    def __init__(self):
        """Initialise le calculateur."""
        self.app_data = None
        self.convention_target = {
            'system': 'ENU',  # East-North-Up
            'z_direction': 'up',  # Z vers le haut
            'roll_positive': 'port_up',  # Roll + = bâbord vers le haut
            'pitch_positive': 'bow_up',   # Pitch + = proue vers le haut
            'heading_zero': 'north'       # Heading 0° = Nord géographique
        }
        
        print("✓ ObservationCalculator initialisé avec convention ENU")
    
    def set_data_model(self, app_data):
        """
        Définit le modèle de données utilisé.
        
        Args:
            app_data: Instance d'ApplicationData contenant les données
        """
        self.app_data = app_data
        logger.info("Modèle de données connecté au calculateur")
    
    def calculate_all_sensors(self):
        """
        Calcule les transformations pour tous les capteurs.
        
        Returns:
            dict: Résultats des calculs par capteur
        """
        if not self.app_data:
            logger.warning("Aucun modèle de données disponible")
            return {}
        
        results = {}
        sensors = self.app_data.observation_data.get('sensors', {})
        sensor_types = self.app_data.observation_data.get('sensor_types', {})
        sign_conventions = self.app_data.observation_data.get('sign_conventions', {})
        
        logger.info(f"Calcul pour {len(sensors)} capteurs")
        
        for sensor_id, sensor_data in sensors.items():
            if sensor_data is not None and not sensor_data.empty:
                try:
                    sensor_type = sensor_types.get(sensor_id, 'Unknown')
                    conventions = sign_conventions.get(sensor_id, {})
                    
                    result = self.calculate_sensor_transform(
                        sensor_id, sensor_data, sensor_type, conventions
                    )
                    
                    if result:
                        results[sensor_id] = result
                        logger.info(f"✓ Calcul réussi pour {sensor_id}")
                    else:
                        logger.warning(f"✗ Échec calcul pour {sensor_id}")
                        
                except Exception as e:
                    logger.error(f"Erreur calcul {sensor_id}: {e}")
                    import traceback
                    traceback.print_exc()
        
        logger.info(f"Calculs terminés: {len(results)} capteurs traités")
        return results
    
    def calculate_sensor_transform(self, sensor_id, data, sensor_type, conventions):
        """
        Calcule la transformation pour un capteur spécifique.
        
        Args:
            sensor_id (str): Identifiant du capteur
            data (pd.DataFrame): Données du capteur
            sensor_type (str): Type de capteur (MRU, Compas, Octans)
            conventions (dict): Conventions de signe configurées
            
        Returns:
            dict: Résultats des calculs
        """
        try:
            logger.info(f"Traitement {sensor_id} ({sensor_type})")
            
            # Conversion des données vers les conventions ENU
            converted_data = self.convert_to_enu_convention(data, sensor_type, conventions)
            
            # Calcul des matrices de rotation
            matrices = self.calculate_rotation_matrices(converted_data, sensor_type)
            
            # Calcul des statistiques
            stats = self.calculate_statistics(converted_data, sensor_type)
            
            # Évaluation de la qualité
            quality = self.evaluate_data_quality(converted_data, sensor_type)
            
            return {
                'sensor_type': sensor_type,
                'data_points': len(converted_data),
                'converted_data': converted_data,
                'rotation_matrices': matrices,
                'statistics': stats,
                'quality_assessment': quality,
                'conventions_applied': conventions,
                'calculation_timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erreur transformation {sensor_id}: {e}")
            return None
    
    def convert_to_enu_convention(self, data, sensor_type, conventions):
        """
        Convertit les données vers la convention ENU standard.
        
        Args:
            data (pd.DataFrame): Données brutes du capteur
            sensor_type (str): Type de capteur
            conventions (dict): Conventions de signe à appliquer
            
        Returns:
            pd.DataFrame: Données converties
        """
        converted = data.copy()
        
        # Application des conventions de signe configurées
        for angle_type, sign_factor in conventions.items():
            if angle_type in ['pitch_sign', 'roll_sign', 'heading_sign']:
                angle_col = angle_type.replace('_sign', '').title()
                if angle_col in converted.columns:
                    converted[angle_col] = converted[angle_col] * sign_factor
                    logger.debug(f"Convention appliquée: {angle_col} × {sign_factor}")
        
        # Normalisation des plages d'angles selon les conventions ENU
        if 'Heading' in converted.columns:
            # Heading: 0-360° (0° = Nord)
            converted['Heading'] = converted['Heading'] % 360
        
        if 'Pitch' in converted.columns:
            # Pitch: ±90° (+ = Bow Up)
            converted['Pitch'] = np.clip(converted['Pitch'], -90, 90)
        
        if 'Roll' in converted.columns:
            # Roll: ±180° (+ = Port Up)
            converted['Roll'] = ((converted['Roll'] + 180) % 360) - 180
        
        logger.debug(f"Données converties vers convention ENU pour {sensor_type}")
        return converted
    
    def calculate_rotation_matrices(self, data, sensor_type):
        """
        Calcule les matrices de rotation selon la convention ENU.
        
        Args:
            data (pd.DataFrame): Données converties
            sensor_type (str): Type de capteur
            
        Returns:
            dict: Matrices de rotation calculées
        """
        matrices = {}
        
        # Vérifier les colonnes disponibles selon le type de capteur
        required_cols = self.get_required_columns(sensor_type)
        available_cols = [col for col in required_cols if col in data.columns]
        
        if len(available_cols) < len(required_cols):
            logger.warning(f"Colonnes manquantes pour {sensor_type}: {set(required_cols) - set(available_cols)}")
            return matrices
        
        # Calculer des matrices pour quelques échantillons représentatifs
        sample_indices = self.select_representative_samples(data)
        
        for i, idx in enumerate(sample_indices):
            try:
                # Extraction des angles en radians
                angles_rad = {}
                
                if 'Heading' in data.columns:
                    angles_rad['heading'] = np.radians(data.iloc[idx]['Heading'])
                else:
                    angles_rad['heading'] = 0.0
                
                if 'Pitch' in data.columns:
                    angles_rad['pitch'] = np.radians(data.iloc[idx]['Pitch'])
                else:
                    angles_rad['pitch'] = 0.0
                
                if 'Roll' in data.columns:
                    angles_rad['roll'] = np.radians(data.iloc[idx]['Roll'])
                else:
                    angles_rad['roll'] = 0.0
                
                # Matrice de rotation ENU (ordre ZYX: Heading-Pitch-Roll)
                rotation = R.from_euler(
                    'ZYX', 
                    [angles_rad['heading'], angles_rad['pitch'], angles_rad['roll']], 
                    degrees=False
                )
                
                matrices[f'sample_{i+1}'] = {
                    'epoch_index': idx,
                    'angles_deg': {
                        'heading': data.iloc[idx].get('Heading', 0.0),
                        'pitch': data.iloc[idx].get('Pitch', 0.0),
                        'roll': data.iloc[idx].get('Roll', 0.0)
                    },
                    'rotation_matrix': rotation.as_matrix(),
                    'quaternion': rotation.as_quat(),
                    'euler_zyx_rad': [angles_rad['heading'], angles_rad['pitch'], angles_rad['roll']]
                }
                
            except Exception as e:
                logger.warning(f"Erreur calcul matrice échantillon {i}: {e}")
                continue
        
        # Matrice moyenne si plusieurs échantillons
        if len(matrices) > 1:
            matrices['mean_rotation'] = self.calculate_mean_rotation(matrices)
        
        logger.info(f"Matrices calculées: {len(matrices)} échantillons")
        return matrices
    
    def get_required_columns(self, sensor_type):
        """
        Retourne les colonnes requises selon le type de capteur.
        
        Args:
            sensor_type (str): Type de capteur
            
        Returns:
            list: Liste des colonnes requises
        """
        requirements = {
            'MRU': ['Pitch', 'Roll'],
            'Compas': ['Heading'],
            'Octans': ['Pitch', 'Roll', 'Heading']
        }
        
        return requirements.get(sensor_type, ['Heading'])
    
    def select_representative_samples(self, data, max_samples=5):
        """
        Sélectionne des échantillons représentatifs dans les données.
        
        Args:
            data (pd.DataFrame): Données à échantillonner
            max_samples (int): Nombre maximum d'échantillons
            
        Returns:
            list: Indices des échantillons sélectionnés
        """
        n_points = len(data)
        
        if n_points <= max_samples:
            return list(range(n_points))
        
        # Échantillonnage uniforme
        step = n_points // max_samples
        indices = [i * step for i in range(max_samples)]
        
        # Ajouter le dernier point si pas déjà inclus
        if indices[-1] != n_points - 1:
            indices[-1] = n_points - 1
        
        return indices
    
    def calculate_mean_rotation(self, matrices):
        """
        Calcule la rotation moyenne à partir de plusieurs matrices.
        
        Args:
            matrices (dict): Dictionnaire de matrices de rotation
            
        Returns:
            dict: Rotation moyenne
        """
        try:
            # Récupérer toutes les rotations (exclure 'mean_rotation' si présent)
            rotations = []
            for key, matrix_data in matrices.items():
                if key != 'mean_rotation' and 'quaternion' in matrix_data:
                    quat = matrix_data['quaternion']
                    rotations.append(R.from_quat(quat))
            
            if not rotations:
                return None
            
            # Calcul de la moyenne des quaternions (méthode simplifiée)
            mean_quat = np.mean([r.as_quat() for r in rotations], axis=0)
            mean_quat = mean_quat / np.linalg.norm(mean_quat)  # Normalisation
            
            mean_rotation = R.from_quat(mean_quat)
            mean_euler = mean_rotation.as_euler('ZYX', degrees=True)
            
            return {
                'rotation_matrix': mean_rotation.as_matrix(),
                'quaternion': mean_rotation.as_quat(),
                'euler_zyx_deg': mean_euler,
                'method': 'quaternion_average'
            }
            
        except Exception as e:
            logger.warning(f"Erreur calcul rotation moyenne: {e}")
            return None
    
    def calculate_statistics(self, data, sensor_type):
        """
        Calcule les statistiques descriptives des données.
        
        Args:
            data (pd.DataFrame): Données converties
            sensor_type (str): Type de capteur
            
        Returns:
            dict: Statistiques calculées
        """
        stats = {
            'sensor_type': sensor_type,
            'data_points': len(data),
            'time_span_seconds': 0,
            'sampling_rate_hz': 0
        }
        
        # Calcul de la période d'échantillonnage si colonne Time disponible
        if 'Time_num' in data.columns and len(data) > 1:
            time_diff = np.diff(data['Time_num'].values)
            mean_dt = np.mean(time_diff)
            
            stats['time_span_seconds'] = data['Time_num'].max() - data['Time_num'].min()
            stats['mean_sampling_interval_s'] = mean_dt
            stats['sampling_rate_hz'] = 1.0 / mean_dt if mean_dt > 0 else 0
            stats['sampling_regularity'] = np.std(time_diff) / mean_dt if mean_dt > 0 else 1.0
        
        # Statistiques par colonne d'angle
        angle_columns = ['Pitch', 'Roll', 'Heading']
        for col in angle_columns:
            if col in data.columns:
                values = data[col].dropna()
                if len(values) > 0:
                    stats[f'{col.lower()}_mean'] = values.mean()
                    stats[f'{col.lower()}_std'] = values.std()
                    stats[f'{col.lower()}_min'] = values.min()
                    stats[f'{col.lower()}_max'] = values.max()
                    stats[f'{col.lower()}_range'] = values.max() - values.min()
                    stats[f'{col.lower()}_median'] = values.median()
                    
                    # Percentiles
                    stats[f'{col.lower()}_p05'] = values.quantile(0.05)
                    stats[f'{col.lower()}_p95'] = values.quantile(0.95)
        
        # Score de qualité global
        stats['quality_score'] = self.calculate_quality_score(stats, sensor_type)
        
        logger.debug(f"Statistiques calculées pour {sensor_type}")
        return stats
    
    def evaluate_data_quality(self, data, sensor_type):
        """
        Évalue la qualité des données du capteur.
        
        Args:
            data (pd.DataFrame): Données converties
            sensor_type (str): Type de capteur
            
        Returns:
            dict: Évaluation de la qualité
        """
        quality = {
            'overall_score': 0.0,
            'data_completeness': 0.0,
            'data_consistency': 0.0,
            'sampling_regularity': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        # Complétude des données
        total_cells = len(data) * len(data.columns)
        valid_cells = total_cells - data.isnull().sum().sum()
        quality['data_completeness'] = valid_cells / total_cells if total_cells > 0 else 0.0
        
        # Régularité d'échantillonnage
        if 'Time_num' in data.columns and len(data) > 1:
            time_diffs = np.diff(data['Time_num'].values)
            cv_sampling = np.std(time_diffs) / np.mean(time_diffs) if np.mean(time_diffs) > 0 else 1.0
            quality['sampling_regularity'] = max(0.0, 1.0 - cv_sampling)
        else:
            quality['sampling_regularity'] = 0.5  # Score neutre si pas de temps
        
        # Cohérence des données (plages d'angles raisonnables)
        consistency_scores = []
        
        if 'Heading' in data.columns:
            heading_range = data['Heading'].max() - data['Heading'].min()
            # Une bonne mesure devrait avoir une variation raisonnable mais pas excessive
            if 0 < heading_range < 720:  # Moins de 2 tours complets
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.5)
                quality['issues'].append(f"Plage de heading excessive: {heading_range:.1f}°")
        
        if 'Pitch' in data.columns:
            pitch_max = data['Pitch'].abs().max()
            if pitch_max <= 45:  # Tangage raisonnable pour un navire
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.7)
                quality['issues'].append(f"Tangage élevé détecté: ±{pitch_max:.1f}°")
        
        if 'Roll' in data.columns:
            roll_max = data['Roll'].abs().max()
            if roll_max <= 60:  # Roulis raisonnable
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.7)
                quality['issues'].append(f"Roulis élevé détecté: ±{roll_max:.1f}°")
        
        quality['data_consistency'] = np.mean(consistency_scores) if consistency_scores else 0.5
        
        # Score global
        weights = [0.3, 0.4, 0.3]  # Complétude, cohérence, régularité
        scores = [quality['data_completeness'], quality['data_consistency'], quality['sampling_regularity']]
        quality['overall_score'] = np.average(scores, weights=weights)
        
        # Recommandations
        if quality['data_completeness'] < 0.95:
            quality['recommendations'].append("Vérifier les données manquantes")
        
        if quality['sampling_regularity'] < 0.8:
            quality['recommendations'].append("Améliorer la régularité d'échantillonnage")
        
        if quality['overall_score'] > 0.9:
            quality['recommendations'].append("Qualité excellente - données prêtes pour calibration")
        elif quality['overall_score'] > 0.7:
            quality['recommendations'].append("Qualité bonne - calibration possible")
        else:
            quality['recommendations'].append("Qualité faible - vérifier les données avant calibration")
        
        return quality
    
    def calculate_quality_score(self, stats, sensor_type):
        """
        Calcule un score de qualité global basé sur les statistiques.
        
        Args:
            stats (dict): Statistiques des données
            sensor_type (str): Type de capteur
            
        Returns:
            float: Score de qualité entre 0 et 1
        """
        score_components = []
        
        # Composante: nombre de points de données
        n_points = stats.get('data_points', 0)
        if n_points >= 1000:
            score_components.append(1.0)
        elif n_points >= 100:
            score_components.append(0.8)
        elif n_points >= 10:
            score_components.append(0.6)
        else:
            score_components.append(0.3)
        
        # Composante: stabilité des mesures (basée sur les écarts-types)
        stability_scores = []
        for angle in ['pitch', 'roll', 'heading']:
            std_key = f'{angle}_std'
            if std_key in stats:
                std_val = stats[std_key]
                # Score basé sur la stabilité (moins de variation = meilleur)
                if std_val < 0.1:
                    stability_scores.append(1.0)
                elif std_val < 0.5:
                    stability_scores.append(0.8)
                elif std_val < 1.0:
                    stability_scores.append(0.6)
                else:
                    stability_scores.append(0.4)
        
        if stability_scores:
            score_components.append(np.mean(stability_scores))
        
        # Composante: régularité d'échantillonnage
        if 'sampling_regularity' in stats:
            regularity = 1.0 - min(1.0, stats['sampling_regularity'])
            score_components.append(regularity)
        
        # Score final
        if score_components:
            return np.mean(score_components)
        else:
            return 0.5  # Score neutre par défaut
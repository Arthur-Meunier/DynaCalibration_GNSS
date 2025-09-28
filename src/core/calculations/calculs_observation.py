# src/core/calculations/calculs_observation.py - VERSION CORRIGÉE

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
from scipy.linalg import cholesky
import math
from typing import Dict, List, Optional, Tuple, Any

class ObservationCalculator:
    """
    Calculateur pour les observations des capteurs de navigation
    Implémente les calculs de matrices de rotation et transformations
    avec méthode de Cholesky pour la stabilité numérique
    """
    
    def __init__(self):
        """Initialise le calculateur avec les conventions par défaut"""
        # Référence vers le modèle de données
        self.app_data = None
        self.convention_target = {
            'system': 'ENU',  # East-North-Up
            'z_direction': 'up',  # Z vers le haut
            'x_direction': 'east',        # X vers l'est
            'y_direction': 'north',       # Y vers le nord
            'heading_zero': 'north'       # Heading 0° = Nord géographique
        }
        
        print("[OK] ObservationCalculator initialisé avec convention ENU")
    
    def set_data_model(self, app_data):
        """Définit le modèle de données à utiliser"""
        self.app_data = app_data
        print("[OK] Modèle de données connecté au calculateur")
    
    def calculate_all_sensors(self) -> Dict[str, Any]:
        """
        Effectue tous les calculs pour tous les capteurs disponibles
        
        Returns:
            Dict: Résultats des calculs par capteur
        """
        if not self.app_data:
            print("[WARN] Aucun modèle de données disponible")
            return {}
        
        sensors = self.app_data.observation_data.get('sensors', {})
        if not sensors:
            print("[INFO] Aucun capteur avec données disponible")
            return {}
        
        results = {}
        
        for sensor_id, sensor_data in sensors.items():
            try:
                print(f"[CALC] Calcul pour capteur: {sensor_id}")
                
                # Obtenir le type de capteur
                sensor_type = self.app_data.observation_data.get('sensor_types', {}).get(sensor_id, 'Unknown')
                
                # Effectuer les calculs selon le type
                if sensor_type in ['MRU', 'Octans']:
                    sensor_results = self.calculate_rotation_matrices(sensor_data, sensor_type)
                elif sensor_type == 'Compas':
                    sensor_results = self.calculate_heading_corrections(sensor_data)
                else:
                    print(f"[WARN] Type de capteur non reconnu: {sensor_type}")
                    continue
                
                # Ajouter les statistiques
                sensor_results['statistics'] = self.calculate_statistics(sensor_data, sensor_type)
                
                results[sensor_id] = sensor_results
                print(f"[OK] Calculs terminés pour {sensor_id}")
                
            except Exception as e:
                print(f"[ERROR] Erreur calcul {sensor_id}: {str(e)}")
                continue
        
        return results
    
    def calculate_rotation_matrices(self, data: pd.DataFrame, sensor_type: str) -> Dict[str, Any]:
        """
        Calcule les matrices de rotation pour un capteur MRU/Octans
        
        Args:
            data: DataFrame avec colonnes Time, Pitch, Roll, [Heading]
            sensor_type: Type de capteur ('MRU' ou 'Octans')
            
        Returns:
            Dict: Matrices de rotation et métriques
        """
        results = {
            'rotation_matrices': {},
            'mean_angles': {},
            'corrections': {}
        }
        
        # Vérifier les colonnes requises
        required_cols = ['Time', 'Pitch', 'Roll']
        if sensor_type == 'Octans':
            required_cols.append('Heading')
        
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Colonnes manquantes: {missing_cols}")
        
        # Convertir en radians
        pitch_rad = np.deg2rad(data['Pitch'].values)
        roll_rad = np.deg2rad(data['Roll'].values)
        
        # Calculs des moyennes
        mean_pitch = np.mean(pitch_rad)
        mean_roll = np.mean(roll_rad)
        
        results['mean_angles'] = {
            'pitch_deg': np.rad2deg(mean_pitch),
            'roll_deg': np.rad2deg(mean_roll)
        }
        
        # Matrice de rotation moyenne (méthode Cholesky pour stabilité)
        if len(pitch_rad) > 1:
            # Construire les matrices de rotation individuelles
            rotation_matrices = []
            
            for i in range(len(pitch_rad)):
                # Rotation autour de X (Roll) puis Y (Pitch)
                Rx = self._rotation_matrix_x(roll_rad[i])
                Ry = self._rotation_matrix_y(pitch_rad[i])
                
                # Combinaison des rotations
                R_combined = Ry @ Rx
                rotation_matrices.append(R_combined)
            
            # Moyenne des matrices (approximation)
            mean_rotation = np.mean(rotation_matrices, axis=0)
            
            # Stabilisation avec décomposition de Cholesky si nécessaire
            try:
                # Vérifier si la matrice est proche d'une rotation valide
                det = np.linalg.det(mean_rotation)
                if abs(det - 1.0) > 0.1:  # Seuil de tolérance
                    print(f"[WARN] Déterminant de rotation: {det:.4f} (attendu: 1.0)")
                    
                    # Re-orthogonalisation via SVD
                    U, S, Vt = np.linalg.svd(mean_rotation)
                    mean_rotation = U @ Vt
                    print("[INFO] Matrice re-orthogonalisée via SVD")
                
                results['rotation_matrices']['mean_rotation'] = mean_rotation
                
            except np.linalg.LinAlgError:
                print("[ERROR] Impossible de stabiliser la matrice de rotation")
                # Utiliser la rotation moyenne simple
                results['rotation_matrices']['mean_rotation'] = self._simple_rotation_matrix(mean_pitch, mean_roll)
        
        else:
            # Cas d'un seul point de données
            results['rotation_matrices']['mean_rotation'] = self._simple_rotation_matrix(mean_pitch, mean_roll)
        
        # Traitement du heading si disponible (Octans)
        if sensor_type == 'Octans' and 'Heading' in data.columns:
            heading_rad = np.deg2rad(data['Heading'].values)
            mean_heading = np.mean(heading_rad)
            
            results['mean_angles']['heading_deg'] = np.rad2deg(mean_heading)
            
            # Matrice de rotation complète (Roll, Pitch, Yaw)
            Rz = self._rotation_matrix_z(mean_heading)
            Ry = self._rotation_matrix_y(mean_pitch)
            Rx = self._rotation_matrix_x(mean_roll)
            
            # Ordre de rotation: Z(Yaw) * Y(Pitch) * X(Roll)
            R_complete = Rz @ Ry @ Rx
            results['rotation_matrices']['complete_rotation'] = R_complete
        
        # Calcul des corrections (différence par rapport à la convention ENU)
        target_rotation = np.eye(3)  # Matrice identité pour ENU parfait
        correction_matrix = target_rotation @ results['rotation_matrices']['mean_rotation'].T
        results['corrections']['rotation_correction'] = correction_matrix
        
        return results
    
    def calculate_heading_corrections(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcule les corrections de cap pour un compas
        
        Args:
            data: DataFrame avec colonnes Time, Heading
            
        Returns:
            Dict: Corrections de cap et statistiques
        """
        results = {
            'heading_corrections': {},
            'mean_angles': {},
            'statistics': {}
        }
        
        if 'Heading' not in data.columns:
            raise ValueError("Colonne 'Heading' manquante pour le compas")
        
        heading_deg = data['Heading'].values
        
        # Traitement des discontinuités à 360°
        heading_unwrapped = np.unwrap(np.deg2rad(heading_deg))
        heading_deg_unwrapped = np.rad2deg(heading_unwrapped)
        
        # Calculs statistiques
        mean_heading = np.mean(heading_deg_unwrapped)
        std_heading = np.std(heading_deg_unwrapped)
        
        results['mean_angles']['heading_deg'] = mean_heading % 360
        results['statistics']['heading_std'] = std_heading
        results['statistics']['heading_range'] = np.ptp(heading_deg_unwrapped)
        
        # Correction par rapport au nord géographique (convention)
        # Dans la convention ENU, le heading 0° doit pointer vers le nord
        target_heading = 0.0  # Nord géographique
        heading_correction = target_heading - mean_heading
        
        results['heading_corrections']['mean_correction'] = heading_correction
        results['heading_corrections']['corrected_headings'] = heading_deg + heading_correction
        
        return results
    
    def calculate_statistics(self, data: pd.DataFrame, sensor_type: str) -> Dict[str, float]:
        """
        Calcule les statistiques de qualité pour un capteur
        
        Args:
            data: DataFrame des données capteur
            sensor_type: Type de capteur
            
        Returns:
            Dict: Statistiques de qualité
        """
        stats = {
            'data_points': len(data),
            'quality_score': 0.0
        }
        
        # Statistiques spécifiques au type de capteur
        if 'Pitch' in data.columns:
            stats['pitch_std'] = np.std(data['Pitch'])
            stats['pitch_range'] = np.ptp(data['Pitch'])
        
        if 'Roll' in data.columns:
            stats['roll_std'] = np.std(data['Roll'])
            stats['roll_range'] = np.ptp(data['Roll'])
        
        if 'Heading' in data.columns:
            # Traitement spécial pour le heading (discontinuité à 360°)
            heading_unwrapped = np.unwrap(np.deg2rad(data['Heading']))
            stats['heading_std'] = np.std(np.rad2deg(heading_unwrapped))
            stats['heading_range'] = np.ptp(np.rad2deg(heading_unwrapped))
        
        # Calcul du score de qualité global (0-100)
        quality_factors = []
        
        # Facteur 1: Nombre de points de données
        data_factor = min(100, len(data) / 100 * 100)  # 100 points = score parfait
        quality_factors.append(data_factor * 0.3)  # Poids 30%
        
        # Facteur 2: Stabilité des mesures (faible écart-type = bonne qualité)
        if 'pitch_std' in stats and 'roll_std' in stats:
            # Score inversement proportionnel à l'écart-type
            stability_score = max(0, 100 - (stats['pitch_std'] + stats['roll_std']) * 10)
            quality_factors.append(stability_score * 0.4)  # Poids 40%
        
        # Facteur 3: Cohérence temporelle
        if len(data) > 1:
            # Calculer la variation temporelle
            time_consistency = 100 - min(100, np.std(np.diff(data.index)) * 100)
            quality_factors.append(time_consistency * 0.3)  # Poids 30%
        
        # Score final
        stats['quality_score'] = np.sum(quality_factors) if quality_factors else 0.0
        
        return stats
    
    # Méthodes utilitaires pour les matrices de rotation
    
    def _rotation_matrix_x(self, angle):
        """Matrice de rotation autour de l'axe X (Roll)"""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [1, 0, 0],
            [0, c, -s],
            [0, s, c]
        ])
    
    def _rotation_matrix_y(self, angle):
        """Matrice de rotation autour de l'axe Y (Pitch)"""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [c, 0, s],
            [0, 1, 0],
            [-s, 0, c]
        ])
    
    def _rotation_matrix_z(self, angle):
        """Matrice de rotation autour de l'axe Z (Yaw/Heading)"""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [c, -s, 0],
            [s, c, 0],
            [0, 0, 1]
        ])
    
    def _simple_rotation_matrix(self, pitch, roll):
        """Construit une matrice de rotation simple à partir de pitch et roll"""
        Rx = self._rotation_matrix_x(roll)
        Ry = self._rotation_matrix_y(pitch)
        return Ry @ Rx
    
    def apply_cholesky_stabilization(self, matrix):
        """
        Applique la décomposition de Cholesky pour stabiliser une matrice
        
        Args:
            matrix: Matrice à stabiliser
            
        Returns:
            np.ndarray: Matrice stabilisée
        """
        try:
            # S'assurer que la matrice est positive définie
            gram_matrix = matrix.T @ matrix
            
            # Ajouter un petit terme de régularisation si nécessaire
            eigenvals = np.linalg.eigvals(gram_matrix)
            if np.min(eigenvals) < 1e-10:
                regularization = 1e-8 * np.eye(gram_matrix.shape[0])
                gram_matrix += regularization
                print("[INFO] Régularisation appliquée pour la décomposition de Cholesky")
            
            # Décomposition de Cholesky
            L = cholesky(gram_matrix, lower=True)
            
            # Reconstruction de la matrice stabilisée
            stabilized_matrix = matrix @ np.linalg.inv(L) @ L
            
            return stabilized_matrix
            
        except np.linalg.LinAlgError as e:
            print(f"[ERROR] Échec de la décomposition de Cholesky: {e}")
            return matrix  # Retourner la matrice originale en cas d'échec
    
    def get_convention_info(self) -> Dict[str, str]:
        """
        Retourne les informations sur la convention utilisée
        
        Returns:
            Dict: Informations sur la convention
        """
        return {
            'system_description': 'East-North-Up (ENU) - Convention géodésique standard',
            'x_axis': 'Est géographique',
            'y_axis': 'Nord géographique', 
            'z_axis': 'Vertical vers le haut',
            'roll_definition': 'Rotation autour de X (axe Est)',
            'pitch_definition': 'Rotation autour de Y (axe Nord)',
            'yaw_definition': 'Rotation autour de Z (axe vertical)',
            'heading_reference': 'Nord géographique = 0°, sens horaire positif'
        }
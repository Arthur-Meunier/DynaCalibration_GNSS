import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal

@dataclass
class GNSSNode:
    """Classe représentant un nœud GNSS avec ses coordonnées et données"""
    name: str
    is_fixed: bool = True
    # Coordonnées du point fixe (E, N, h)
    fixed_coordinates: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    # Données temporelles pour les points mobiles
    time_data: Optional[pd.DataFrame] = None
    
    # Métadonnées d'importation
    import_file_path: str = ""
    import_headers: Dict[str, int] = field(default_factory=dict)
    
    def get_stats(self) -> Dict[str, float]:
        """Retourne des statistiques sur les données (pour points mobiles)"""
        if not self.is_fixed and self.time_data is not None:
            stats = {}
            for col in ["E", "N", "h"]:
                if col in self.time_data.columns:
                    stats[f"{col}_mean"] = self.time_data[col].mean()
                    stats[f"{col}_std"] = self.time_data[col].std()
                    stats[f"{col}_min"] = self.time_data[col].min()
                    stats[f"{col}_max"] = self.time_data[col].max()
            return stats
        return {}

@dataclass
class Sensor:
    """Classe représentant un capteur avec son type et ses données"""
    name: str
    sensor_type: str  # "Gyroscope", "MRU", "Combined"
    # DataFrame avec colonnes: Time, hdg, pitch, roll
    data: Optional[pd.DataFrame] = None
    # Ajustement temporel en secondes
    time_adjustment: float = 0.0
    # Conventions de signe
    sign_conventions: Dict[str, int] = field(default_factory=dict)  # 1 pour positif, -1 pour négatif
    # Métadonnées d'importation
    import_file_path: str = ""
    import_headers: Dict[str, int] = field(default_factory=dict)
    
    def get_adjusted_data(self) -> pd.DataFrame:
        """Retourne un DataFrame avec l'ajustement temporel appliqué"""
        if self.data is not None:
            df_copy = self.data.copy()
            if 'Time' in df_copy.columns:
                df_copy['Time'] = df_copy['Time'] + self.time_adjustment
            # Appliquer les conventions de signe
            for col, sign in self.sign_conventions.items():
                if col in df_copy.columns:
                    df_copy[col] = df_copy[col] * sign
            return df_copy
        return pd.DataFrame()

class ApplicationData(QObject):
    """Classe pour stocker et gérer les données de l'application avec signaux"""
    
    # Signal émis quand les données changent, avec le nom de la section modifiée
    data_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        # Initialisation des données pour Dimcon
        self.dimcon = {
            "Bow": {"X": 0.0, "Y": -64.0, "Z": 10.0},
            "Port": {"X": -9.0, "Y": -28.0, "Z": 13.0},
            "Stb": {"X": 9.0, "Y": -28.0, "Z": 13.0}
        }
        
        # CORRECTION: Initialisation des données GNSS avec des structures appropriées
        self.gnss_data = {
            "meridian_convergence": 0.0,
            "scale_factor": 1.0,
            "time_offset": 0.0,
            "fixed_point": {
                "position": "Bow",
                "E": 0.0, 
                "N": 0.0, 
                "h": 0.0
            },
            "mobile_points": {},  # Dictionnaire vide au lieu de None
            "mobile_positions": ["Bow", "Bow"]  # Positions par défaut pour 2 points mobiles
        }
        
        # Initialisation des données pour les capteurs
        self.sensors = {
            "gyro": {},
            "mru": {},
            "combined": {}
        }
        
        # Données pour les résultats
        self.results = {}
    
    def get_dimcon_points(self):
        """Retourne les points Dimcon"""
        return self.dimcon
    
    def update_dimcon_point(self, point_id, coords):
        """Met à jour les coordonnées d'un point DIMCON"""
        if point_id in self.dimcon:
            self.dimcon[point_id] = coords.copy()
            # Émet un signal pour informer que les données ont changé
            self.data_changed.emit("dimcon")
    
    def initialize_gnss_data(self):
        """Initialise ou réinitialise les données GNSS avec une structure appropriée"""
        self.gnss_data = {
            "meridian_convergence": 0.0,
            "scale_factor": 1.0,
            "time_offset": 0.0,
            "fixed_point": {
                "position": "Bow",
                "E": 0.0, 
                "N": 0.0, 
                "h": 0.0
            },
            "mobile_points": {},  # Dictionnaire pour stocker les points mobiles
            "mobile_positions": ["Bow", "Bow"]  # Positions par défaut
        }
        
        # Émettre le signal de changement
        self.data_changed.emit("gnss")
    
    def ensure_gnss_structure(self):
        """S'assure que la structure des données GNSS est correcte"""
        if 'mobile_points' not in self.gnss_data or self.gnss_data['mobile_points'] is None:
            self.gnss_data['mobile_points'] = {}
        
        if 'mobile_positions' not in self.gnss_data:
            self.gnss_data['mobile_positions'] = ["Bow", "Bow"]
        
        if 'fixed_point' not in self.gnss_data:
            self.gnss_data['fixed_point'] = {
                "position": "Bow",
                "E": 0.0, 
                "N": 0.0, 
                "h": 0.0
            }
        
        # S'assurer que les paramètres par défaut existent
        default_params = {
            'meridian_convergence': 0.0,
            'scale_factor': 1.0,
            'time_offset': 0.0
        }
        
        for param, default_value in default_params.items():
            if param not in self.gnss_data:
                self.gnss_data[param] = default_value
    
    def add_gnss_mobile_point(self, point_index, data, position="Bow"):
        """Ajoute ou met à jour un point mobile GNSS"""
        # S'assurer que la structure est correcte
        self.ensure_gnss_structure()
        
        # Créer la clé pour le point
        point_key = f"mobile_{point_index + 1}"
        
        # Stocker les données
        self.gnss_data['mobile_points'][point_key] = {
            'data': data,
            'position': position,
            'import_timestamp': pd.Timestamp.now(),
            'file_info': {
                'rows': len(data) if data is not None else 0,
                'columns': list(data.columns) if data is not None and hasattr(data, 'columns') else []
            }
        }
        
        # Mettre à jour la position si nécessaire
        if point_index < len(self.gnss_data['mobile_positions']):
            self.gnss_data['mobile_positions'][point_index] = position
        
        # Émettre le signal de changement
        self.data_changed.emit("gnss")
    
    def remove_gnss_mobile_point(self, point_index):
        """Supprime un point mobile GNSS"""
        point_key = f"mobile_{point_index + 1}"
        
        if point_key in self.gnss_data.get('mobile_points', {}):
            del self.gnss_data['mobile_points'][point_key]
            self.data_changed.emit("gnss")
    
    def get_gnss_mobile_points_summary(self):
        """Retourne un résumé des points mobiles GNSS"""
        summary = {}
        mobile_points = self.gnss_data.get('mobile_points', {})
        
        for key, point_data in mobile_points.items():
            if isinstance(point_data, dict) and 'data' in point_data:
                data = point_data['data']
                if data is not None and hasattr(data, '__len__'):
                    summary[key] = {
                        'rows': len(data),
                        'position': point_data.get('position', 'Unknown'),
                        'columns': point_data.get('file_info', {}).get('columns', []),
                        'import_time': point_data.get('import_timestamp', 'Unknown')
                    }
        
        return summary
    
    def update_gnss_data(self, gnss_data):
        """Met à jour les données GNSS"""
        self.gnss_data = gnss_data
        self.data_changed.emit("gnss")
    
    def add_sensor(self, sensor_type, sensor_id, data):
        """Ajoute ou met à jour un capteur"""
        if sensor_type in self.sensors:
            self.sensors[sensor_type][sensor_id] = data
            self.data_changed.emit(f"sensor_{sensor_type}")
    
    def remove_sensor(self, sensor_type, sensor_id):
        """Supprime un capteur"""
        if sensor_type in self.sensors and sensor_id in self.sensors[sensor_type]:
            del self.sensors[sensor_type][sensor_id]
            self.data_changed.emit(f"sensor_{sensor_type}")
    
    def update_results(self, result_id, data):
        """Met à jour les résultats"""
        self.results[result_id] = data
        self.data_changed.emit("results")
    
    def get_results_summary(self):
        """Retourne un résumé des résultats"""
        return self.results

# Instance globale des données
app_data = ApplicationData()
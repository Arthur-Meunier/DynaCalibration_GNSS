# core/app_data.py - Version optimisée avec HDF5 + RAM + LRU

import numpy as np
import pandas as pd
import h5py
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from functools import lru_cache
from pathlib import Path
from datetime import datetime,timezone
import json
import warnings

from PyQt5.QtCore import QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)
# Suppression des warnings HDF5 non critiques
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

@dataclass
class GNSSNode:
    """Classe représentant un nœud GNSS avec ses coordonnées et données"""
    name: str
    is_fixed: bool = True
    # Coordonnées du point fixe (E, N, h)
    fixed_coordinates: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    # Données temporelles pour les points mobiles (maintenant référence vers RAM)
    time_data: Optional[pd.DataFrame] = None
    
    # Métadonnées d'importation
    import_file_path: str = ""
    import_headers: Dict[str, int] = field(default_factory=dict)
    processing_params: Dict[str, Any] = field(default_factory=dict)
    
    def get_stats(self) -> Dict[str, float]:
        """Retourne des statistiques sur les données (pour points mobiles)"""
        if not self.is_fixed and self.time_data is not None:
            stats = {}
            for col in ["E", "N", "h"]:
                if col in self.time_data.columns:
                    stats[f"{col}_mean"] = float(self.time_data[col].mean())
                    stats[f"{col}_std"] = float(self.time_data[col].std())
                    stats[f"{col}_min"] = float(self.time_data[col].min())
                    stats[f"{col}_max"] = float(self.time_data[col].max())
            return stats
        return {}

@dataclass
class Sensor:
    """Classe représentant un capteur avec son type et ses données"""
    name: str
    sensor_type: str  # "Gyroscope", "MRU", "Combined"
    # DataFrame avec colonnes: Time, hdg, pitch, roll (maintenant en RAM)
    data: Optional[pd.DataFrame] = None
    # Ajustement temporel en secondes
    time_adjustment: float = 0.0
    # Conventions de signe
    sign_conventions: Dict[str, int] = field(default_factory=dict)  # 1 pour positif, -1 pour négatif
    # Métadonnées d'importation
    import_file_path: str = ""
    import_headers: Dict[str, int] = field(default_factory=dict)
    import_metadata: Dict[str, Any] = field(default_factory=dict)
    
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
    """
    Classe optimisée pour stocker et gérer les données de l'application
    
    ARCHITECTURE :
    - Données courantes en RAM pour performance maximale
    - Persistance HDF5 pour robustesse et compression
    - Cache LRU pour calculs lourds
    - API simple et directe
    """
    
    # Signal émis quand les données changent, avec le nom de la section modifiée
    data_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # === CONFIGURATION PROJET ===
        self.project_path = None
        self.hdf5_file_path = None
        
        # === DONNÉES EN RAM (accès instantané) ===
        
        # Données DIMCON (légères, toujours en RAM)
        self.dimcon = {
            "Bow": {"X": 0.0, "Y": -64.0, "Z": 10.0},
            "Port": {"X": -9.0, "Y": -28.0, "Z": 13.0},
            "Stb": {"X": 9.0, "Y": -28.0, "Z": 13.0}
        }
        
        # Données GNSS (chargées en RAM depuis HDF5)
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
            "mobile_points": {},  # point_id -> DataFrame (en RAM)
            "mobile_positions": ["Bow", "Bow"]
        }
        
        # Données capteurs (chargées en RAM depuis HDF5)
        self.sensor_data = {}  # sensor_id -> DataFrame (en RAM)
        
        # Métadonnées d'import (pour traçabilité)
        self.import_metadata = {}  # data_id -> métadonnées complètes
        
        # Résultats de calculs
        self.results = {}
        
        # === CACHE POUR CALCULS LOURDS ===
        self._calculation_cache = {}
        self._clear_cache_on_data_change = True
        
        print("✅ ApplicationData optimisée initialisée")
    
    # ==========================================
    # GESTION PROJET ET PERSISTANCE HDF5
    # ==========================================
    
    def set_project_path(self, project_path: str):
        """Configure le projet et initialise le fichier HDF5"""
        self.project_path = Path(project_path)
        
        # Créer structure des dossiers
        data_dir = self.project_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichier HDF5 principal
        self.hdf5_file_path = data_dir / "project_data.h5"
        
        print(f"✅ Projet configuré: {self.project_path}")
        print(f"📁 Fichier HDF5: {self.hdf5_file_path}")
    
    def save_all_to_hdf5(self):
        """Sauvegarde toutes les données RAM vers HDF5"""
        if not self.hdf5_file_path:
            raise ValueError("Chemin projet non configuré - appelez set_project_path() d'abord")
        
        print(f"💾 Sauvegarde vers HDF5: {self.hdf5_file_path}")
        
        with h5py.File(self.hdf5_file_path, 'w') as f:
            
            # === DIMCON ===
            dimcon_grp = f.create_group("dimcon")
            for point_name, coords in self.dimcon.items():
                point_grp = dimcon_grp.create_group(point_name)
                for coord, value in coords.items():
                    point_grp.attrs[coord] = value
            
            # === GNSS CONFIG ===
            gnss_grp = f.create_group("gnss")
            
            # Paramètres de configuration
            config_grp = gnss_grp.create_group("config")
            config_grp.attrs["meridian_convergence"] = self.gnss_data["meridian_convergence"]
            config_grp.attrs["scale_factor"] = self.gnss_data["scale_factor"]
            config_grp.attrs["time_offset"] = self.gnss_data["time_offset"]
            
            # Point fixe
            fixed_grp = gnss_grp.create_group("fixed_point")
            for key, value in self.gnss_data["fixed_point"].items():
                fixed_grp.attrs[key] = value
            
            # Points mobiles (DataFrames)
            if self.gnss_data["mobile_points"]:
                mobile_grp = gnss_grp.create_group("mobile_points")
                for point_id, dataframe in self.gnss_data["mobile_points"].items():
                    if isinstance(dataframe, pd.DataFrame) and not dataframe.empty:
                        point_grp = mobile_grp.create_group(point_id)
                        
                        # Sauver chaque colonne avec compression
                        for col in dataframe.columns:
                            point_grp.create_dataset(
                                col, 
                                data=dataframe[col].values,
                                compression='gzip', 
                                compression_opts=1  # Compression légère pour vitesse
                            )
                        
                        # Métadonnées dans attributs
                        point_grp.attrs["rows"] = len(dataframe)
                        point_grp.attrs["columns"] = json.dumps(list(dataframe.columns))
            
            # === CAPTEURS ===
            if self.sensor_data:
                sensors_grp = f.create_group("sensors")
                for sensor_id, dataframe in self.sensor_data.items():
                    if isinstance(dataframe, pd.DataFrame) and not dataframe.empty:
                        sensor_grp = sensors_grp.create_group(sensor_id)
                        
                        # Sauver données avec compression
                        for col in dataframe.columns:
                            sensor_grp.create_dataset(
                                col,
                                data=dataframe[col].values,
                                compression='gzip',
                                compression_opts=1
                            )
                        
                        # Métadonnées
                        sensor_grp.attrs["rows"] = len(dataframe)
                        sensor_grp.attrs["columns"] = json.dumps(list(dataframe.columns))
            
            # === MÉTADONNÉES D'IMPORT ===
            if self.import_metadata:
                meta_grp = f.create_group("import_metadata")
                for data_id, metadata in self.import_metadata.items():
                    # Sauver métadonnées comme JSON string
                    meta_grp.attrs[data_id] = json.dumps(metadata, ensure_ascii=False)
        
        print(f"✅ Sauvegarde HDF5 terminée: {self.hdf5_file_path.stat().st_size / 1024:.1f} KB")
    
    def load_all_from_hdf5(self):
        """Charge toutes les données HDF5 vers RAM"""
        if not self.hdf5_file_path or not self.hdf5_file_path.exists():
            print("⚠️ Aucun fichier HDF5 à charger")
            return
        
        print(f"📂 Chargement depuis HDF5: {self.hdf5_file_path}")
        
        with h5py.File(self.hdf5_file_path, 'r') as f:
            
            # === DIMCON ===
            if "dimcon" in f:
                dimcon_grp = f["dimcon"]
                self.dimcon = {}
                for point_name in dimcon_grp.keys():
                    point_grp = dimcon_grp[point_name]
                    self.dimcon[point_name] = dict(point_grp.attrs)
            
            # === GNSS ===
            if "gnss" in f:
                gnss_grp = f["gnss"]
                
                # Configuration
                if "config" in gnss_grp:
                    config_grp = gnss_grp["config"]
                    self.gnss_data.update({
                        "meridian_convergence": config_grp.attrs.get("meridian_convergence", 0.0),
                        "scale_factor": config_grp.attrs.get("scale_factor", 1.0),
                        "time_offset": config_grp.attrs.get("time_offset", 0.0)
                    })
                
                # Point fixe
                if "fixed_point" in gnss_grp:
                    fixed_grp = gnss_grp["fixed_point"]
                    self.gnss_data["fixed_point"] = dict(fixed_grp.attrs)
                
                # Points mobiles
                if "mobile_points" in gnss_grp:
                    mobile_grp = gnss_grp["mobile_points"]
                    self.gnss_data["mobile_points"] = {}
                    
                    for point_id in mobile_grp.keys():
                        point_grp = mobile_grp[point_id]
                        
                        # Reconstruire DataFrame
                        data = {}
                        for col in point_grp.keys():
                            data[col] = point_grp[col][:]
                        
                        if data:
                            self.gnss_data["mobile_points"][point_id] = pd.DataFrame(data)
            
            # === CAPTEURS ===
            if "sensors" in f:
                sensors_grp = f["sensors"]
                self.sensor_data = {}
                
                for sensor_id in sensors_grp.keys():
                    sensor_grp = sensors_grp[sensor_id]
                    
                    # Reconstruire DataFrame
                    data = {}
                    for col in sensor_grp.keys():
                        data[col] = sensor_grp[col][:]
                    
                    if data:
                        self.sensor_data[sensor_id] = pd.DataFrame(data)
            
            # === MÉTADONNÉES ===
            if "import_metadata" in f:
                meta_grp = f["import_metadata"]
                self.import_metadata = {}
                
                for data_id in meta_grp.attrs.keys():
                    json_str = meta_grp.attrs[data_id]
                    self.import_metadata[data_id] = json.loads(json_str)
        
        # Statistiques de chargement
        gnss_count = len(self.gnss_data.get("mobile_points", {}))
        sensor_count = len(self.sensor_data)
        
        print(f"✅ Chargement terminé: {gnss_count} points GNSS, {sensor_count} capteurs")
        
        # Émettre signal global de changement
        self.data_changed.emit("all")
    
    # ==========================================
    # API GNSS (compatible avec votre code existant)
    # ==========================================
    
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
    
    def add_gnss_mobile_point(self, point_index: int, dataframe: pd.DataFrame, 
                             position: str = "Bow", rinex_metadata: dict = None):
        """
        Ajoute ou met à jour un point mobile GNSS
        
        Args:
            point_index: Index du point (0, 1, 2...)
            dataframe: DataFrame avec colonnes Time, E, N, h, etc.
            position: Position de l'antenne ("Bow", "Port", "Stb")
            rinex_metadata: Métadonnées du traitement RINEX
        """
        self.ensure_gnss_structure()
        
        point_key = f"mobile_{point_index + 1}"
        
        # Stocker le DataFrame directement en RAM
        self.gnss_data['mobile_points'][point_key] = dataframe
        
        # Mettre à jour la position
        if point_index < len(self.gnss_data['mobile_positions']):
            self.gnss_data['mobile_positions'][point_index] = position
        else:
            self.gnss_data['mobile_positions'].append(position)
        
        # Sauvegarder métadonnées d'import
        if rinex_metadata:
            self.import_metadata[f"gnss_{point_key}"] = {
                **rinex_metadata,
                'position': position,
                'import_timestamp': datetime.now().isoformat(),
                'data_summary': {
                    'rows': len(dataframe),
                    'columns': list(dataframe.columns),
                    'time_range': {
                        'start': float(dataframe['Time'].min()) if 'Time' in dataframe.columns else None,
                        'end': float(dataframe['Time'].max()) if 'Time' in dataframe.columns else None
                    }
                }
            }
        
        # Auto-sauvegarde HDF5 si projet configuré
        if self.hdf5_file_path:
            self.save_all_to_hdf5()
        
        # Émettre signal de changement
        self.data_changed.emit("gnss")
        
        print(f"✅ Point GNSS {point_key} ajouté: {len(dataframe)} observations, position {position}")
    
    def remove_gnss_mobile_point(self, point_index: int):
        """Supprime un point mobile GNSS"""
        point_key = f"mobile_{point_index + 1}"
        
        if point_key in self.gnss_data.get('mobile_points', {}):
            del self.gnss_data['mobile_points'][point_key]
            
            # Supprimer métadonnées associées
            meta_key = f"gnss_{point_key}"
            if meta_key in self.import_metadata:
                del self.import_metadata[meta_key]
            
            # Auto-sauvegarde
            if self.hdf5_file_path:
                self.save_all_to_hdf5()
            
            self.data_changed.emit("gnss")
            print(f"✅ Point GNSS {point_key} supprimé")
    
    def get_gnss_mobile_point(self, point_index: int) -> Optional[pd.DataFrame]:
        """Retourne les données d'un point mobile (accès direct RAM)"""
        point_key = f"mobile_{point_index + 1}"
        return self.gnss_data.get('mobile_points', {}).get(point_key)
    
    def get_gnss_mobile_points_summary(self):
        """Retourne un résumé des points mobiles GNSS"""
        summary = {}
        mobile_points = self.gnss_data.get('mobile_points', {})
        
        for key, dataframe in mobile_points.items():
            if isinstance(dataframe, pd.DataFrame):
                meta_key = f"gnss_{key}"
                metadata = self.import_metadata.get(meta_key, {})
                
                summary[key] = {
                    'rows': len(dataframe),
                    'position': metadata.get('position', 'Unknown'),
                    'columns': list(dataframe.columns),
                    'import_time': metadata.get('import_timestamp', 'Unknown'),
                    'time_range': metadata.get('data_summary', {}).get('time_range', {})
                }
        
        return summary
    
    # ==========================================
    # API CAPTEURS (nouvelle architecture optimisée)
    # ==========================================
    
    def add_sensor_data(self, sensor_id: str, dataframe: pd.DataFrame, 
                       import_metadata: dict = None):
        """
        Ajoute des données de capteur
        
        Args:
            sensor_id: Identifiant unique du capteur (ex: "MRU_1", "Gyro_1")
            dataframe: DataFrame avec colonnes Time, Pitch, Roll, Heading, etc.
            import_metadata: Métadonnées d'import de votre système actuel
        """
        # Stocker directement en RAM
        self.sensor_data[sensor_id] = dataframe
        
        # Sauvegarder métadonnées complètes
        if import_metadata:
            self.import_metadata[f"sensor_{sensor_id}"] = {
                **import_metadata,
                'import_timestamp': datetime.now().isoformat(),
                'data_summary': {
                    'rows': len(dataframe),
                    'columns': list(dataframe.columns),
                    'time_range': {
                        'start': float(dataframe['Time'].min()) if 'Time' in dataframe.columns else None,
                        'end': float(dataframe['Time'].max()) if 'Time' in dataframe.columns else None
                    },
                    'data_ranges': self._calculate_data_ranges(dataframe)
                }
            }
        
        # Auto-sauvegarde HDF5
        if self.hdf5_file_path:
            self.save_all_to_hdf5()
        
        # Clear cache car nouvelles données
        if self._clear_cache_on_data_change:
            self._calculation_cache.clear()
        
        # Émettre signal
        sensor_type = sensor_id.split('_')[0].lower()
        self.data_changed.emit(f"sensor_{sensor_type}")
        
        print(f"✅ Capteur {sensor_id} ajouté: {len(dataframe)} mesures")
    
    def get_sensor_data(self, sensor_id: str) -> Optional[pd.DataFrame]:
        """Retourne les données d'un capteur (accès direct RAM)"""
        return self.sensor_data.get(sensor_id)
    
    def get_all_sensor_ids(self) -> List[str]:
        """Retourne la liste de tous les IDs de capteurs"""
        return list(self.sensor_data.keys())
    
    def get_sensors_by_type(self, sensor_type: str) -> Dict[str, pd.DataFrame]:
        """Retourne tous les capteurs d'un type donné (MRU, Gyro, etc.)"""
        return {sid: data for sid, data in self.sensor_data.items() 
                if sid.lower().startswith(sensor_type.lower())}
    
    def remove_sensor_data(self, sensor_id: str):
        """Supprime un capteur"""
        if sensor_id in self.sensor_data:
            del self.sensor_data[sensor_id]
            
            # Supprimer métadonnées
            meta_key = f"sensor_{sensor_id}"
            if meta_key in self.import_metadata:
                del self.import_metadata[meta_key]
            
            # Auto-sauvegarde
            if self.hdf5_file_path:
                self.save_all_to_hdf5()
            
            self.data_changed.emit(f"sensor_{sensor_id}")
            print(f"✅ Capteur {sensor_id} supprimé")
    
    # ==========================================
    # API DIMCON (inchangée, déjà optimale)
    # ==========================================
    
    def get_dimcon_points(self):
        """Retourne les points Dimcon"""
        return self.dimcon
    
    def update_dimcon_point(self, point_id: str, coords: dict):
        """Met à jour les coordonnées d'un point DIMCON"""
        if point_id in self.dimcon:
            self.dimcon[point_id] = coords.copy()
            
            # Auto-sauvegarde
            if self.hdf5_file_path:
                self.save_all_to_hdf5()
            
            self.data_changed.emit("dimcon")
            print(f"✅ Point DIMCON {point_id} mis à jour: {coords}")
    
    def update_gnss_reference_station(self, metadata):
        """
        Met à jour les informations de la station de référence GNSS
        CORRECTION: Ajouter vérification que metadata n'est pas None
        """
        try:
            # NOUVEAU: Vérification robuste des paramètres
            if not metadata:
                logger.warning("update_gnss_reference_station: metadata est None")
                return
            
            if not isinstance(metadata, dict):
                logger.warning(f"update_gnss_reference_station: metadata n'est pas un dict ({type(metadata)})")
                return
            
            logger.info("🎯 Mise à jour station de référence GNSS")
            
            reference_station = {
                'coordinates_source': 'rinex_header',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Position approximative avec vérification
            if 'approx_position' in metadata and isinstance(metadata['approx_position'], dict):
                approx_pos = metadata['approx_position']
                reference_station['coordinates_xyz'] = {
                    'x': approx_pos.get('x', 0.0),
                    'y': approx_pos.get('y', 0.0), 
                    'z': approx_pos.get('z', 0.0)
                }
            
            # Informations équipement avec vérifications
            if 'receiver_type' in metadata:
                reference_station['receiver_type'] = str(metadata['receiver_type'])
                
            if 'antenna_type' in metadata:
                reference_station['antenna_type'] = str(metadata['antenna_type'])
                
            if 'antenna_height' in metadata:
                reference_station['antenna_height'] = float(metadata.get('antenna_height', 0.0))
            
            # Sauvegarder dans gnss_data
            self.gnss_data['reference_station'] = reference_station
            
            # Émettre signal de changement
            self.data_changed.emit("gnss_reference_station")
            
            logger.info("✅ Station de référence GNSS mise à jour")
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour station référence: {e}")
            import traceback
        traceback.print_exc()

    def update_gnss_session_info(self, metadata: Dict[str, Any]):
        """
        Met à jour les informations de session GNSS (TIME OF FIRST/LAST OBS)
        NOUVELLE MÉTHODE - Sauvegarde les temps de début/fin extraits du RINEX
        """
        self.ensure_gnss_structure()
        
        if 'session_info' not in self.gnss_data:
            self.gnss_data['session_info'] = {}
        
        # Informations temporelles cruciales
        temporal_info = {
            'start_time': metadata.get('time_of_first_obs'),
            'end_time': metadata.get('time_of_last_obs'),
            'duration_hours': metadata.get('session_duration_hours', 0.0),
            'observation_interval': metadata.get('observation_interval', 0.0),
            'observation_types': metadata.get('observation_types', []),
            'updated_at': datetime.now().isoformat()
        }
        
        self.gnss_data['session_info'].update(temporal_info)
        
        if temporal_info['start_time'] and temporal_info['end_time']:
            print(f"✅ Session GNSS: {temporal_info['start_time']} → {temporal_info['end_time']} ({temporal_info['duration_hours']:.2f}h)")
        
        # Auto-sauvegarde
        if self.hdf5_file_path:
            self.save_all_to_hdf5()
        
        self.data_changed.emit("gnss_session")
    
   
    
    def update_sp3_clk_availability(self, validation_result: Dict[str, Any]):
        """
        Met à jour le statut de disponibilité des fichiers SP3/CLK
        
        Args:
            validation_result: Résultat de SP3CLKValidator.validate_sp3_clk_availability()
        """
        self.ensure_gnss_structure()
        
        # Ajouter timestamp de vérification
        validation_result['checked_at'] = datetime.now().isoformat()
        
        # Sauvegarder le statut complet
        self.gnss_data['sp3_clk_availability'] = validation_result
        
        # Log du résultat avec indicateurs simples
        sp3_ok = "✅ OK" if validation_result.get('sp3_available', False) else "❌ MANQUANT"
        clk_ok = "✅ OK" if validation_result.get('clk_available', False) else "❌ MANQUANT"
        coverage = validation_result.get('coverage_status', 'unknown')
        
        print(f"✅ Validation SP3/CLK terminée:")
        print(f"   SP3: {sp3_ok}")
        print(f"   CLK: {clk_ok}")
        print(f"   Couverture globale: {coverage}")
        
        if validation_result.get('coverage_statistics'):
            stats = validation_result['coverage_statistics']
            print(f"   Statistiques: SP3={stats.get('sp3_coverage_percent', 0):.0f}% | CLK={stats.get('clk_coverage_percent', 0):.0f}%")
        
        # Auto-sauvegarde HDF5
        if self.hdf5_file_path:
            self.save_all_to_hdf5()
        
        # Émettre signal de changement
        self.data_changed.emit("gnss_sp3")

    
    def get_gnss_metadata_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé complet des métadonnées GNSS pour le projet
        
        Returns:
            Dictionnaire avec toutes les métadonnées importantes
        """
        self.ensure_gnss_structure()
        
        summary = {
            'reference_station': self.gnss_data.get('reference_station', {}),
            'session_info': self.gnss_data.get('session_info', {}),
            'sp3_clk_availability': self.gnss_data.get('sp3_clk_availability', {}),
            'mobile_points_count': len(self.gnss_data.get('mobile_points', {})),
            'processing_params': {
                'meridian_convergence': self.gnss_data.get('meridian_convergence', 0.0),
                'scale_factor': self.gnss_data.get('scale_factor', 1.0),
                'time_offset': self.gnss_data.get('time_offset', 0.0)
            },
            'summary_generated_at': datetime.now().isoformat()
        }
        
        return summary
    
    def get_rinex_files_registry(self) -> Dict[str, Any]:
        """
        Retourne un registre de tous les fichiers RINEX importés avec leurs chemins
        
        Returns:
            Registre des fichiers par position
        """
        registry = {
            'files_by_position': {},
            'total_files': 0,
            'last_updated': None
        }
        
        # Parcourir les métadonnées d'import pour trouver les fichiers RINEX
        for data_id, metadata in self.import_metadata.items():
            if data_id.startswith('gnss_') and 'file_paths' in metadata:
                position = metadata.get('position', 'unknown')
                file_paths = metadata['file_paths']
                
                registry['files_by_position'][position] = {
                    'obs_file': file_paths.get('obs', ''),
                    'nav_file': file_paths.get('nav', ''),
                    'gnav_file': file_paths.get('gnav', ''),
                    'base_directory': metadata.get('base_directory', ''),
                    'import_timestamp': metadata.get('import_timestamp', ''),
                    'validation_status': metadata.get('validation_status', 'unknown')
                }
                
                registry['total_files'] += len([f for f in file_paths.values() if f])
        
        if registry['files_by_position']:
            registry['last_updated'] = max(
                info.get('import_timestamp', '') 
                for info in registry['files_by_position'].values()
            )
        
        return registry
    
    def save_rinex_import_metadata(self, position: str, file_info: Dict[str, Any]):
        """
        Sauvegarde les métadonnées d'import d'un triplet RINEX
        
        Args:
            position: Position de l'antenne (Bow/Stern, Port, Starboard)
            file_info: Informations complètes sur les fichiers importés
        """
        data_id = f"gnss_rinex_{position.lower().replace('/', '_')}"
        
        # Préparer les métadonnées complètes
        metadata = {
            'data_type': 'rinex_triplet',
            'position': position,
            'import_timestamp': datetime.now().isoformat(),
            'validation_status': 'valid' if file_info.get('validation_successful', False) else 'invalid',
            'file_paths': file_info.get('found_files', {}),
            'base_directory': file_info.get('base_dir', ''),
            'selected_file': file_info.get('selected_file', ''),
            'missing_types': file_info.get('missing_types', []),
            'rinex_metadata': file_info.get('rinex_metadata', {}),
            'sp3_clk_status': file_info.get('sp3_clk_status', {}),
            'validation_timestamp': file_info.get('validation_timestamp', '')
        }
        
        # Sauvegarder dans le registre des métadonnées
        self.import_metadata[data_id] = metadata
        
        # Mettre à jour les structures spécialisées si position de référence
        if position == "Bow/Stern" and file_info.get('rinex_metadata'):
            self.update_gnss_reference_station(file_info['rinex_metadata'])
            self.update_gnss_session_info(file_info['rinex_metadata'])
            
            if file_info.get('sp3_clk_status'):
                self.update_sp3_clk_availability(file_info['sp3_clk_status'])
        
        # Auto-sauvegarde
        if self.hdf5_file_path:
            self.save_all_to_hdf5()
        
        print(f"✅ Métadonnées RINEX sauvegardées pour {position}")
    
    def check_gnss_data_completeness(self) -> Dict[str, Any]:
        """
        Vérifie la complétude des données GNSS pour validation workflow
        
        Returns:
            Statut de complétude avec détails
        """
        completeness = {
            'is_complete': False,
            'completion_percentage': 0.0,
            'required_elements': {},
            'missing_elements': [],
            'warnings': [],
            'checked_at': datetime.now().isoformat()
        }
        
        # Éléments requis et leur poids
        required_checks = {
            'reference_coordinates': {
                'weight': 30,
                'check': lambda: bool(self.gnss_data.get('reference_station', {}).get('coordinates_xyz')),
                'description': 'Coordonnées XYZ de la station de référence'
            },
            'session_times': {
                'weight': 20,
                'check': lambda: bool(
                    self.gnss_data.get('session_info', {}).get('start_time') and 
                    self.gnss_data.get('session_info', {}).get('end_time')
                ),
                'description': 'Temps de début et fin de session'
            },
            'rinex_files_imported': {
                'weight': 25,
                'check': lambda: len([k for k in self.import_metadata.keys() if k.startswith('gnss_rinex_')]) >= 3,
                'description': 'Fichiers RINEX des 3 positions importés'
            },
            'sp3_availability_checked': {
                'weight': 15,
                'check': lambda: bool(self.gnss_data.get('sp3_clk_availability', {}).get('files_status')),
                'description': 'Vérification disponibilité SP3/CLK'
            },
            'mobile_points_data': {
                'weight': 10,
                'check': lambda: len(self.gnss_data.get('mobile_points', {})) > 0,
                'description': 'Données des points mobiles'
            }
        }
        
        total_weight = 0
        achieved_weight = 0
        
        for element_name, check_config in required_checks.items():
            weight = check_config['weight']
            is_present = check_config['check']()
            description = check_config['description']
            
            total_weight += weight
            
            completeness['required_elements'][element_name] = {
                'present': is_present,
                'weight': weight,
                'description': description
            }
            
            if is_present:
                achieved_weight += weight
            else:
                completeness['missing_elements'].append(description)
        
        # Calculer le pourcentage
        completeness['completion_percentage'] = (achieved_weight / total_weight) * 100 if total_weight > 0 else 0
        completeness['is_complete'] = completeness['completion_percentage'] >= 80  # Seuil de 80%
        
        # Ajouter des avertissements spécifiques
        sp3_status = self.gnss_data.get('sp3_clk_availability', {})
        if sp3_status.get('coverage_status') in ['partial', 'insufficient']:
            completeness['warnings'].append("Couverture SP3/CLK incomplète - précision réduite attendue")
        
        session_info = self.gnss_data.get('session_info', {})
        if session_info.get('duration_hours', 0) < 1:
            completeness['warnings'].append("Session GNSS courte (< 1h) - précision limitée")
        
        return completeness
    
    def export_gnss_metadata_for_project(self) -> Dict[str, Any]:
        """
        Exporte toutes les métadonnées GNSS dans un format adapté au JSON du projet
        
        Returns:
            Dictionnaire optimisé pour sauvegarde projet
        """
        export_data = {
            # Métadonnées de base
            'metadata_version': '1.0',
            'export_timestamp': datetime.now().isoformat(),
            
            # Station de référence (coordonnées cruciales)
            'reference_station': self.gnss_data.get('reference_station', {}),
            
            # Informations temporelles de session
            'session_info': self.gnss_data.get('session_info', {}),
            
            # Registre des fichiers RINEX
            'rinex_files': self.get_rinex_files_registry(),
            
            # Statut SP3/CLK (résumé seulement)
            'sp3_clk_summary': {
                'coverage_status': self.gnss_data.get('sp3_clk_availability', {}).get('coverage_status', 'unknown'),
                'files_status': self.gnss_data.get('sp3_clk_availability', {}).get('files_status', 'not_checked'),
                'date_range_needed': self.gnss_data.get('sp3_clk_availability', {}).get('date_range_needed'),
                'coverage_statistics': self.gnss_data.get('sp3_clk_availability', {}).get('coverage_statistics'),
                'checked_at': self.gnss_data.get('sp3_clk_availability', {}).get('checked_at')
            },
            
            # Paramètres de traitement
            'processing_parameters': {
                'meridian_convergence': self.gnss_data.get('meridian_convergence', 0.0),
                'scale_factor': self.gnss_data.get('scale_factor', 1.0),
                'time_offset': self.gnss_data.get('time_offset', 0.0),
                'use_sp3': True  # Par défaut, sera mis à jour par l'interface
            },
            
            # Statut de complétude
            'completeness_check': self.check_gnss_data_completeness(),
            
            # Points mobiles (résumé seulement - données complètes en HDF5)
            'mobile_points_summary': {
                point_id: {
                    'rows': len(data) if isinstance(data, pd.DataFrame) else 0,
                    'columns': list(data.columns) if isinstance(data, pd.DataFrame) else [],
                    'memory_mb': data.memory_usage(deep=True).sum() / (1024**2) if isinstance(data, pd.DataFrame) else 0
                }
                for point_id, data in self.gnss_data.get('mobile_points', {}).items()
            }
        }
        
        return export_data
    
    def import_gnss_metadata_from_project(self, project_gnss_data: Dict[str, Any]):
        """
        Importe les métadonnées GNSS depuis un JSON de projet
        
        Args:
            project_gnss_data: Données GNSS du projet JSON
        """
        self.ensure_gnss_structure()
        
        try:
            # Restaurer station de référence
            if 'reference_station' in project_gnss_data:
                self.gnss_data['reference_station'] = project_gnss_data['reference_station']
                print("✅ Station de référence restaurée")
            
            # Restaurer informations de session
            if 'session_info' in project_gnss_data:
                self.gnss_data['session_info'] = project_gnss_data['session_info']
                print("✅ Informations de session restaurées")
            
            # Restaurer paramètres de traitement
            if 'processing_parameters' in project_gnss_data:
                params = project_gnss_data['processing_parameters']
                self.gnss_data.update({
                    'meridian_convergence': params.get('meridian_convergence', 0.0),
                    'scale_factor': params.get('scale_factor', 1.0),
                    'time_offset': params.get('time_offset', 0.0)
                })
                print("✅ Paramètres de traitement restaurés")
            
            # Restaurer résumé SP3/CLK
            if 'sp3_clk_summary' in project_gnss_data:
                # Reconstruire une version simplifiée pour usage immédiat
                self.gnss_data['sp3_clk_availability'] = project_gnss_data['sp3_clk_summary']
                print("✅ Statut SP3/CLK restauré")
            
            # Les données complètes (mobile_points) seront chargées depuis HDF5
            # Les fichiers RINEX devront être re-validés si nécessaire
            
            # Émettre signal global de restauration
            self.data_changed.emit("gnss_project_loaded")
            
            print("✅ Métadonnées GNSS projet restaurées avec succès")
            
        except Exception as e:
            print(f"✗ Erreur import métadonnées GNSS: {e}")
            raise
        
      
    # ==========================================
    # CACHE LRU POUR CALCULS LOURDS
    # ==========================================
    
    @lru_cache(maxsize=20)
    def calculate_gnss_baseline(self, point1_id: str, point2_id: str, 
                               method: str = "least_squares") -> Dict[str, Any]:
        """
        Cache LRU pour calcul de ligne de base GNSS
        Exemple de calcul potentiellement coûteux
        """
        print(f"🔄 Calcul ligne de base {point1_id} → {point2_id} (méthode: {method})")
        
        # Récupérer données (accès RAM instantané)
        df1 = self.get_gnss_mobile_point(int(point1_id.split('_')[-1]) - 1)
        df2 = self.get_gnss_mobile_point(int(point2_id.split('_')[-1]) - 1)
        
        if df1 is None or df2 is None:
            return {"error": "Données manquantes"}
        
        # Calcul (simulation - remplacer par vraie logique)
        result = {
            "baseline_vector": {
                "dE": float(df2['E'].mean() - df1['E'].mean()),
                "dN": float(df2['N'].mean() - df1['N'].mean()), 
                "dh": float(df2['h'].mean() - df1['h'].mean())
            },
            "precision": {
                "sigma_E": float(np.sqrt(df1['E'].var() + df2['E'].var())),
                "sigma_N": float(np.sqrt(df1['N'].var() + df2['N'].var())),
                "sigma_h": float(np.sqrt(df1['h'].var() + df2['h'].var()))
            },
            "method": method,
            "computed_at": datetime.now().isoformat()
        }
        
        print(f"✅ Ligne de base calculée et mise en cache")
        return result
    
    @lru_cache(maxsize=10)
    def calculate_rotation_matrix(self, sensor_id: str, time_window: int = 60) -> np.ndarray:
        """
        Cache LRU pour calcul de matrice de rotation
        Exemple de calcul matriciel coûteux
        """
        print(f"🔄 Calcul matrice rotation pour {sensor_id} (fenêtre: {time_window}s)")
        
        data = self.get_sensor_data(sensor_id)
        if data is None or len(data) == 0:
            return np.eye(3)
        
        # Calcul simulation (remplacer par vraie logique)
        # Moyenner les angles sur la fenêtre temporelle
        angles = data[['Pitch', 'Roll', 'Heading']].mean()
        
        # Conversion en radians et construction matrice
        pitch, roll, heading = np.radians([angles['Pitch'], angles['Roll'], angles['Heading']])
        
        # Matrices de rotation élémentaires
        Rx = np.array([[1, 0, 0],
                       [0, np.cos(pitch), -np.sin(pitch)],
                       [0, np.sin(pitch), np.cos(pitch)]])
        
        Ry = np.array([[np.cos(roll), 0, np.sin(roll)],
                       [0, 1, 0],
                       [-np.sin(roll), 0, np.cos(roll)]])
        
        Rz = np.array([[np.cos(heading), -np.sin(heading), 0],
                       [np.sin(heading), np.cos(heading), 0],
                       [0, 0, 1]])
        
        # Matrice de rotation complète
        R = Rz @ Ry @ Rx
        
        print(f"✅ Matrice rotation calculée et mise en cache")
        return R
    
    def clear_calculation_cache(self):
        """Vide le cache de calculs (utile après modification données)"""
        self.calculate_gnss_baseline.cache_clear()
        self.calculate_rotation_matrix.cache_clear()
        self._calculation_cache.clear()
        print("🗑️ Cache de calculs vidé")
    
    # ==========================================
    # UTILITAIRES ET DIAGNOSTICS
    # ==========================================
    
    def _calculate_data_ranges(self, dataframe: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calcule les plages de données pour résumé"""
        ranges = {}
        numeric_cols = dataframe.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col not in ['Time', 'Time_num']:  # Exclure colonnes temporelles
                ranges[col] = {
                    'min': float(dataframe[col].min()),
                    'max': float(dataframe[col].max()),
                    'mean': float(dataframe[col].mean()),
                    'std': float(dataframe[col].std())
                }
        
        return ranges
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Diagnostic mémoire détaillé"""
        usage = {
            'gnss': {'size_mb': 0, 'count': 0, 'details': {}},
            'sensors': {'size_mb': 0, 'count': 0, 'details': {}},
            'total_mb': 0
        }
        
        # GNSS
        gnss_points = self.gnss_data.get('mobile_points', {})
        for point_id, df in gnss_points.items():
            if isinstance(df, pd.DataFrame):
                size_mb = df.memory_usage(deep=True).sum() / (1024**2)
                usage['gnss']['details'][point_id] = {
                    'size_mb': size_mb,
                    'rows': len(df),
                    'columns': len(df.columns)
                }
                usage['gnss']['size_mb'] += size_mb
                usage['gnss']['count'] += 1
        
        # Capteurs
        for sensor_id, df in self.sensor_data.items():
            if isinstance(df, pd.DataFrame):
                size_mb = df.memory_usage(deep=True).sum() / (1024**2)
                usage['sensors']['details'][sensor_id] = {
                    'size_mb': size_mb,
                    'rows': len(df),
                    'columns': len(df.columns)
                }
                usage['sensors']['size_mb'] += size_mb
                usage['sensors']['count'] += 1
        
        usage['total_mb'] = usage['gnss']['size_mb'] + usage['sensors']['size_mb']
        
        return usage
    
    def get_enhanced_project_summary(self) -> Dict[str, Any]:
        """
        Version enrichie du résumé projet avec métadonnées GNSS détaillées
        
        Cette méthode étend get_project_summary() en ajoutant les nouvelles
        métadonnées RINEX/SP3 extraites.
        
        Returns:
            Dictionnaire complet avec résumé de base + métadonnées GNSS enrichies
        """
        # Récupérer le résumé de base (votre méthode existante)
        base_summary = self.get_project_summary()
        
        # Ajouter section GNSS enrichie avec toutes les nouvelles métadonnées
        base_summary['gnss_enhanced'] = {
            'metadata_summary': self.get_gnss_metadata_summary(),
            'completeness_check': self.check_gnss_data_completeness(),
            'files_registry': self.get_rinex_files_registry()
        }
        
        return base_summary
    
    
    def get_project_summary(self) -> Dict[str, Any]:
        """
        Résumé complet du projet (VERSION ENRICHIE)
        
        Cette version étend votre méthode existante avec les nouvelles métadonnées
        """
        # === DONNÉES DE BASE (votre code existant) ===
        summary = {
            'dimcon_points': len(self.dimcon),
            'gnss_mobile_points': len(self.gnss_data.get('mobile_points', {})),
            'sensor_count': len(self.sensor_data),
            'import_metadata_count': len(self.import_metadata),
            'memory_usage': self.get_memory_usage(),
            'hdf5_file': str(self.hdf5_file_path) if self.hdf5_file_path else None,
            'cache_info': {
                'baseline_cache': self.calculate_gnss_baseline.cache_info(),
                'rotation_cache': self.calculate_rotation_matrix.cache_info()
            }
        }
        
        # === NOUVELLES MÉTADONNÉES GNSS (enrichissement) ===
        
        # Station de référence
        ref_station = self.gnss_data.get('reference_station', {})
        summary['gnss_reference_station'] = {
            'has_coordinates': bool(ref_station.get('coordinates_xyz')),
            'coordinates_source': ref_station.get('coordinates_source', 'unknown'),
            'antenna_type': ref_station.get('antenna_type', ''),
            'receiver_type': ref_station.get('receiver_type', '')
        }
        
        # Session GNSS
        session_info = self.gnss_data.get('session_info', {})
        summary['gnss_session'] = {
            'has_time_info': bool(session_info.get('start_time') and session_info.get('end_time')),
            'duration_hours': session_info.get('duration_hours', 0.0),
            'observation_interval': session_info.get('observation_interval', 0.0),
            'observation_types_count': len(session_info.get('observation_types', []))
        }
        
        # Fichiers RINEX
        rinex_registry = self.get_rinex_files_registry() if hasattr(self, 'get_rinex_files_registry') else {}
        summary['rinex_files'] = {
            'total_files': rinex_registry.get('total_files', 0),
            'positions_imported': len(rinex_registry.get('files_by_position', {})),
            'last_import': rinex_registry.get('last_updated', 'Never')
        }
        
        # SP3/CLK disponibilité
        sp3_availability = self.gnss_data.get('sp3_clk_availability', {})
        summary['sp3_clk_status'] = {
            'coverage_status': sp3_availability.get('coverage_status', 'unknown'),
            'files_status': sp3_availability.get('files_status', 'not_checked'),
            'checked': bool(sp3_availability.get('checked_at'))
        }
        
        # Complétude globale GNSS
        completeness = self.check_gnss_data_completeness() if hasattr(self, 'check_gnss_data_completeness') else {}
        summary['gnss_completeness'] = {
            'percentage': completeness.get('completion_percentage', 0.0),
            'is_complete': completeness.get('is_complete', False),
            'missing_count': len(completeness.get('missing_elements', [])),
            'warnings_count': len(completeness.get('warnings', []))
        }
        
        return summary
    def ensure_app_data_has_sp3_methods(app_data_instance):
        """
        Vérifie et ajoute les méthodes SP3/CLK manquantes à app_data
        """
        if not hasattr(app_data_instance, 'update_sp3_clk_availability'):
            def update_sp3_clk_availability(validation_result):
                """Met à jour le statut SP3/CLK dans app_data"""
                if not hasattr(app_data_instance, 'gnss_data'):
                    app_data_instance.gnss_data = {}
                
                app_data_instance.gnss_data['sp3_clk_availability'] = validation_result
                print(f"✅ SP3/CLK status sauvegardé: SP3={validation_result.get('sp3_available')}, CLK={validation_result.get('clk_available')}")
                
                # Émettre signal si possible
                if hasattr(app_data_instance, 'data_changed'):
                    app_data_instance.data_changed.emit("gnss_sp3")
            
            app_data_instance.update_sp3_clk_availability = update_sp3_clk_availability
            print("🔧 Méthode update_sp3_clk_availability ajoutée à app_data")
    
    def print_enhanced_diagnostic(self):
        """
        Version enrichie de print_diagnostic() avec métadonnées GNSS
        
        À appeler pour debug ou vérification de l'état des données
        """
        print("\n" + "="*70)
        print("📊 DIAGNOSTIC COMPLET APPLICATION DATA (VERSION ENRICHIE)")
        print("="*70)
        
        # === DIAGNOSTIC DE BASE (votre code existant) ===
        summary = self.get_project_summary()
        memory = summary['memory_usage']
        
        print(f"📁 Projet: {self.project_path}")
        print(f"💾 Fichier HDF5: {summary['hdf5_file']}")
        print(f"\n📐 DIMCON: {summary['dimcon_points']} points")
        print(f"🛰️ GNSS: {summary['gnss_mobile_points']} points mobiles")
        print(f"📊 Capteurs: {summary['sensor_count']} capteurs")
        
        print(f"\n💾 MÉMOIRE:")
        print(f"   GNSS: {memory['gnss']['size_mb']:.2f} MB ({memory['gnss']['count']} datasets)")
        print(f"   Capteurs: {memory['sensors']['size_mb']:.2f} MB ({memory['sensors']['count']} datasets)")
        print(f"   TOTAL: {memory['total_mb']:.2f} MB")
        
        # === NOUVEAU: DIAGNOSTIC MÉTADONNÉES GNSS ===
        print(f"\n🛰️ MÉTADONNÉES GNSS ENRICHIES:")
        
        # Station de référence
        ref_info = summary['gnss_reference_station']
        coords_status = "✅" if ref_info['has_coordinates'] else "❌"
        print(f"   Station référence: {coords_status} {ref_info['coordinates_source']}")
        if ref_info['antenna_type']:
            print(f"   Équipement: {ref_info['receiver_type']} / {ref_info['antenna_type']}")
        
        # Session
        session_info = summary['gnss_session']
        time_status = "✅" if session_info['has_time_info'] else "❌"
        print(f"   Informations session: {time_status}")
        if session_info['has_time_info']:
            print(f"   Durée: {session_info['duration_hours']:.2f}h, Intervalle: {session_info['observation_interval']}s")
        
        # Fichiers RINEX
        rinex_info = summary['rinex_files']
        print(f"   Fichiers RINEX: {rinex_info['total_files']} fichiers, {rinex_info['positions_imported']}/3 positions")
        
        # SP3/CLK
        sp3_info = summary['sp3_clk_status']
        sp3_icons = {
            'complete': '🟢', 'mostly_complete': '🟡', 
            'partial': '🟠', 'insufficient': '🔴', 'unknown': '❓'
        }
        sp3_icon = sp3_icons.get(sp3_info['coverage_status'], '❓')
        print(f"   SP3/CLK: {sp3_icon} {sp3_info['coverage_status']} ({sp3_info['files_status']})")
        
        # Complétude
        completeness_info = summary['gnss_completeness']
        completion_icon = "✅" if completeness_info['is_complete'] else "⏳"
        print(f"   Complétude: {completion_icon} {completeness_info['percentage']:.1f}%")
        
        if completeness_info['missing_count'] > 0:
            print(f"   Éléments manquants: {completeness_info['missing_count']}")
        
        if completeness_info['warnings_count'] > 0:
            print(f"   Avertissements: {completeness_info['warnings_count']}")
        
        # === CACHE LRU (votre code existant) ===
        print(f"\n⚡ CACHE LRU:")
        baseline_cache = summary['cache_info']['baseline_cache']
        rotation_cache = summary['cache_info']['rotation_cache']
        print(f"   Lignes de base: {baseline_cache.hits} hits, {baseline_cache.misses} misses")
        print(f"   Matrices rotation: {rotation_cache.hits} hits, {rotation_cache.misses} misses")
        
        print("="*70 + "\n")

# Instance globale des données (compatible avec votre code existant)
app_data = ApplicationData()
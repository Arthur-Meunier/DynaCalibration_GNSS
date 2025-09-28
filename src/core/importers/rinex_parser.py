"""
Module de parsing des fichiers RINEX
Gère l'extraction des métadonnées et des données d'observation depuis les fichiers RINEX
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class RinexHeaderParser:
    """Parseur pour les en-têtes de fichiers RINEX"""
    
    def __init__(self):
        self.header_data = {}
        self.observation_types = []
        self.satellite_systems = []
        
    def parse_header(self, file_path: str) -> Dict[str, Any]:
        """
        Parse l'en-tête d'un fichier RINEX
        
        Args:
            file_path: Chemin vers le fichier RINEX
            
        Returns:
            Dict contenant les métadonnées extraites
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            metadata = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'parsing_method': 'rinex_parser',
                'parsing_timestamp': datetime.now().isoformat(),
                'success': False,
                'error': None
            }
            
            # Parse des lignes d'en-tête
            for i, line in enumerate(lines[:100]):  # Limite aux 100 premières lignes
                line = line.strip()
                
                # Informations générales
                if 'MARKER NAME' in line:
                    metadata['marker_name'] = line.split()[0] if line.split() else 'UNKNOWN'
                
                elif 'MARKER TYPE' in line:
                    metadata['marker_type'] = line.split()[0] if line.split() else 'UNKNOWN'
                
                elif 'REC # / TYPE / VERS' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        metadata['receiver_type'] = parts[1]
                        metadata['receiver_version'] = parts[2]
                
                elif 'ANT # / TYPE' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        metadata['antenna_type'] = parts[1]
                
                elif 'APPROX POSITION XYZ' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            metadata['approx_position'] = {
                                'x': float(parts[0]),
                                'y': float(parts[1]),
                                'z': float(parts[2])
                            }
                        except ValueError:
                            pass
                
                elif 'TIME OF FIRST OBS' in line:
                    parts = line.split()
                    if len(parts) >= 7:
                        try:
                            metadata['first_obs_time'] = datetime(
                                int(parts[0]), int(parts[1]), int(parts[2]),
                                int(parts[3]), int(parts[4]), int(float(parts[5]))
                            ).isoformat()
                        except (ValueError, IndexError):
                            pass
                
                elif 'TIME OF LAST OBS' in line:
                    parts = line.split()
                    if len(parts) >= 7:
                        try:
                            metadata['last_obs_time'] = datetime(
                                int(parts[0]), int(parts[1]), int(parts[2]),
                                int(parts[3]), int(parts[4]), int(float(parts[5]))
                            ).isoformat()
                        except (ValueError, IndexError):
                            pass
                
                elif 'SYS / # / OBS TYPES' in line:
                    # Parse des types d'observation
                    parts = line.split()
                    if len(parts) >= 2:
                        system = parts[0]
                        num_obs = int(parts[1]) if parts[1].isdigit() else 0
                        
                        if system not in metadata:
                            metadata[f'{system}_obs_types'] = []
                        
                        # Types d'observation sur cette ligne
                        obs_types = parts[2:2+num_obs] if len(parts) > 2 else []
                        metadata[f'{system}_obs_types'].extend(obs_types)
            
            # Calcul de la durée si les deux temps sont disponibles
            if 'first_obs_time' in metadata and 'last_obs_time' in metadata:
                try:
                    first_time = datetime.fromisoformat(metadata['first_obs_time'])
                    last_time = datetime.fromisoformat(metadata['last_obs_time'])
                    duration = last_time - first_time
                    metadata['duration_hours'] = duration.total_seconds() / 3600
                except (ValueError, TypeError):
                    pass
            
            metadata['success'] = True
            logger.info(f"✅ En-tête RINEX parsé avec succès: {metadata['file_name']}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing en-tête RINEX: {e}")
            metadata['success'] = False
            metadata['error'] = str(e)
            return metadata


class RinexObservationParser:
    """Parseur pour les données d'observation RINEX"""
    
    def __init__(self):
        self.observations = []
        self.epochs = []
        
    def parse_observations(self, file_path: str, max_epochs: int = 100) -> Dict[str, Any]:
        """
        Parse les données d'observation d'un fichier RINEX
        
        Args:
            file_path: Chemin vers le fichier RINEX
            max_epochs: Nombre maximum d'époques à parser
            
        Returns:
            Dict contenant les données d'observation
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            data = {
                'file_path': file_path,
                'parsing_method': 'rinex_observation_parser',
                'parsing_timestamp': datetime.now().isoformat(),
                'success': False,
                'error': None,
                'epochs_parsed': 0,
                'total_satellites': 0,
                'observation_summary': {}
            }
            
            # Trouver le début des données d'observation
            data_start = 0
            for i, line in enumerate(lines):
                if 'END OF HEADER' in line:
                    data_start = i + 1
                    break
            
            # Parser les époques
            epoch_count = 0
            current_line = data_start
            
            while current_line < len(lines) and epoch_count < max_epochs:
                line = lines[current_line].strip()
                
                if not line:
                    current_line += 1
                    continue
                
                # Ligne d'époque
                if re.match(r'^\d{4}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+[\d.]+\s+\d+', line):
                    parts = line.split()
                    if len(parts) >= 7:
                        try:
                            epoch_time = datetime(
                                int(parts[0]), int(parts[1]), int(parts[2]),
                                int(parts[3]), int(parts[4]), int(float(parts[5]))
                            )
                            
                            num_satellites = int(parts[6])
                            
                            # Lire les satellites
                            satellites = []
                            sat_line = current_line + 1
                            
                            # Les satellites peuvent être sur plusieurs lignes
                            sat_count = 0
                            while sat_count < num_satellites and sat_line < len(lines):
                                sat_line_content = lines[sat_line].strip()
                                if not sat_line_content:
                                    sat_line += 1
                                    continue
                                
                                # Parser les satellites (3 caractères par satellite)
                                for i in range(0, len(sat_line_content), 3):
                                    if sat_count >= num_satellites:
                                        break
                                    sat_code = sat_line_content[i:i+3].strip()
                                    if sat_code:
                                        satellites.append(sat_code)
                                        sat_count += 1
                                
                                sat_line += 1
                            
                            # Compter les systèmes de satellites
                            systems = {}
                            for sat in satellites:
                                system = sat[0] if sat else 'U'
                                systems[system] = systems.get(system, 0) + 1
                            
                            epoch_data = {
                                'time': epoch_time.isoformat(),
                                'satellites': satellites,
                                'num_satellites': len(satellites),
                                'systems': systems
                            }
                            
                            data['epochs_parsed'] += 1
                            data['total_satellites'] += len(satellites)
                            
                            # Mettre à jour le résumé des systèmes
                            for system, count in systems.items():
                                if system not in data['observation_summary']:
                                    data['observation_summary'][system] = 0
                                data['observation_summary'][system] += count
                            
                            epoch_count += 1
                            current_line = sat_line
                            
                        except (ValueError, IndexError) as e:
                            logger.warning(f"⚠️ Erreur parsing époque: {e}")
                            current_line += 1
                else:
                    current_line += 1
            
            data['success'] = True
            logger.info(f"✅ Observations RINEX parsées: {data['epochs_parsed']} époques, {data['total_satellites']} satellites")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing observations RINEX: {e}")
            data['success'] = False
            data['error'] = str(e)
            return data


def extract_rinex_metadata(file_path: str) -> Dict[str, Any]:
    """
    Fonction utilitaire pour extraire les métadonnées d'un fichier RINEX
    
    Args:
        file_path: Chemin vers le fichier RINEX
        
    Returns:
        Dict contenant les métadonnées extraites
    """
    parser = RinexHeaderParser()
    return parser.parse_header(file_path)


def extract_rinex_observations(file_path: str, max_epochs: int = 100) -> Dict[str, Any]:
    """
    Fonction utilitaire pour extraire les observations d'un fichier RINEX
    
    Args:
        file_path: Chemin vers le fichier RINEX
        max_epochs: Nombre maximum d'époques à parser
        
    Returns:
        Dict contenant les données d'observation
    """
    parser = RinexObservationParser()
    return parser.parse_observations(file_path, max_epochs)


# Classes et fonctions pour compatibilité avec le code existant
class RinexParser:
    """Classe de compatibilité pour l'interface existante"""
    
    def __init__(self):
        self.header_parser = RinexHeaderParser()
        self.observation_parser = RinexObservationParser()
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse un fichier RINEX complet"""
        header_data = self.header_parser.parse_header(file_path)
        observation_data = self.observation_parser.parse_observations(file_path)
        
        return {
            'header': header_data,
            'observations': observation_data,
            'file_path': file_path,
            'parsing_timestamp': datetime.now().isoformat()
        }


# Export des classes principales
__all__ = [
    'RinexHeaderParser',
    'RinexObservationParser', 
    'RinexParser',
    'extract_rinex_metadata',
    'extract_rinex_observations'
]

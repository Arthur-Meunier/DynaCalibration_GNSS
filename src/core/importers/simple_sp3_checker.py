# -*- coding: utf-8 -*-
"""
Created on Wed Aug  6 23:35:09 2025

@author: a.meunier
"""

# src/core/importers/simple_sp3_checker.py - Version unifiée et simplifiée

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

class SimpleSP3Checker:
    """
    Vérificateur SP3/CLK unifié et simple
    
    Fonctionnalité unique : vérifier la présence des fichiers SP3 et CLK
    dans le même répertoire que le fichier d'observation Bow/Stern
    """
    
    @staticmethod
    def check_sp3_clk_in_directory(obs_file_path: str) -> Dict[str, any]:
        """
        Vérifie la présence des fichiers SP3/CLK dans le répertoire du fichier d'observation
        
        Args:
            obs_file_path: Chemin vers le fichier d'observation (.o, .25o, etc.)
            
        Returns:
            {
                'sp3_found': bool,
                'clk_found': bool,
                'sp3_files': [list of file paths],
                'clk_files': [list of file paths],
                'search_directory': str,
                'message': str,
                'checked_at': str
            }
        """
        result = {
            'sp3_found': False,
            'clk_found': False,
            'sp3_files': [],
            'clk_files': [],
            'search_directory': '',
            'message': '',
            'checked_at': datetime.now().isoformat()
        }
        
        try:
            # Répertoire de recherche
            obs_path = Path(obs_file_path)
            search_dir = obs_path.parent
            result['search_directory'] = str(search_dir)
            
            if not search_dir.exists():
                result['message'] = f"Répertoire non trouvé: {search_dir}"
                return result
            
            print(f"🔍 Recherche SP3/CLK dans: {search_dir}")
            
            # Patterns de fichiers SP3 (simples et efficaces)
            sp3_patterns = [
                "*.sp3", "*.SP3",           # Extensions directes
                "*ORB.SP3", "*ORB.sp3",     # Format officiel avec ORB
                "IGS*.sp3", "IGS*.SP3",     # Fichiers IGS
                "COD*.sp3", "COD*.SP3"      # Fichiers CODE
            ]
            
            # Patterns de fichiers CLK
            clk_patterns = [
                "*.clk", "*.CLK",           # Extensions directes  
                "*CLK.CLK", "*CLK.clk",     # Format officiel avec CLK
                "IGS*.clk", "IGS*.CLK",     # Fichiers IGS
                "COD*.clk", "COD*.CLK"      # Fichiers CODE
            ]
            
            # Recherche SP3
            sp3_files = []
            for pattern in sp3_patterns:
                found_files = list(search_dir.glob(pattern))
                sp3_files.extend(found_files)
            
            # Supprimer doublons et trier
            sp3_files = sorted(list(set(sp3_files)), key=lambda x: x.name)
            
            # Recherche CLK
            clk_files = []
            for pattern in clk_patterns:
                found_files = list(search_dir.glob(pattern))
                clk_files.extend(found_files)
            
            # Supprimer doublons et trier
            clk_files = sorted(list(set(clk_files)), key=lambda x: x.name)
            
            # Résultats
            result['sp3_found'] = len(sp3_files) > 0
            result['clk_found'] = len(clk_files) > 0
            result['sp3_files'] = [str(f) for f in sp3_files]
            result['clk_files'] = [str(f) for f in clk_files]
            
            # Message de résumé
            sp3_count = len(sp3_files)
            clk_count = len(clk_files)
            
            if result['sp3_found'] and result['clk_found']:
                result['message'] = f"✅ SP3 et CLK trouvés ({sp3_count} SP3, {clk_count} CLK)"
            elif result['sp3_found']:
                result['message'] = f"⚠️ SP3 trouvé mais CLK manquant ({sp3_count} SP3, 0 CLK)"
            elif result['clk_found']:
                result['message'] = f"⚠️ CLK trouvé mais SP3 manquant (0 SP3, {clk_count} CLK)"
            else:
                result['message'] = "❌ Aucun fichier SP3/CLK trouvé"
            
            # Log détaillé
            print(f"📊 Résultats recherche SP3/CLK:")
            print(f"   SP3: {sp3_count} fichier(s) trouvé(s)")
            for sp3_file in sp3_files:
                size_mb = sp3_file.stat().st_size / (1024**2)
                print(f"     • {sp3_file.name} ({size_mb:.1f} MB)")
            
            print(f"   CLK: {clk_count} fichier(s) trouvé(s)")
            for clk_file in clk_files:
                size_mb = clk_file.stat().st_size / (1024**2)
                print(f"     • {clk_file.name} ({size_mb:.1f} MB)")
            
            logger.info(f"SP3/CLK check: {result['message']}")
            
        except Exception as e:
            result['message'] = f"Erreur lors de la recherche: {str(e)}"
            logger.error(f"Erreur SimpleSP3Checker: {e}")
        
        return result
    
    @staticmethod
    def get_simple_status(obs_file_path: str) -> Dict[str, bool]:
        """
        Version ultra-simple qui retourne juste les statuts booléens
        
        Returns:
            {'sp3_ok': bool, 'clk_ok': bool}
        """
        result = SimpleSP3Checker.check_sp3_clk_in_directory(obs_file_path)
        return {
            'sp3_ok': result['sp3_found'],
            'clk_ok': result['clk_found']
        }
    
    @staticmethod
    def get_first_files(obs_file_path: str) -> Dict[str, Optional[str]]:
        """
        Retourne les chemins du premier fichier SP3 et CLK trouvé
        (utile pour les traitements qui n'ont besoin que d'un fichier de chaque)
        
        Returns:
            {'sp3_file': str|None, 'clk_file': str|None}
        """
        result = SimpleSP3Checker.check_sp3_clk_in_directory(obs_file_path)
        return {
            'sp3_file': result['sp3_files'][0] if result['sp3_files'] else None,
            'clk_file': result['clk_files'][0] if result['clk_files'] else None
        }
    
    @staticmethod
    def list_all_sp3_clk_in_directory(directory_path: str) -> Dict[str, List[str]]:
        """
        Liste tous les fichiers SP3/CLK dans un répertoire donné
        (utile pour l'explorateur de fichiers)
        
        Returns:
            {'sp3_files': [list], 'clk_files': [list]}
        """
        # Créer un fichier temporaire fictif pour utiliser la méthode principale
        fake_obs_file = Path(directory_path) / "temp.25o"
        result = SimpleSP3Checker.check_sp3_clk_in_directory(str(fake_obs_file))
        
        return {
            'sp3_files': result['sp3_files'],
            'clk_files': result['clk_files']
        }


# ===== WIDGET SIMPLE POUR L'INTERFACE =====

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

class SimpleSP3StatusWidget(QWidget):
    """Widget simple pour afficher le statut SP3/CLK"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Indicateur SP3
        self.sp3_label = QLabel("SP3: ❓")
        self.sp3_label.setMinimumWidth(80)
        
        # Indicateur CLK  
        self.clk_label = QLabel("CLK: ❓")
        self.clk_label.setMinimumWidth(80)
        
        layout.addWidget(self.sp3_label)
        layout.addWidget(self.clk_label)
        layout.addStretch()
        
        # Style par défaut
        self.update_status(False, False)
    
    def update_status(self, sp3_found: bool, clk_found: bool, 
                     sp3_files: List[str] = None, clk_files: List[str] = None):
        """Met à jour l'affichage du statut"""
        
        # SP3
        if sp3_found:
            self.sp3_label.setText("SP3: ✅")
            self.sp3_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            if sp3_files:
                tooltip = f"Fichiers SP3 trouvés:\n" + "\n".join([Path(f).name for f in sp3_files[:5]])
                if len(sp3_files) > 5:
                    tooltip += f"\n... et {len(sp3_files)-5} autres"
                self.sp3_label.setToolTip(tooltip)
        else:
            self.sp3_label.setText("SP3: ❌")
            self.sp3_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.sp3_label.setToolTip("Aucun fichier SP3 trouvé")
        
        # CLK
        if clk_found:
            self.clk_label.setText("CLK: ✅")
            self.clk_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            if clk_files:
                tooltip = f"Fichiers CLK trouvés:\n" + "\n".join([Path(f).name for f in clk_files[:5]])
                if len(clk_files) > 5:
                    tooltip += f"\n... et {len(clk_files)-5} autres"
                self.clk_label.setToolTip(tooltip)
        else:
            self.clk_label.setText("CLK: ❌")
            self.clk_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.clk_label.setToolTip("Aucun fichier CLK trouvé")
    
    def update_from_obs_file(self, obs_file_path: str):
        """Met à jour le statut basé sur un fichier d'observation"""
        result = SimpleSP3Checker.check_sp3_clk_in_directory(obs_file_path)
        self.update_status(
            result['sp3_found'], 
            result['clk_found'],
            result['sp3_files'],
            result['clk_files']
        )


# ===== INTÉGRATION AVEC APP_DATA =====

def add_simple_sp3_methods_to_app_data(app_data_instance):
    """
    Ajoute les méthodes SP3/CLK simplifiées à app_data
    """
    
    def update_sp3_clk_simple(obs_file_path: str):
        """Méthode simple pour mettre à jour le statut SP3/CLK"""
        if not hasattr(app_data_instance, 'gnss_data'):
            app_data_instance.gnss_data = {}
        
        # Vérification simple
        result = SimpleSP3Checker.check_sp3_clk_in_directory(obs_file_path)
        
        # Sauvegarder dans un format simple
        app_data_instance.gnss_data['sp3_clk_status'] = {
            'sp3_available': result['sp3_found'],
            'clk_available': result['clk_found'],
            'sp3_files_count': len(result['sp3_files']),
            'clk_files_count': len(result['clk_files']),
            'first_sp3_file': result['sp3_files'][0] if result['sp3_files'] else None,
            'first_clk_file': result['clk_files'][0] if result['clk_files'] else None,
            'search_directory': result['search_directory'],
            'message': result['message'],
            'checked_at': result['checked_at']
        }
        
        # Émettre signal si possible
        if hasattr(app_data_instance, 'data_changed'):
            app_data_instance.data_changed.emit("gnss_sp3_simple")
        
        print(f"✅ Statut SP3/CLK simple mis à jour: {result['message']}")
    
    def get_sp3_clk_simple_status() -> Dict[str, bool]:
        """Récupère le statut simple SP3/CLK"""
        if not hasattr(app_data_instance, 'gnss_data'):
            return {'sp3_ok': False, 'clk_ok': False}
        
        status = app_data_instance.gnss_data.get('sp3_clk_status', {})
        return {
            'sp3_ok': status.get('sp3_available', False),
            'clk_ok': status.get('clk_available', False)
        }
    
    # Ajouter les méthodes à l'instance
    app_data_instance.update_sp3_clk_simple = update_sp3_clk_simple
    app_data_instance.get_sp3_clk_simple_status = get_sp3_clk_simple_status
    
    print("🔧 Méthodes SP3/CLK simples ajoutées à app_data")


# ===== EXEMPLES D'UTILISATION =====

def exemple_utilisation_simple():
    """Exemples d'utilisation du vérificateur simplifié"""
    
    # Chemin vers votre fichier d'observation Bow/Stern
    obs_file = "C:/1-Data/01-Projet/ProjetPY/Thialf/2/Bow-9205.25o"
    
    print("=" * 60)
    print("🧪 TEST SIMPLE SP3CHECKER")
    print("=" * 60)
    
    # 1. Vérification complète
    print("\n1️⃣ Vérification complète:")
    result = SimpleSP3Checker.check_sp3_clk_in_directory(obs_file)
    print(f"   Résultat: {result['message']}")
    print(f"   SP3 trouvé: {result['sp3_found']}")
    print(f"   CLK trouvé: {result['clk_found']}")
    
    # 2. Statut simple
    print("\n2️⃣ Statut simple:")
    simple = SimpleSP3Checker.get_simple_status(obs_file)
    print(f"   SP3: {'✅' if simple['sp3_ok'] else '❌'}")
    print(f"   CLK: {'✅' if simple['clk_ok'] else '❌'}")
    
    # 3. Premiers fichiers trouvés
    print("\n3️⃣ Premiers fichiers:")
    first_files = SimpleSP3Checker.get_first_files(obs_file)
    print(f"   Premier SP3: {Path(first_files['sp3_file']).name if first_files['sp3_file'] else 'Aucun'}")
    print(f"   Premier CLK: {Path(first_files['clk_file']).name if first_files['clk_file'] else 'Aucun'}")
    
    print("=" * 60)


def exemple_integration_app_data():
    """Exemple d'intégration avec app_data"""
    
    # Mock app_data
    class MockAppData:
        def __init__(self):
            self.gnss_data = {}
    
    app_data = MockAppData()
    
    # Ajouter les méthodes simples
    add_simple_sp3_methods_to_app_data(app_data)
    
    # Test
    obs_file = "C:/1-Data/01-Projet/ProjetPY/Thialf/2/Bow-9205.25o"
    app_data.update_sp3_clk_simple(obs_file)
    
    # Récupérer le statut
    status = app_data.get_sp3_clk_simple_status()
    print(f"Statut depuis app_data: {status}")


if __name__ == "__main__":
    # Test direct
    exemple_utilisation_simple()
    
    print("\n" + "=" * 60)
    print("🔗 Test intégration app_data")
    print("=" * 60)
    
    exemple_integration_app_data()
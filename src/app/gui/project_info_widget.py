# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 22:19:30 2025

@author: a.meunier
"""

# project_info_widget.py
# Widget d'informations de projet pour la page d'accueil

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime


class ProjectInfoWidget(QWidget):
    """Widget d'affichage des informations du projet courant"""
    
    # Signaux émis par ce widget
    edit_requested = pyqtSignal()
    
    def __init__(self, parent=None, progress_manager=None, app_data=None):
        super().__init__(parent)
        
        # Données du projet
        self.project_data = None
        self.info_labels = {}
        
        # Références pour synchronisation avec le dashboard
        self.progress_manager = progress_manager
        self.app_data = app_data
        
        # === CORRECTION: Initialiser les références à None ===
        self.project_name_label = None
        self.project_description_label = None
        self.edit_button = None
        
        try:
            self.setup_ui()
            self.apply_styles()
            self.reset_to_default()
            print("✅ ProjectInfoWidget initialisé avec succès")
        except Exception as e:
            print(f"❌ Erreur initialisation ProjectInfoWidget: {e}")
            import traceback
            traceback.print_exc()
            # Créer une interface minimale en cas d'erreur
            self.setup_fallback_ui()
    
    def setup_ui(self):
        """Configure l'interface du widget"""
        # Groupe principal
        self.info_group = QGroupBox("📋 INFORMATIONS PROJET")
        self.info_group.setObjectName("infoGroup")
        
        info_layout = QVBoxLayout(self.info_group)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(15, 20, 15, 15)
        
        # === EN-TÊTE AVEC NOM DU PROJET ===
        header_section = self.create_header_section()
        info_layout.addWidget(header_section)
        
        # === INFORMATIONS PRINCIPALES ===
        main_info_section = self.create_main_info_section()
        info_layout.addLayout(main_info_section)
        
        # === SÉPARATEUR ===
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #555558; margin: 5px 0px;")
        info_layout.addWidget(separator)
        
        # === STATISTIQUES DE PROGRESSION ===
        progress_section = self.create_progress_section()
        info_layout.addLayout(progress_section)
        
        # === BOUTON D'ÉDITION ===
        edit_section = self.create_edit_section()
        info_layout.addLayout(edit_section)
        
        # Espace flexible
        info_layout.addStretch()
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.info_group)
    
    def create_header_section(self):
        """Crée la section d'en-tête avec le nom du projet"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(3)
        
        # === CORRECTION: S'assurer que les labels sont créés ===
        try:
            # Nom du projet (titre principal)
            self.project_name_label = QLabel("Aucun projet")
            self.project_name_label.setObjectName("projectTitle")
            self.project_name_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.project_name_label.setAlignment(Qt.AlignCenter)
            self.project_name_label.setWordWrap(True)
            
            # Description courte
            self.project_description_label = QLabel("Veuillez créer ou ouvrir un projet")
            self.project_description_label.setObjectName("projectDescription")
            self.project_description_label.setFont(QFont("Segoe UI", 9))
            self.project_description_label.setAlignment(Qt.AlignCenter)
            self.project_description_label.setWordWrap(True)
            
            header_layout.addWidget(self.project_name_label)
            header_layout.addWidget(self.project_description_label)
            
            print("✅ Labels d'en-tête créés avec succès")
            
        except Exception as e:
            print(f"❌ Erreur création labels d'en-tête: {e}")
            # Créer des labels de secours
            self.project_name_label = QLabel("Erreur initialisation")
            self.project_description_label = QLabel("Erreur initialisation")
            header_layout.addWidget(self.project_name_label)
            header_layout.addWidget(self.project_description_label)
        
        return header_frame
    
    def create_main_info_section(self):
        """Crée la section des informations principales"""
        layout = QGridLayout()
        layout.setSpacing(8)
        layout.setColumnStretch(1, 1)  # Deuxième colonne extensible
        
        # Configuration des champs d'information
        info_fields = [
            ("vessel", "🚢 Navire:", "Non défini"),
            ("company", "🏢 Société:", "Non définie"),
            ("engineer", "👤 Ingénieur:", "Non défini"),
            ("created", "📅 Créé:", "Non défini"),
            ("last_modified", "🔄 Modifié:", "Non défini"),
            ("version", "📌 Version:", "Non définie")
        ]
        
        try:
            for row, (key, label_text, default_value) in enumerate(info_fields):
                # Label du champ
                label = QLabel(label_text)
                label.setObjectName("fieldLabel")
                label.setFont(QFont("Segoe UI", 9))
                
                # Valeur du champ
                value_label = QLabel(default_value)
                value_label.setObjectName("fieldValue")
                value_label.setFont(QFont("Segoe UI", 9))
                value_label.setWordWrap(True)
                
                # Stocker la référence
                self.info_labels[key] = value_label
                
                # Ajouter au layout
                layout.addWidget(label, row, 0, Qt.AlignTop)
                layout.addWidget(value_label, row, 1, Qt.AlignTop)
            
            print("✅ Section informations principales créée")
            
        except Exception as e:
            print(f"❌ Erreur création section informations: {e}")
        
        return layout
    
    def create_progress_section(self):
        """Crée la section des statistiques de progression"""
        layout = QVBoxLayout()
        layout.setSpacing(6)
        
        try:
            # Titre de la section
            progress_title = QLabel("📊 Progression du Workflow")
            progress_title.setObjectName("sectionTitle")
            progress_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
            layout.addWidget(progress_title)
            
            # Grille pour les métriques
            metrics_layout = QGridLayout()
            metrics_layout.setSpacing(8)
            
            # Métriques de progression
            metrics_fields = [
                ("modules_completed", "Modules terminés:", "0/4"),
                ("total_progress", "Progression globale:", "0%"),
                ("last_save", "Dernière sauvegarde:", "Jamais"),
                ("status", "Statut:", "Non démarré")
            ]
            
            for row, (key, label_text, default_value) in enumerate(metrics_fields):
                # Label
                label = QLabel(label_text)
                label.setObjectName("metricLabel")
                label.setFont(QFont("Segoe UI", 8))
                
                # Valeur
                value_label = QLabel(default_value)
                value_label.setObjectName("metricValue")
                value_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
                
                # Stocker la référence
                self.info_labels[key] = value_label
                
                # Ajouter au layout
                metrics_layout.addWidget(label, row, 0)
                metrics_layout.addWidget(value_label, row, 1)
            
            layout.addLayout(metrics_layout)
            print("✅ Section progression créée")
            
        except Exception as e:
            print(f"❌ Erreur création section progression: {e}")
        
        return layout
    
    def create_edit_section(self):
        """Crée la section avec le bouton d'édition"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 8, 0, 0)
        
        try:
            # Bouton d'édition
            self.edit_button = QPushButton("✏️ Éditer le Projet")
            self.edit_button.setObjectName("editButton")
            self.edit_button.clicked.connect(self.edit_requested.emit)
            self.edit_button.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.edit_button.setMinimumHeight(32)
            self.edit_button.setEnabled(False)  # Désactivé par défaut
            
            layout.addStretch()
            layout.addWidget(self.edit_button)
            layout.addStretch()
            
            print("✅ Bouton d'édition créé")
            
        except Exception as e:
            print(f"❌ Erreur création bouton d'édition: {e}")
            # Bouton de secours
            self.edit_button = QPushButton("Erreur")
            layout.addWidget(self.edit_button)
        
        return layout
    
    def setup_fallback_ui(self):
        """Interface de secours en cas d'erreur"""
        try:
            fallback_layout = QVBoxLayout(self)
            
            error_label = QLabel("❌ ERREUR PROJECTINFOWIDGET\n\nImpossible d'initialiser l'interface normale.\nMode de secours activé.")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d30;
                    border: 2px solid #ff6b6b;
                    border-radius: 8px;
                    padding: 20px;
                    color: #ffffff;
                    font-size: 12px;
                }
            """)
            
            # Créer les attributs de base pour éviter les erreurs
            self.project_name_label = QLabel("Mode de secours")
            self.project_description_label = QLabel("Erreur d'initialisation")
            self.edit_button = QPushButton("Non disponible")
            self.edit_button.setEnabled(False)
            
            fallback_layout.addWidget(error_label)
            fallback_layout.addWidget(self.project_name_label)
            fallback_layout.addWidget(self.project_description_label)
            fallback_layout.addWidget(self.edit_button)
            
            print("⚠️ Interface de secours ProjectInfoWidget activée")
            
        except Exception as e:
            print(f"❌ Erreur critique setup_fallback_ui: {e}")
    
    def apply_styles(self):
        """Applique les styles du thème sombre"""
        try:
            self.setStyleSheet("""
                /* === GROUPBOX === */
                QGroupBox {
                    font-weight: bold;
                    font-size: 11px;
                    color: #ffffff;
                    border: 2px solid #0d7377;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 8px;
                    background-color: #2d2d30;
                }
                
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 15px;
                    padding: 0 8px 0 8px;
                    background-color: #2d2d30;
                    color: #ffffff;
                }
                
                /* === EN-TÊTE === */
                #headerFrame {
                    background-color: rgba(13, 115, 119, 0.1);
                    border: 1px solid #0d7377;
                    border-radius: 6px;
                    padding: 8px;
                    margin-bottom: 8px;
                }
                
                #projectTitle {
                    color: #ffffff;
                    background: transparent;
                }
                
                #projectDescription {
                    color: #d4d4d4;
                    background: transparent;
                }
                
                /* === CHAMPS D'INFORMATION === */
                #fieldLabel {
                    color: #b0b0b0;
                    background: transparent;
                    font-weight: bold;
                }
                
                #fieldValue {
                    color: #ffffff;
                    background: transparent;
                    padding-left: 8px;
                }
                
                /* === MÉTRIQUES === */
                #sectionTitle {
                    color: #ffffff;
                    background: transparent;
                    margin-bottom: 5px;
                }
                
                #metricLabel {
                    color: #b0b0b0;
                    background: transparent;
                }
                
                #metricValue {
                    color: #ffffff;
                    background: transparent;
                    padding-left: 8px;
                }
                
                /* === BOUTON D'ÉDITION === */
                #editButton {
                    background-color: #0d7377;
                    color: #ffffff;
                    border: 1px solid #0d7377;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                
                #editButton:hover {
                    background-color: #14a085;
                    border-color: #14a085;
                }
                
                #editButton:pressed {
                    background-color: #0a5d61;
                }
                
                #editButton:disabled {
                    background-color: #2a2a2a;
                    color: #666666;
                    border-color: #444444;
                }
            """)
            print("✅ Styles appliqués")
        except Exception as e:
            print(f"❌ Erreur application styles: {e}")
    
    # === MÉTHODES DE MISE À JOUR ===
    
    def update_project_info(self, project_data):
        """Met à jour les informations du projet"""
        if not project_data:
            self.reset_to_default()
            return
        
        self.project_data = project_data
        
        try:
            # Récupérer les métadonnées
            metadata = project_data.get('metadata', {})
            
            # === CORRECTION: Vérifier que les labels existent ===
            if not self.project_name_label or not self.project_description_label:
                print("❌ Labels non initialisés, impossible de mettre à jour")
                return
            
            # Mise à jour du nom et de la description
            project_name = metadata.get('vessel', 'Projet sans nom')
            if project_name == 'Projet sans nom' and 'name' in metadata:
                project_name = metadata['name']
            
            self.project_name_label.setText(project_name)
            
            description = metadata.get('description', 'Aucune description')
            if len(description) > 100:
                description = description[:97] + "..."
            self.project_description_label.setText(description)
            
            # Mise à jour des champs d'information
            if 'vessel' in self.info_labels:
                self.info_labels['vessel'].setText(metadata.get('vessel', 'Non défini'))
            if 'company' in self.info_labels:
                self.info_labels['company'].setText(metadata.get('company', 'Non définie'))
            if 'engineer' in self.info_labels:
                self.info_labels['engineer'].setText(metadata.get('engineer', 'Non défini'))
            if 'version' in self.info_labels:
                self.info_labels['version'].setText(metadata.get('version', '1.0'))
            
            # Formatage des dates
            self.update_date_field('created', metadata.get('created', ''))
            self.update_date_field('last_modified', metadata.get('last_modified', ''))
            
            # Mise à jour des métriques de progression
            self.update_progress_metrics(project_data)
            
            # log désactivé
            
        except Exception as e:
            print(f"[ERREUR] Mise à jour des informations projet: {e}")
            self.reset_to_default()
    
    def update_date_field(self, field_name, date_value):
        """Met à jour un champ de date avec formatage"""
        try:
            if field_name in self.info_labels:
                if date_value:
                    try:
                        # Essayer de parser la date ISO
                        dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                        self.info_labels[field_name].setText(dt.strftime('%d/%m/%Y %H:%M'))
                    except:
                        self.info_labels[field_name].setText(date_value[:10] if len(date_value) > 10 else date_value)
                else:
                    self.info_labels[field_name].setText('Non défini')
        except Exception as e:
            print(f"❌ Erreur mise à jour date {field_name}: {e}")
    
    def update_progress_metrics(self, project_data):
        """Met à jour les métriques de progression en utilisant ProgressManager"""
        try:
            # Utiliser ProgressManager si disponible pour cohérence avec le dashboard
            if hasattr(self, 'progress_manager') and self.progress_manager and hasattr(self, 'app_data') and self.app_data:
                all_progress_details = self.progress_manager.calculate_all_progress(self.app_data)
                
                # Calculer les modules terminés basés sur ProgressManager
                completed_modules = 0
                total_progress = 0
                
                for module_name, module_data in all_progress_details.items():
                    if isinstance(module_data, dict) and 'progress' in module_data:
                        progress = module_data['progress']
                        total_progress += progress
                        if progress >= 100:
                            completed_modules += 1
                
                # Mettre à jour l'affichage
                if 'modules_completed' in self.info_labels:
                    self.info_labels['modules_completed'].setText(f"{completed_modules}/4")
                
                if 'total_progress' in self.info_labels:
                    avg_progress = total_progress / len(all_progress_details) if all_progress_details else 0
                    self.info_labels['total_progress'].setText(f"{avg_progress:.0f}%")
                
                # Silencer: ne pas imprimer systématiquement
                if not hasattr(self, '_last_project_info_values'):
                    self._last_project_info_values = {}
                self._last_project_info_values['values'] = (completed_modules, avg_progress)
                
            else:
                # Fallback avec l'ancienne méthode
                workflow = project_data.get('workflow_status', {})
                modules = ['dimcon', 'gnss', 'observation', 'qc']
                completed_modules = sum(1 for module in modules if workflow.get(module, {}).get('completed', False))
                
                if 'modules_completed' in self.info_labels:
                    self.info_labels['modules_completed'].setText(f"{completed_modules}/4")
                
                # Calculer la progression globale
                progress_sum = 0
                for module in modules:
                    progress_sum += workflow.get(module, {}).get('progress', 0)
                
                global_progress = progress_sum / len(modules) if modules else 0
                if 'total_progress' in self.info_labels:
                    self.info_labels['total_progress'].setText(f"{global_progress:.0f}%")
            
            # Dernière sauvegarde
            last_modified = project_data.get('metadata', {}).get('last_modified', '')
            if 'last_save' in self.info_labels:
                if last_modified:
                    try:
                        dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                        self.info_labels['last_save'].setText(dt.strftime('%H:%M'))
                    except:
                        self.info_labels['last_save'].setText('Récemment')
                else:
                    self.info_labels['last_save'].setText('Jamais')
            
            # Statut global - utiliser avg_progress calculé par ProgressManager
            if 'status' in self.info_labels:
                if avg_progress >= 80:
                    status = "🟢 Prêt"
                    status_color = "#28a745"
                elif avg_progress >= 50:
                    status = "🟡 En cours"
                    status_color = "#ffc107"
                elif avg_progress >= 20:
                    status = "🔄 Configuration"
                    status_color = "#007acc"
                else:
                    status = "🔴 Démarrage"
                    status_color = "#dc3545"
                
                self.info_labels['status'].setText(status)
                self.info_labels['status'].setStyleSheet(f"color: {status_color}; font-weight: bold;")
            
        except Exception as e:
            print(f"[ERREUR] Calcul des métriques: {e}")
    
    def reset_to_default(self):
        """Remet le widget à son état par défaut"""
        try:
            # Reset du nom et description si les labels existent
            if self.project_name_label:
                self.project_name_label.setText("Aucun projet")
            if self.project_description_label:
                self.project_description_label.setText("Veuillez créer ou ouvrir un projet")
            
            # Reset des champs d'information
            default_values = {
                'vessel': 'Non défini',
                'company': 'Non définie',
                'engineer': 'Non défini',
                'created': 'Non défini',
                'last_modified': 'Non défini',
                'version': 'Non définie'
            }
            
            for key, default_value in default_values.items():
                if key in self.info_labels:
                    self.info_labels[key].setText(default_value)
            
            # Reset des métriques
            metrics_defaults = {
                'modules_completed': '0/4',
                'total_progress': '0%',
                'last_save': 'Jamais',
                'status': 'Non démarré'
            }
            
            for key, default_value in metrics_defaults.items():
                if key in self.info_labels:
                    self.info_labels[key].setText(default_value)
                    self.info_labels[key].setStyleSheet("")  # Reset du style
            
            # Désactiver le bouton d'édition
            if self.edit_button:
                self.edit_button.setEnabled(False)
            
            # Reset des données
            self.project_data = None
            
            print("[PROJECT_INFO] Reset à l'état par défaut")
            
        except Exception as e:
            print(f"❌ Erreur reset_to_default: {e}")
    
    def enable_edit_button(self, enabled):
        """Active ou désactive le bouton d'édition"""
        try:
            if self.edit_button:
                self.edit_button.setEnabled(enabled)
        except Exception as e:
            print(f"❌ Erreur enable_edit_button: {e}")
    
    def set_project_name(self, name):
        """Met à jour le nom du projet"""
        try:
            if self.project_name_label:
                self.project_name_label.setText(name or "Projet sans nom")
        except Exception as e:
            print(f"❌ Erreur set_project_name: {e}")
    
    def set_project_description(self, description):
        """Met à jour la description du projet"""
        try:
            if self.project_description_label:
                if description and len(description) > 100:
                    description = description[:97] + "..."
                self.project_description_label.setText(description or "Aucune description")
        except Exception as e:
            print(f"❌ Erreur set_project_description: {e}")
    
    def get_project_info_summary(self):
        """Retourne un résumé des informations pour l'application principale"""
        try:
            if not self.project_data:
                return None
            
            summary = {}
            if self.project_name_label:
                summary['name'] = self.project_name_label.text()
            if self.project_description_label:
                summary['description'] = self.project_description_label.text()
            
            # Ajouter les autres informations si disponibles
            for key in ['company', 'vessel', 'engineer', 'total_progress', 'status']:
                if key in self.info_labels:
                    summary[key] = self.info_labels[key].text()
            
            return summary
            
        except Exception as e:
            print(f"❌ Erreur get_project_info_summary: {e}")
            return None


# Test du widget si exécuté directement
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Créer une fenêtre de test
    widget = ProjectInfoWidget()
    
    # Connexions de test
    widget.edit_requested.connect(lambda: print("Signal: Édition demandée"))
    
    # Fenêtre de test
    widget.setWindowTitle("Test Project Info Widget")
    widget.resize(350, 600)
    widget.show()
    
    # ✅ SUPPRESSION DES DONNÉES FACTICES
    # Le widget affiche maintenant les vraies données du projet
    # ou reste vide si aucun projet n'est chargé
    
    sys.exit(app.exec_())
# src/core/reports/report_generator.py

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging

# Imports pour génération PDF
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Imports matplotlib pour graphiques
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
import base64

logger = logging.getLogger(__name__)

@dataclass
class ReportConfig:
    """Configuration pour la génération de rapports"""
    template_type: str = "complete"  # complete, progress, qc, technical
    include_charts: bool = True
    include_logs: bool = True
    include_matrices: bool = False
    chart_style: str = "professional"  # professional, colorful, minimal
    logo_path: Optional[str] = None
    company_info: Dict[str, str] = None
    
    def __post_init__(self):
        if self.company_info is None:
            self.company_info = {
                'name': 'Calibration Services',
                'address': '',
                'phone': '',
                'email': ''
            }

@dataclass 
class ReportData:
    """Structure des données pour un rapport"""
    project_metadata: Dict[str, Any]
    workflow_status: Dict[str, Any]
    qc_metrics: Dict[str, Any]
    sensor_data: List[Dict[str, Any]]
    calculation_results: Dict[str, Any] = None
    logs_summary: List[Dict[str, Any]] = None
    generated_at: str = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now(timezone.utc).isoformat()

class ReportGenerator:
    """
    Générateur de rapports PDF professionnel pour les projets de calibration
    """
    
    def __init__(self, config: ReportConfig = None):
        self.config = config or ReportConfig()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        logger.info("[OK] ReportGenerator initialisé")
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour les rapports"""
        # Style titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=1  # Centré
        ))
        
        # Style sous-titre
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=15,
            spaceAfter=10
        ))
        
        # Style métrique
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#27ae60'),
            alignment=1,
            fontName='Helvetica-Bold'
        ))
        
        # Style note
        self.styles.add(ParagraphStyle(
            name='Note',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            fontName='Helvetica-Oblique'
        ))
    
    def generate_complete_report(self, report_data: ReportData, output_path: str) -> bool:
        """
        Génère un rapport de calibration complet
        
        Args:
            report_data: Données du rapport
            output_path: Chemin de sortie du PDF
            
        Returns:
            bool: Succès de la génération
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # Page de garde
            story.extend(self._build_cover_page(report_data))
            story.append(PageBreak())
            
            # Résumé exécutif
            story.extend(self._build_executive_summary(report_data))
            story.append(PageBreak())
            
            # Détails du projet
            story.extend(self._build_project_details(report_data))
            
            # Progression du workflow
            story.extend(self._build_workflow_progress(report_data))
            
            # Métriques de qualité
            story.extend(self._build_quality_metrics(report_data))
            
            # Données des capteurs
            if report_data.sensor_data:
                story.extend(self._build_sensor_analysis(report_data))
            
            # Résultats de calculs
            if report_data.calculation_results and self.config.include_matrices:
                story.append(PageBreak())
                story.extend(self._build_calculation_results(report_data))
            
            # Logs et historique
            if report_data.logs_summary and self.config.include_logs:
                story.append(PageBreak())
                story.extend(self._build_logs_section(report_data))
            
            # Annexes
            story.append(PageBreak())
            story.extend(self._build_appendices(report_data))
            
            # Générer le PDF
            doc.build(story)
            
            logger.info(f"[OK] Rapport complet généré: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Échec génération rapport: {e}")
            return False
    
    def _build_cover_page(self, data: ReportData) -> List[Flowable]:
        """Construit la page de garde"""
        content = []
        
        # Logo si disponible
        if self.config.logo_path and Path(self.config.logo_path).exists():
            content.append(Image(self.config.logo_path, width=2*inch, height=1*inch))
            content.append(Spacer(1, 0.5*inch))
        
        # Titre principal
        title = f"Rapport de Calibration<br/>{data.project_metadata.get('vessel', 'Navire')}"
        content.append(Paragraph(title, self.styles['CustomTitle']))
        content.append(Spacer(1, 0.5*inch))
        
        # Informations projet
        project_info = [
            ['Compagnie:', data.project_metadata.get('company', 'N/A')],
            ['Navire:', data.project_metadata.get('vessel', 'N/A')],
            ['Ingénieur:', data.project_metadata.get('engineer', 'N/A')],
            ['Date de création:', self._format_date(data.project_metadata.get('created'))],
            ['Date du rapport:', self._format_date(data.generated_at)]
        ]
        
        info_table = Table(project_info, colWidths=[3*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(info_table)
        
        content.append(Spacer(1, 2*inch))
        
        # Score global si disponible
        global_score = data.qc_metrics.get('global_score', 0)
        if global_score > 0:
            score_text = f"Score de Qualité Global: {global_score:.1f}%"
            content.append(Paragraph(score_text, self.styles['MetricValue']))
        
        return content
    
    def _build_executive_summary(self, data: ReportData) -> List[Flowable]:
        """Construit le résumé exécutif"""
        content = []
        
        content.append(Paragraph("Résumé Exécutif", self.styles['CustomHeading']))
        
        # Analyse automatique du projet
        workflow = data.workflow_status
        completed_steps = sum(1 for step in workflow.values() 
                            if isinstance(step, dict) and step.get('completed', False))
        total_steps = len(workflow)
        completion_rate = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        summary_text = f"""
        Ce rapport présente les résultats de la calibration des capteurs de navigation 
        pour le navire {data.project_metadata.get('vessel', 'N/A')} de la compagnie 
        {data.project_metadata.get('company', 'N/A')}.
        
        <b>État d'avancement :</b> {completed_steps}/{total_steps} étapes complétées ({completion_rate:.1f}%)
        
        <b>Score de qualité global :</b> {data.qc_metrics.get('global_score', 0):.1f}%
        
        <b>Nombre de capteurs analysés :</b> {len(data.sensor_data)}
        
        <b>Statut du projet :</b> {'Terminé' if completion_rate == 100 else 'En cours'}
        """
        
        content.append(Paragraph(summary_text, self.styles['Normal']))
        content.append(Spacer(1, 0.3*inch))
        
        # Recommandations
        content.append(Paragraph("Recommandations", self.styles['CustomHeading']))
        
        recommendations = self._generate_recommendations(data)
        for rec in recommendations:
            content.append(Paragraph(f"• {rec}", self.styles['Normal']))
        
        return content
    
    def _build_project_details(self, data: ReportData) -> List[Flowable]:
        """Construit la section détails du projet"""
        content = []
        
        content.append(Paragraph("Détails du Projet", self.styles['CustomHeading']))
        
        # Table des métadonnées
        metadata = data.project_metadata
        details_data = [
            ['Paramètre', 'Valeur'],
            ['Nom du projet', metadata.get('name', 'N/A')],
            ['Version', metadata.get('version', 'N/A')],
            ['Description', metadata.get('description', 'Aucune description')],
            ['Date de création', self._format_date(metadata.get('created'))],
            ['Dernière modification', self._format_date(metadata.get('last_modified'))],
        ]
        
        details_table = Table(details_data, colWidths=[4*cm, 8*cm])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(details_table)
        content.append(Spacer(1, 0.3*inch))
        
        return content
    
    def _build_workflow_progress(self, data: ReportData) -> List[Flowable]:
        """Construit la section progression du workflow"""
        content = []
        
        content.append(Paragraph("Progression du Workflow", self.styles['CustomHeading']))
        
        workflow = data.workflow_status
        workflow_data = [['Étape', 'Progression', 'Statut', 'Commentaires']]
        
        step_names = {
            'dimcon': 'Configuration Dimcon',
            'gnss': 'Configuration GNSS', 
            'observation': 'Acquisition Données',
            'qc': 'Contrôle Qualité'
        }
        
        for step_key, step_data in workflow.items():
            if isinstance(step_data, dict):
                step_name = step_names.get(step_key, step_key.title())
                progress = step_data.get('progress', 0)
                completed = step_data.get('completed', False)
                status = 'Complété' if completed else f'{progress}%'
                
                # Commentaires basés sur le statut
                if completed:
                    comment = 'Étape terminée avec succès'
                elif progress > 50:
                    comment = 'En cours - Avancement satisfaisant'
                elif progress > 0:
                    comment = 'En cours - Début d\'avancement'
                else:
                    comment = 'Non démarré'
                
                workflow_data.append([step_name, f'{progress}%', status, comment])
        
        workflow_table = Table(workflow_data, colWidths=[3*cm, 2*cm, 2*cm, 5*cm])
        workflow_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980b9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(workflow_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Graphique de progression si demandé
        if self.config.include_charts:
            chart_path = self._create_workflow_chart(workflow)
            if chart_path:
                content.append(Image(chart_path, width=6*inch, height=3*inch))
                content.append(Spacer(1, 0.2*inch))
        
        return content
    
    def _build_quality_metrics(self, data: ReportData) -> List[Flowable]:
        """Construit la section métriques de qualité"""
        content = []
        
        content.append(Paragraph("Métriques de Qualité", self.styles['CustomHeading']))
        
        metrics = data.qc_metrics
        
        # Table des métriques
        metrics_data = [
            ['Métrique', 'Valeur', 'Évaluation'],
            ['Score Global', f"{metrics.get('global_score', 0):.1f}%", 
             self._evaluate_score(metrics.get('global_score', 0))],
            ['Score GNSS', f"{metrics.get('gnss_score', 0):.1f}%",
             self._evaluate_score(metrics.get('gnss_score', 0))],
            ['Score Capteurs', f"{metrics.get('sensors_score', 0):.1f}%",
             self._evaluate_score(metrics.get('sensors_score', 0))]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[4*cm, 3*cm, 5*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(metrics_table)
        content.append(Spacer(1, 0.3*inch))
        
        return content
    
    def _build_sensor_analysis(self, data: ReportData) -> List[Flowable]:
        """Construit l'analyse des capteurs"""
        content = []
        
        content.append(Paragraph("Analyse des Capteurs", self.styles['CustomHeading']))
        
        # Résumé des capteurs
        sensor_summary = {}
        for sensor in data.sensor_data:
            sensor_type = sensor.get('type', 'Unknown')
            sensor_summary[sensor_type] = sensor_summary.get(sensor_type, 0) + 1
        
        summary_text = f"<b>Nombre total de capteurs:</b> {len(data.sensor_data)}<br/>"
        for sensor_type, count in sensor_summary.items():
            summary_text += f"<b>{sensor_type}:</b> {count} capteur(s)<br/>"
        
        content.append(Paragraph(summary_text, self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Table détaillée des capteurs
        if data.sensor_data:
            sensor_data = [['ID Capteur', 'Type', 'Statut', 'Qualité']]
            
            for sensor in data.sensor_data:
                sensor_id = sensor.get('id', 'N/A')
                sensor_type = sensor.get('type', 'N/A')
                status = 'Configuré' if sensor.get('configured', False) else 'En attente'
                quality = sensor.get('quality_score', 'N/A')
                if isinstance(quality, (int, float)):
                    quality = f"{quality:.1f}%"
                
                sensor_data.append([sensor_id, sensor_type, status, str(quality)])
            
            sensor_table = Table(sensor_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2*cm])
            sensor_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(sensor_table)
        
        return content
    
    def _build_calculation_results(self, data: ReportData) -> List[Flowable]:
        """Construit la section résultats de calculs"""
        content = []
        
        content.append(Paragraph("Résultats de Calculs", self.styles['CustomHeading']))
        
        if not data.calculation_results:
            content.append(Paragraph("Aucun résultat de calcul disponible.", self.styles['Normal']))
            return content
        
        # Résumé des calculs
        calc_summary = f"""
        Les calculs de calibration ont été effectués sur {len(data.calculation_results)} capteur(s).
        Les matrices de rotation et les corrections ont été calculées selon la convention ENU.
        """
        content.append(Paragraph(calc_summary, self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Détails par capteur
        for sensor_id, results in data.calculation_results.items():
            content.append(Paragraph(f"Capteur: {sensor_id}", self.styles['Heading2']))
            
            # Statistiques si disponibles
            if 'statistics' in results:
                stats = results['statistics']
                stats_text = f"""
                <b>Points de données:</b> {stats.get('data_points', 'N/A')}<br/>
                <b>Score de qualité:</b> {stats.get('quality_score', 0):.2f}<br/>
                """
                
                if 'pitch_std' in stats:
                    stats_text += f"<b>Écart-type Pitch:</b> {stats['pitch_std']:.4f}°<br/>"
                if 'roll_std' in stats:
                    stats_text += f"<b>Écart-type Roll:</b> {stats['roll_std']:.4f}°<br/>"
                if 'heading_std' in stats:
                    stats_text += f"<b>Écart-type Heading:</b> {stats['heading_std']:.4f}°<br/>"
                
                content.append(Paragraph(stats_text, self.styles['Normal']))
            
            content.append(Spacer(1, 0.1*inch))
        
        return content
    
    def _build_logs_section(self, data: ReportData) -> List[Flowable]:
        """Construit la section des logs"""
        content = []
        
        content.append(Paragraph("Historique et Logs", self.styles['CustomHeading']))
        
        if not data.logs_summary:
            content.append(Paragraph("Aucun log disponible.", self.styles['Normal']))
            return content
        
        # Table des logs récents
        logs_data = [['Horodatage', 'Niveau', 'Message']]
        
        for log_entry in data.logs_summary[-20:]:  # 20 derniers logs
            timestamp = log_entry.get('timestamp', '')
            level = log_entry.get('level', 'INFO')
            message = log_entry.get('message', '')[:50] + '...' if len(log_entry.get('message', '')) > 50 else log_entry.get('message', '')
            
            logs_data.append([self._format_date(timestamp), level, message])
        
        logs_table = Table(logs_data, colWidths=[3.5*cm, 1.5*cm, 7*cm])
        logs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(logs_table)
        
        return content
    
    def _build_appendices(self, data: ReportData) -> List[Flowable]:
        """Construit les annexes"""
        content = []
        
        content.append(Paragraph("Annexes", self.styles['CustomHeading']))
        
        # Annexe A: Configuration technique
        content.append(Paragraph("Annexe A: Configuration Technique", self.styles['Heading2']))
        
        tech_info = f"""
        <b>Convention de coordonnées:</b> ENU (East-North-Up)<br/>
        <b>Système de référence:</b> Navigation locale<br/>
        <b>Précision GNSS:</b> Centimétrique<br/>
        <b>Fréquence d'échantillonnage:</b> Variable selon capteur<br/>
        <b>Méthode de calcul:</b> Matrices de rotation avec stabilisation Cholesky<br/>
        """
        content.append(Paragraph(tech_info, self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Annexe B: Contact et support
        content.append(Paragraph("Annexe B: Contact et Support", self.styles['Heading2']))
        
        contact_info = f"""
        <b>Société:</b> {self.config.company_info.get('name', 'N/A')}<br/>
        <b>Adresse:</b> {self.config.company_info.get('address', 'N/A')}<br/>
        <b>Téléphone:</b> {self.config.company_info.get('phone', 'N/A')}<br/>
        <b>Email:</b> {self.config.company_info.get('email', 'N/A')}<br/>
        <b>Date de génération:</b> {self._format_date(data.generated_at)}<br/>
        """
        content.append(Paragraph(contact_info, self.styles['Normal']))
        
        return content
    
    # Méthodes utilitaires
    
    def _format_date(self, iso_date: str) -> str:
        """Formate une date ISO en format lisible"""
        if not iso_date:
            return "N/A"
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y à %H:%M")
        except:
            return iso_date
    
    def _evaluate_score(self, score: float) -> str:
        """Évalue un score et retourne une appréciation"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Très bien"
        elif score >= 60:
            return "Satisfaisant"
        elif score >= 40:
            return "Améliorable"
        else:
            return "Insuffisant"
    
    def _generate_recommendations(self, data: ReportData) -> List[str]:
        """Génère des recommandations automatiques basées sur les données"""
        recommendations = []
        
        # Analyse du workflow
        workflow = data.workflow_status
        completed_steps = sum(1 for step in workflow.values() 
                            if isinstance(step, dict) and step.get('completed', False))
        total_steps = len(workflow)
        
        if completed_steps < total_steps:
            recommendations.append(f"Compléter les {total_steps - completed_steps} étapes restantes du workflow")
        
        # Analyse des métriques
        global_score = data.qc_metrics.get('global_score', 0)
        if global_score < 70:
            recommendations.append("Améliorer la qualité des données - score global inférieur à 70%")
        
        gnss_score = data.qc_metrics.get('gnss_score', 0)
        if gnss_score < 80:
            recommendations.append("Vérifier la configuration GNSS - score GNSS faible")
        
        # Analyse des capteurs
        if len(data.sensor_data) < 3:
            recommendations.append("Considérer l'ajout de capteurs supplémentaires pour une meilleure redondance")
        
        if not recommendations:
            recommendations.append("Configuration optimale - aucune recommandation particulière")
        
        return recommendations
    
    def _create_workflow_chart(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Crée un graphique de progression du workflow"""
        try:
            import tempfile
            
            fig, ax = plt.subplots(figsize=(8, 4))
            
            steps = []
            progress = []
            
            step_names = {
                'dimcon': 'Dimcon',
                'gnss': 'GNSS', 
                'observation': 'Observation',
                'qc': 'QC'
            }
            
            for step_key, step_data in workflow.items():
                if isinstance(step_data, dict):
                    steps.append(step_names.get(step_key, step_key.title()))
                    progress.append(step_data.get('progress', 0))
            
            bars = ax.bar(steps, progress, color=['#2ecc71' if p == 100 else '#f39c12' if p > 0 else '#e74c3c' for p in progress])
            
            ax.set_ylabel('Progression (%)')
            ax.set_title('Progression du Workflow de Calibration')
            ax.set_ylim(0, 100)
            
            # Ajouter les valeurs sur les barres
            for bar, prog in zip(bars, progress):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{prog}%', ha='center', va='bottom')
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Sauvegarder dans un fichier temporaire
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close()
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"[ERROR] Erreur création graphique: {e}")
            return None

# Fonctions d'export rapide

def generate_quick_report(project_manager, output_path: str, report_type: str = "complete") -> bool:
    """
    Génère rapidement un rapport depuis le ProjectManager
    
    Args:
        project_manager: Instance du ProjectManager
        output_path: Chemin de sortie
        report_type: Type de rapport (complete, progress, qc)
        
    Returns:
        bool: Succès de la génération
    """
    try:
        current_project = project_manager.get_current_project()
        if not current_project:
            logger.error("[ERROR] Aucun projet chargé")
            return False
        
        # Préparer les données
        report_data = ReportData(
            project_metadata=current_project.get('metadata', {}),
            workflow_status=current_project.get('workflow_status', {}),
            qc_metrics=current_project.get('qc_metrics', {}),
            sensor_data=current_project.get('observation_sensors', []),
            calculation_results=current_project.get('calculations', {})
        )
        
        # Configuration selon le type
        config = ReportConfig(template_type=report_type)
        
        # Générer le rapport
        generator = ReportGenerator(config)
        return generator.generate_complete_report(report_data, output_path)
        
    except Exception as e:
        logger.error(f"[ERROR] Erreur génération rapport rapide: {e}")
        return False
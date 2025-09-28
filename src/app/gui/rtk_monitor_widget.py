"""
Widget de monitoring RTK avec barre de progression et diagramme
Basé sur test_RTKbat.py
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, 
    QLabel, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont


class DonutChartWidget(QWidget):
    """Widget graphique en donut pour afficher les statistiques de qualité"""
    
    def __init__(self):
        super().__init__()
        self.quality_data = {}
        self.colors = {
            '1': QColor("#A3BE8C"),  # Vert - Fix
            '2': QColor("#EBCB8B"),  # Jaune - Float
            '5': QColor("#D08770"),  # Orange - Single
            '4': QColor("#B48EAD"),  # Violet - DGPS
            '3': QColor("#8FBCBB"),  # Cyan - PSR
            '6': QColor("#88C0D0"),  # Bleu clair - DR
            '0': QColor("#BF616A"),  # Rouge - None
        }
        self.setMinimumSize(120, 120)
        self.setMaximumSize(120, 120)
    
    def update_data(self, quality_data):
        """Met à jour les données de qualité"""
        self.quality_data = quality_data.copy()
        self.update()
    
    def paintEvent(self, event):
        """Dessine le graphique en donut"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        side = min(rect.width(), rect.height())
        chart_rect = QRectF(
            (rect.width() - side) / 2 + 10, 
            (rect.height() - side) / 2 + 10, 
            side - 20, 
            side - 20
        )
        
        total = sum(self.quality_data.values())
        
        if total == 0:
            # Aucune donnée - cercle vide
            painter.setPen(QPen(QColor("#4C566A"), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(chart_rect)
            return
        
        # Dessin des segments
        cumulative_angle = 90.0 * 16.0  # Commence en haut
        for quality, count in sorted(self.quality_data.items()):
            if count > 0:
                angle = (count / total) * 360.0 * 16.0
                color = self.colors.get(quality, QColor("gray"))
                
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawPie(chart_rect, round(cumulative_angle), round(angle))
                cumulative_angle += angle
        
        # Trou central
        hole_radius = chart_rect.width() * 0.4
        hole_rect = QRectF(
            chart_rect.center().x() - hole_radius,
            chart_rect.center().y() - hole_radius,
            hole_radius * 2,
            hole_radius * 2
        )
        
        painter.setBrush(QColor("#2E3440"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(hole_rect)
        
        # Texte central
        painter.setPen(QColor("#ECEFF4"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(hole_rect, Qt.AlignCenter, f"{total}")


class RTKMonitorWidget(QWidget):
    """Widget principal de monitoring RTK"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Groupe principal
        group = QGroupBox("Monitoring RTK")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4C566A;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        group_layout = QVBoxLayout(group)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4C566A;
                border-radius: 8px;
                text-align: center;
                padding: 2px;
                background-color: #3B4252;
                height: 30px;
                font-size: 10pt;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1: 0, y1: 0.5, x2: 1, y2: 0.5,
                    stop: 0 #81A1C1, stop: 1 #88C0D0
                );
                border-radius: 6px;
            }
        """)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("En attente...")
        self.progress_bar.setValue(0)
        
        # Layout horizontal pour progression + diagramme
        monitor_layout = QHBoxLayout()
        monitor_layout.setSpacing(15)
        
        # Barre de progression (prend plus d'espace)
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(QLabel("Progression:"))
        progress_layout.addWidget(self.progress_bar)
        
        # Diagramme de qualité
        quality_layout = QVBoxLayout()
        quality_layout.addWidget(QLabel("Qualité:"))
        
        self.donut_chart = DonutChartWidget()
        quality_layout.addWidget(self.donut_chart)
        
        # Légende des couleurs
        legend_layout = QGridLayout()
        legend_layout.setSpacing(5)
        
        legend_items = [
            ("1", "Fix", "#A3BE8C"),
            ("2", "Float", "#EBCB8B"),
            ("5", "Single", "#D08770"),
            ("4", "DGPS", "#B48EAD"),
            ("3", "PSR", "#8FBCBB"),
            ("6", "DR", "#88C0D0"),
            ("0", "None", "#BF616A")
        ]
        
        for i, (code, label, color) in enumerate(legend_items):
            color_label = QLabel()
            color_label.setStyleSheet(f"background-color: {color}; border: 1px solid #4C566A;")
            color_label.setFixedSize(12, 12)
            
            text_label = QLabel(label)
            text_label.setStyleSheet("font-size: 8pt;")
            
            legend_layout.addWidget(color_label, i // 2, (i % 2) * 2)
            legend_layout.addWidget(text_label, i // 2, (i % 2) * 2 + 1)
        
        quality_layout.addLayout(legend_layout)
        
        # Assemblage
        monitor_layout.addLayout(progress_layout, 2)  # Plus d'espace pour la progression
        monitor_layout.addLayout(quality_layout, 1)   # Moins d'espace pour la qualité
        
        group_layout.addLayout(monitor_layout)
        layout.addWidget(group)
    
    def update_progress(self, message: str, percentage: int):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(message)
    
    def update_quality(self, quality_data: dict):
        """Met à jour le diagramme de qualité"""
        self.donut_chart.update_data(quality_data)
    
    def reset(self):
        """Remet à zéro l'affichage"""
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("En attente...")
        self.donut_chart.update_data({})
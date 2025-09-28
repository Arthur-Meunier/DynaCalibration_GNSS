import sys
import subprocess
import re
import os
import math
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QProgressBar, QLabel,
    QPushButton, QTextEdit, QHBoxLayout, QGridLayout, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

# --- Style de l'application (Thème sombre "Nord") ---
APP_STYLESHEET = """
QWidget {
    background-color: #2E3440;
    color: #ECEFF4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}
QProgressBar {
    border: 1px solid #4C566A;
    border-radius: 8px;
    text-align: center;
    padding: 1px;
    background-color: #3B4252;
    height: 40px; /* Hauteur augmentée pour la lisibilité */
    font-size: 11pt;
}
QProgressBar::chunk {
    background-color: qlineargradient(
        x1: 0, y1: 0.5, x2: 1, y2: 0.5,
        stop: 0 #81A1C1, stop: 1 #88C0D0
    );
    border-radius: 7px;
}
"""

class RTKConfig:
    """
    Classe pour centraliser tous les chemins et paramètres modifiables.
    """
    def __init__(self):
        # --- Chemins à configurer ---
        self.working_dir = r"C:\1-Data\01-Projet\ProjetPY\DynaCalibration_GNSS\RTKlib"
        self.exe_path = os.path.join(self.working_dir, "rnx2rtkp.exe")
        self.conf_file = os.path.join(self.working_dir, r"configs\conf.conf")
        gnss_data_dir = r"C:\1-Data\01-Projet\ProjetPY\Thialf\DC-250802\GNSS"
        self.rover_obs_file = os.path.join(gnss_data_dir, "merde.25o")
        self.base_obs_file = os.path.join(gnss_data_dir, "Prt_214A.25O")
        self.rover_nav_file = os.path.join(gnss_data_dir, "merde.25n")
        self.galileo_nav_file = os.path.join(gnss_data_dir, "merde.25g")
        self.precise_eph_file = os.path.join(gnss_data_dir, "COD0OPSULT_20252131800_02D_05M_ORB.SP3")
        self.precise_clk_file = os.path.join(gnss_data_dir, "ESA0OPSFIN_20252100000_01D_30S_CLK.CLK")
        output_dir = os.path.join(gnss_data_dir, "export")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = os.path.join(output_dir, f"rtk_output_{timestamp}.pos")


class RTKProcessor(QThread):
    """
    Thread pour exécuter le processus RTKLIB et surveiller sa progression.
    """
    progress_updated = pyqtSignal(str, int)
    quality_updated = pyqtSignal(dict)
    process_finished = pyqtSignal(int)

    def __init__(self, config: RTKConfig):
        super().__init__()
        self.config = config
        self.obs_file = self.config.rover_obs_file
        self.total_epochs = self._estimate_total_epochs()
        self.processed_epochs = 0
        self.quality_counts = {str(k): 0 for k in range(7)}
        self.is_two_pass = True
        self.total_work_units = self.total_epochs * 2 if self.is_two_pass else self.total_epochs

    def _estimate_total_epochs(self):
        try:
            epoch_regex = re.compile(r'(^\s*>\s*\d{4}|^\s*\d{2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+[\d.]+\s+\d)')
            with open(self.obs_file, 'r', errors='ignore') as f:
                line_count = sum(1 for line in f if epoch_regex.match(line))
                print(f"Nombre d'époques estimé dans le fichier (RINEX v2/v3): {line_count}")
                return max(line_count, 1)
        except Exception as e:
            print(f"Erreur dans _estimate_total_epochs: {e}")
            return 3600

    def run(self):
        command = [
            self.config.exe_path, "-k", self.config.conf_file, "-o", self.config.output_file,
            self.config.rover_obs_file, self.config.base_obs_file, self.config.rover_nav_file,
            self.config.precise_eph_file, self.config.precise_clk_file, self.config.galileo_nav_file,
        ]
        self.progress_updated.emit("Démarrage...", 0)
        print(f"Commande: {' '.join(command)}")

        try:
            if os.path.exists(self.config.output_file):
                os.remove(self.config.output_file)

            process = subprocess.Popen(
                command, cwd=self.config.working_dir, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                bufsize=1, universal_newlines=True # Force line-buffering
            )

            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue

                #print(f"[RTKLIB]: {line}")

                if "processing" in line.lower():
                    self.processed_epochs += 1
                    message = "Traitement..."  # Message par défaut

                    quality_match = re.search(r'Q=(\d+)', line)
                    datetime_match = re.search(r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})', line)

                    if quality_match:
                        quality = quality_match.group(1)
                        if quality in self.quality_counts:
                            self.quality_counts[quality] += 1
                            self.quality_updated.emit(self.quality_counts.copy())
                        
                        if datetime_match:
                            datetime_str = datetime_match.group(1)
                            message = f"{datetime_str} Q={quality}"

                    progress = min(int((self.processed_epochs / self.total_work_units) * 100), 100) if self.total_work_units > 0 else 0
                    self.progress_updated.emit(message, progress)

            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                self.progress_updated.emit("Traitement terminé.", 100)

            print(f"=== FIN DU TRAITEMENT - Code retour: {return_code} ===")
            self.process_finished.emit(return_code)

        except FileNotFoundError:
            print(f"ERREUR: Exécutable '{self.config.exe_path}' introuvable.")
            self.process_finished.emit(-1)
        except Exception as e:
            print(f"ERREUR CRITIQUE: {e}")
            self.process_finished.emit(-1)


class DonutChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.quality_data = {}
        self.colors = {
            '1': QColor("#A3BE8C"), '2': QColor("#EBCB8B"), '5': QColor("#D08770"),
            '4': QColor("#B48EAD"), '3': QColor("#8FBCBB"), '6': QColor("#88C0D0"),
            '0': QColor("#BF616A"),
        }
        self.setMinimumSize(80, 80) # Taille réduite

    def update_data(self, quality_data):
        self.quality_data = quality_data.copy()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect, side = self.rect(), min(self.rect().width(), self.rect().height())
        chart_rect = QRectF((rect.width()-side)/2+5, (rect.height()-side)/2+5, side-10, side-10)
        total = sum(self.quality_data.values())

        if total == 0:
            painter.setPen(QPen(QColor("#4C566A"), 2))
            painter.drawEllipse(chart_rect)
            return

        cumulative_angle = 90.0 * 16.0
        for quality, count in sorted(self.quality_data.items()):
            if count > 0:
                angle = (count / total) * 360.0 * 16.0
                painter.setBrush(self.colors.get(quality, QColor("gray"))); painter.setPen(Qt.NoPen)
                painter.drawPie(chart_rect, round(cumulative_angle), round(angle))
                cumulative_angle += angle
        
        hole_radius = chart_rect.width() * 0.4
        hole_rect = QRectF(chart_rect.center().x()-hole_radius, chart_rect.center().y()-hole_radius, hole_radius*2, hole_radius*2)
        painter.setBrush(QColor("#2E3440")); painter.drawEllipse(hole_rect)
        painter.setPen(QColor("#ECEFF4")); painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(hole_rect, Qt.AlignCenter, f"{total}")


class RTKMonitorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.initUI()
        self.start_processing() # Démarrage automatique

    def initUI(self):
        self.setWindowTitle('Moniteur RTK'); self.setGeometry(100, 100, 700, 100)
        self.setStyleSheet(APP_STYLESHEET)
        
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Initialisation...")

        self.donut_chart = DonutChartWidget()
        self.donut_chart.setFixedSize(80, 80)

        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.donut_chart)

    def start_processing(self):
        try:
            config = RTKConfig()
            for f_path in [config.exe_path, config.conf_file, config.rover_obs_file, config.base_obs_file]:
                if not os.path.exists(f_path):
                    self.progress_bar.setFormat(f"Erreur : Fichier introuvable : {os.path.basename(f_path)}")
                    return
        except Exception as e:
            self.progress_bar.setFormat(f"Erreur de configuration : {e}"); return
            
        self.progress_bar.setValue(0)
        self.donut_chart.update_data({})

        self.worker = RTKProcessor(config)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.quality_updated.connect(self.donut_chart.update_data)
        self.worker.process_finished.connect(self.on_process_finished)
        self.worker.start()

    def update_progress(self, message, percentage):
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(message)

    def on_process_finished(self, return_code):
        if return_code != 0:
            self.progress_bar.setFormat(f"Erreur (code: {return_code})")
        # Le message "Terminé" est déjà géré par la boucle de progression.
        # Pas besoin de le forcer ici.

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.quit(); self.worker.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RTKMonitorApp()
    window.show()
    sys.exit(app.exec_())


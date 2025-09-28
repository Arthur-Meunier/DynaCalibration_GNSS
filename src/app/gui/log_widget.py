# src/app/gui/log_widget.py - VERSION SIMPLE COMPATIBLE

import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
)
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QFont

class StreamRedirector(QObject):
    """
    Redirecteur de flux simple et compatible
    """
    messageWritten = pyqtSignal(str)
    
    def __init__(self, stream_type='stdout'):
        super().__init__()
        self.stream_type = stream_type
        
    def write(self, text):
        if text.strip():  # Ignorer les chaînes vides
            self.messageWritten.emit(str(text))
    
    def flush(self):
        pass

class LogWidget(QWidget):
    """
    Widget de log simple et compatible avec l'existant
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogWidget")
        self.setup_ui()

    def setup_ui(self):
        """Configuration de l'interface utilisateur simple"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Layout pour le titre et le bouton "Effacer"
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Console de Log")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        clear_button = QPushButton("Effacer")
        clear_button.clicked.connect(self.clear_log)
        clear_button.setFixedWidth(80)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_button)
        
        layout.addLayout(header_layout)

        # Zone de texte pour afficher les logs
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 9))
        
        # Style compatible
        self.apply_simple_styles()
        
        layout.addWidget(self.log_output)

    def apply_simple_styles(self):
        """Applique des styles simples et compatibles"""
        self.setStyleSheet("""
            LogWidget {
                background-color: #2d2d30;
                color: white;
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)

    def add_log_message(self, message):
        """
        Ajoute un message à la zone de texte avec horodatage
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message.strip()}\n"
        
        self.log_output.append(formatted_message.rstrip())
        
        # Auto-scroll vers le bas
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Limiter le nombre de lignes pour éviter la surcharge mémoire
        self.limit_log_lines()

    def limit_log_lines(self):
        """Limite le nombre de lignes dans le log"""
        document = self.log_output.document()
        max_lines = 1000
        
        if document.blockCount() > max_lines:
            # Supprimer les anciennes lignes
            cursor = self.log_output.textCursor()
            cursor.movePosition(cursor.Start)
            for _ in range(document.blockCount() - max_lines):
                cursor.select(cursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # Supprimer le saut de ligne

    def clear_log(self):
        """Efface le contenu du log"""
        self.log_output.clear()
        self.add_log_message("Console effacée")

    @staticmethod
    def redirect_console(log_widget):
        """
        Redirige la console vers le widget de log de manière simple
        """
        try:
            stdout_redirector = StreamRedirector('stdout')
            stderr_redirector = StreamRedirector('stderr')
            
            # Connexion des signaux
            stdout_redirector.messageWritten.connect(log_widget.add_log_message)
            stderr_redirector.messageWritten.connect(log_widget.add_log_message)
            
            # Redirection effective
            sys.stdout = stdout_redirector
            sys.stderr = stderr_redirector
            
            return stdout_redirector, stderr_redirector
            
        except Exception as e:
            print(f"Erreur redirection console: {e}")
            return None, None

    def restore_console(self):
        """Restaure la console standard"""
        try:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        except:
            pass

def create_safe_log_widget(parent=None):
    """
    Crée un widget de log de manière sécurisée
    """
    try:
        return LogWidget(parent)
    except Exception as e:
        print(f"Erreur création LogWidget: {e}")
        # Fallback très basique
        from PyQt5.QtWidgets import QTextEdit
        fallback = QTextEdit()
        fallback.setReadOnly(True)
        fallback.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #555;
                font-family: 'Consolas', monospace;
            }
        """)
        fallback.setText("LogWidget en mode secours\n")
        return fallback
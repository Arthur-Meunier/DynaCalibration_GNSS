# -*- coding: utf-8 -*-
"""
Created on Mon Aug  4 02:52:07 2025

@author: a.meunier
"""

# test_webview_minimal.py - Test WebView ultra-simple

import sys
from pathlib import Path

# Ajouter src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src" if (current_dir / "src").exists() else current_dir
sys.path.insert(0, str(src_dir))

def test_webview_basic():
    """Test WebView avec HTML minimal"""
    print("🧪 TEST WEBVIEW BASIQUE")
    print("=" * 30)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5.QtCore import QUrl
        
        app = QApplication.instance() or QApplication([])
        
        # HTML ultra-simple
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { 
                    background: #1e1e1e; 
                    color: white; 
                    font-family: Arial; 
                    text-align: center;
                    padding: 50px;
                }
                .circle {
                    width: 200px;
                    height: 200px;
                    border: 5px solid #00d4aa;
                    border-radius: 50%;
                    margin: 20px auto;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <h1>TEST WEBVIEW</h1>
            <div class="circle">50%</div>
            <p>Si vous voyez ce cercle, QtWebEngine fonctionne!</p>
        </body>
        </html>
        """
        
        webview = QWebEngineView()
        webview.setHtml(html, QUrl("qrc:/"))
        webview.show()
        webview.resize(400, 400)
        webview.setWindowTitle("Test WebView Minimal")
        
        print("✅ WebView créée avec HTML simple")
        print("📋 Vous devriez voir un cercle vert avec '50%' dedans")
        
        return webview, app
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    webview, app = test_webview_basic()
    if webview:
        input("Appuyez sur Entrée pour fermer...")
        webview.close()
    else:
        print("❌ Test échoué")
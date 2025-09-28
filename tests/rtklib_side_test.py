import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_rtklib_with_forced_base(conf_path: Path, work_dir: Path, exe_path: Path) -> int:
    print("🔍 DÉBUT run_rtklib_with_forced_base")
    print(f"   work_dir: {work_dir}")
    print(f"   conf_path: {conf_path}")
    print(f"   exe_path: {exe_path}")
    
    print("📂 Lecture des fichiers dans work_dir...")
    files = list(work_dir.glob('*'))
    print(f"   {len(files)} fichiers trouvés")

    # Base FORCÉE: Prt_214A.25O (insensible à la casse)
    print("🔍 Recherche du fichier base Prt_214A.25O...")
    base_obs = next((p for p in files if p.name.lower() == 'prt_214a.25o'), None)
    if base_obs is None:
        # tolérer .25o/.obs
        print("   Tentative avec extensions alternatives...")
        base_obs = next((p for p in files if p.name.lower().startswith('prt_214a') and p.suffix.lower() in {'.25o', '.o', '.obs'}), None)
    
    if base_obs:
        print(f"   ✅ Base trouvée: {base_obs}")
    else:
        print("   ❌ Base Prt_214A.25O introuvable")

    # Rovers: merde.25o (Bow/Stern) et Stbd*.25o
    print("🔍 Recherche des fichiers rover...")
    rover_bowstern = next((p for p in files if p.name.lower() == 'merde.25o'), None)
    rover_stbd = next((p for p in files if p.name.lower().startswith('stbd') and p.suffix.lower() in {'.25o', '.o', '.obs'}), None)
    
    if rover_bowstern:
        print(f"   ✅ Rover Bow/Stern trouvé: {rover_bowstern}")
    else:
        print("   ❌ Rover Bow/Stern (merde.25o) introuvable")
        
    if rover_stbd:
        print(f"   ✅ Rover Stbd trouvé: {rover_stbd}")
    else:
        print("   ❌ Rover Stbd introuvable")

    def nav_for(obs: Path):
        if not obs:
            return None
        for ext in ('.n', '.nav', '.25n', '.24n', '.23n'):
            c = obs.with_suffix(ext)
            if c.exists():
                return c
        return None

    def gnav_for(base: Path, rover: Path):
        # 1) préférer GNAV qui partage le même préfixe que la base
        def find_by_stem(stem: str):
            for ext in ('.g', '.gnav', '.25g', '.24g', '.23g'):
                cand = (work_dir / f"{stem}{ext}")
                if cand.exists():
                    return cand
            return None
        if base:
            g = find_by_stem(base.stem)
            if g:
                return g
        if rover:
            g = find_by_stem(rover.stem)
            if g:
                return g
        # 2) fallback: premier GNAV du dossier
        for p in work_dir.glob('*'):
            if p.suffix.lower() in {'.g', '.gnav', '.25g', '.24g', '.23g'}:
                return p
        return None

    print("🔍 Recherche des fichiers de navigation...")
    base_nav = nav_for(base_obs)
    if base_nav:
        print(f"   ✅ Base NAV trouvé: {base_nav}")
    else:
        print("   ❌ Base NAV introuvable")
    
    # Préférence SP3 : ULT 02D > RAP 01D > premier .sp3
    print("🔍 Recherche des fichiers SP3...")
    sp3_candidates = [p for p in files if p.suffix.lower() == '.sp3']
    print(f"   {len(sp3_candidates)} fichiers SP3 trouvés")
    sp3 = None
    for p in sp3_candidates:
        n = p.name.upper()
        if 'OPSULT' in n and '_02D_' in n:
            sp3 = p; break
    if sp3 is None:
        for p in sp3_candidates:
            n = p.name.upper()
            if 'OPSRAP' in n and '_01D_' in n:
                sp3 = p; break
    if sp3 is None and sp3_candidates:
        sp3 = sp3_candidates[0]
    
    if sp3:
        print(f"   ✅ SP3 sélectionné: {sp3}")
    else:
        print("   ❌ Aucun fichier SP3 trouvé")
    
    print("🔍 Recherche des fichiers CLK...")
    clk = next((p for p in files if p.suffix.lower() == '.clk'), None)
    if clk:
        print(f"   ✅ CLK trouvé: {clk}")
    else:
        print("   ❌ Aucun fichier CLK trouvé")
    
    # GNAV (GLONASS nav) – essayer d'assortir la base, sinon rover, sinon n'importe
    print("🔍 Recherche des fichiers GNAV...")
    gnav = gnav_for(base_obs, rover_bowstern or rover_stbd)
    if gnav:
        print(f"   ✅ GNAV trouvé: {gnav}")
    else:
        print("   ❌ Aucun fichier GNAV trouvé")

    print("🔍 Vérification des prérequis...")
    if not exe_path.exists():
        print(f"❌ rnx2rtkp.exe introuvable: {exe_path}")
        return 1
    else:
        print(f"   ✅ rnx2rtkp.exe trouvé: {exe_path}")
        
    if not conf_path.exists():
        print(f"❌ Fichier conf introuvable: {conf_path}")
        return 1
    else:
        print(f"   ✅ Fichier conf trouvé: {conf_path}")
        
    if not base_obs or not base_obs.exists():
        print("❌ Base forcée Prt_214A.25O introuvable")
        return 1
    else:
        print(f"   ✅ Base forcée trouvée: {base_obs}")

    # Diagnostic initial
    print("🚀 DÉMARRAGE DIAGNOSTIC RTKLIB")
    print("==============================")
    print("📋 Appel de compare_with_manual_execution...")
    compare_with_manual_execution(conf_path, work_dir, exe_path)
    print("✅ compare_with_manual_execution terminé")

    print("📁 Création des répertoires d'export...")
    export_dir = work_dir / 'export'
    export_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = export_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"   ✅ export_dir: {export_dir}")
    print(f"   ✅ logs_dir: {logs_dir}")

    # Log de configuration globale
    config_log = f"""CONFIGURATION GLOBALE
====================
exe_path: {exe_path}
conf_path: {conf_path}
work_dir: {work_dir}
base_obs: {base_obs}
rover_bowstern: {rover_bowstern}
rover_stbd: {rover_stbd}
sp3: {sp3}
clk: {clk}
base_nav: {base_nav}
gnav: {gnav}

Fichiers détectés dans work_dir:
{chr(10).join([f"  {f.name} ({f.stat().st_size} octets)" for f in files if f.is_file()])}
"""
    print("💾 Sauvegarde de la configuration globale...")
    (logs_dir / "config_globale.txt").write_text(config_log, encoding='utf-8')
    print("   ✅ Configuration sauvegardée")

    def run_one(rover_obs: Path, suffix: str) -> int:
        print(f"🔧 DÉBUT run_one pour {suffix}")
        print(f"   rover_obs: {rover_obs}")
        if not rover_obs or not rover_obs.exists():
            print(f"⚠️ Rover {suffix} introuvable - ignoré")
            return 0
        print(f"   ✅ Rover {suffix} trouvé et valide")
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_pos = export_dir / f"rtk_{suffix}_{ts}.pos"
        # Commande avec chemins absolus
        cmd = [
            str(exe_path.resolve()),
            '-k', str(conf_path.resolve()),
            # Options CLI qui alignent le format de sortie sur l'interface
            # -a: baseline ENU, -u: temps UTC, -t: format yyyy/mm/dd hh:mm:ss
            '-a', '-u', '-t',
            '-o', str(out_pos.resolve()),
            str(rover_obs.resolve()),
            str(base_obs.resolve())
        ]
        if sp3:
            cmd.append(str(sp3.resolve()))
        if clk:
            cmd.append(str(clk.resolve()))
        if base_nav:
            cmd.append(str(base_nav.resolve()))
        if gnav:
            cmd.append(str(gnav.resolve()))

        # Sauvegarde de la commande
        cmd_file = logs_dir / f"{suffix}_command.txt"
        cmd_file.write_text(' '.join(cmd) + '\n', encoding='utf-8')

        # Diagnostic environnement
        print("🔍 DIAGNOSTIC ENVIRONNEMENT:")
        print(f"   Répertoire de travail: {exe_path.parent}")
        print(f"   Répertoire des données: {work_dir}")
        print(f"   Commande sauvée dans: {cmd_file}")

        print("🛠️ RTKLIB:")
        print("   exe  :", exe_path.resolve())
        print("   conf :", conf_path.resolve())
        print("   rover:", rover_obs.resolve())
        print("   base :", base_obs.resolve())
        if sp3: print("   sp3  :", sp3.resolve())
        if clk: print("   clk  :", clk.resolve())
        if base_nav: print("   nav  :", base_nav.resolve())
        if gnav: print("   gnav :", gnav.resolve())
        print("   out  :", out_pos.resolve())

        # Timing et exécution
        print(f"⏰ Démarrage de l'exécution RTKLIB pour {suffix}...")
        start_time = datetime.now()
        print(f"   Commande: {' '.join(cmd)}")
        print(f"   Répertoire de travail: {exe_path.parent}")
        proc = subprocess.run(cmd, cwd=str(exe_path.parent), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        end_time = datetime.now()
        print(f"   ⏱️ Exécution terminée en {end_time - start_time}")
        print(f"   Code de retour: {proc.returncode}")

        # Log complet
        try:
            rtklib_dir_list = []
            for f in exe_path.parent.iterdir():
                try:
                    if f.is_file():
                        rtklib_dir_list.append(f"  {f.name} ({f.stat().st_size} octets)")
                    else:
                        rtklib_dir_list.append(f"  {f.name}/")
                except Exception:
                    rtklib_dir_list.append(f"  {f.name}")
        except Exception:
            rtklib_dir_list = ["(lecture impossible)"]

        log_content = f"""DIAGNOSTIC RTKLIB - {suffix.upper()}
=====================================
Timestamp: {start_time}
Durée d'exécution: {end_time - start_time}
Code de retour: {proc.returncode}

COMMANDE EXÉCUTÉE:
{' '.join(cmd)}

RÉPERTOIRE DE TRAVAIL:
{exe_path.parent}

FICHIERS PRÉSENTS DANS LE RÉPERTOIRE RTK:
{chr(10).join(rtklib_dir_list)}

STDOUT:
{proc.stdout or '(vide)'}

STDERR:
{proc.stderr or '(vide)'}

TAILLE FICHIER SORTIE:
{out_pos.stat().st_size if out_pos.exists() else 'Fichier non créé'} octets
"""
        (logs_dir / f"{suffix}_diagnostic_complet.txt").write_text(log_content, encoding='utf-8')

        # Logs séparés
        (logs_dir / f"{suffix}_stdout.txt").write_text(proc.stdout or '', encoding='utf-8', errors='ignore')
        (logs_dir / f"{suffix}_stderr.txt").write_text(proc.stderr or '', encoding='utf-8', errors='ignore')

        if proc.returncode != 0:
            print(f"❌ Échec ({proc.returncode})")
            print(f"🔍 Voir diagnostic complet: {logs_dir / f'{suffix}_diagnostic_complet.txt'}")
            return proc.returncode

        if out_pos.exists() and out_pos.stat().st_size > 0:
            print(f"✅ Généré: {out_pos} ({out_pos.stat().st_size} octets)")
            # Aperçu amélioré
            try:
                with open(out_pos, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    data_lines = [l.rstrip() for l in lines if not l.startswith('%') and l.strip()]
                    header_lines = [l.rstrip() for l in lines if l.startswith('%')]
                print(f"🔎 Statistiques fichier .pos:")
                print(f"   Total lignes: {len(lines)}")
                print(f"   Lignes header: {len(header_lines)}")
                print(f"   Lignes données: {len(data_lines)}")
                if header_lines:
                    print("📋 Headers importants:")
                    for h in header_lines[:5]:
                        print(f"   {h}")
                if data_lines:
                    print("📊 Aperçu données:")
                    for l in data_lines[:3]:
                        print(f"   {l}")
            except Exception as e:
                print(f"⚠️ Erreur lecture aperçu: {e}")
            return 0
        else:
            print("⚠️ Sortie .pos non créée ou vide")
            return 2

    print("🚀 DÉMARRAGE DES CALCULS RTKLIB")
    print("===============================")
    print("📊 Lancement du calcul Bow/Stern...")
    rc1 = run_one(rover_bowstern, 'bowstern')
    print(f"   Code de retour Bow/Stern: {rc1}")
    
    print("📊 Lancement du calcul Stbd...")
    rc2 = run_one(rover_stbd, 'stbd')
    print(f"   Code de retour Stbd: {rc2}")
    
    print(f"\n📋 Tous les logs sauvés dans: {logs_dir}")
    print("🔍 Pour diagnostic, vérifiez:")
    print(f"   - {logs_dir}/config_globale.txt")
    print(f"   - {logs_dir}/*_diagnostic_complet.txt")
    print(f"   - {logs_dir}/*_command.txt")
    
    final_result = 0 if rc1 == 0 and rc2 == 0 else (rc1 or rc2)
    print(f"🏁 FIN run_rtklib_with_forced_base - Code de retour: {final_result}")
    return final_result


def compare_with_manual_execution(conf_path: Path, work_dir: Path, exe_path: Path):
    """
    Comparaison avec exécution manuelle (affiche chemins et contenus utiles)
    """
    print("🔍 COMPARAISON AVEC EXÉCUTION MANUELLE")
    print("=====================================")
    print(f"Pour reproduire manuellement:")
    print(f"1. Ouvrir cmd dans: {exe_path.parent}")
    print(f"2. Exécuter la commande trouvée dans: export/logs/*_command.txt")
    print(f"3. Comparer le résultat avec: export/rtk_*_*.pos")
    print(f"\n📁 Fichiers dans {exe_path.parent}:")
    try:
        for f in sorted(exe_path.parent.iterdir()):
            print(f"   {f.name}")
    except Exception as e:
        print(f"   (lecture impossible: {e})")
    print(f"\n📁 Fichiers dans {work_dir}:")
    try:
        for f in sorted(work_dir.iterdir()):
            if f.is_file():
                print(f"   {f.name} ({f.stat().st_size} octets)")
    except Exception as e:
        print(f"   (lecture impossible: {e})")


def test_manual_command():
    """
    Affiche une commande manuelle reproductible
    """
    conf_path = Path(r"C:\1-Data\01-Projet\ProjetPY\Thialf\DC-250802\GNSS\conf.conf")
    work_dir = Path(r"C:\1-Data\01-Projet\ProjetPY\Thialf\DC-250802\GNSS")
    project_root = Path(__file__).resolve().parents[1]
    exe_path = project_root / 'RTKlib' / 'rnx2rtkp.exe'
    print("🧪 TEST COMMANDE MANUELLE")
    print("========================")
    print(f"Copier-coller cette commande dans cmd depuis {exe_path.parent}:")
    files = list(work_dir.glob('*'))
    base_obs = next((p for p in files if p.name.lower() == 'prt_214a.25o'), None)
    rover_bowstern = next((p for p in files if p.name.lower() == 'merde.25o'), None)
    if base_obs and rover_bowstern:
        cmd = f'rnx2rtkp.exe -k "{conf_path}" -o "test_manual.pos" "{rover_bowstern}" "{base_obs}"'
        print(f"\n{cmd}")
        print(f"\nPuis comparer test_manual.pos avec le fichier généré par le script")


if __name__ == '__main__':
    print("🚀 DÉMARRAGE DU SCRIPT RTKLIB SIDE TEST")
    print("=====================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("📋 Mode test - génération commande manuelle")
        test_manual_command()
        sys.exit(0)
    
    print("🔧 Initialisation des chemins...")
    conf_path = Path(r"C:\1-Data\01-Projet\ProjetPY\Thialf\DC-250802\GNSS\conf.conf")
    work_dir = Path(r"C:\1-Data\01-Projet\ProjetPY\Thialf\DC-250802\GNSS")
    project_root = Path(__file__).resolve().parents[1]
    exe_path = project_root / 'RTKlib' / 'rnx2rtkp.exe'
    
    print(f"📁 conf_path: {conf_path}")
    print(f"📁 work_dir: {work_dir}")
    print(f"📁 exe_path: {exe_path}")
    print(f"📁 project_root: {project_root}")
    
    print("✅ Chemins initialisés, lancement de run_rtklib_with_forced_base...")
    result = run_rtklib_with_forced_base(conf_path, work_dir, exe_path)
    print(f"🏁 Script terminé avec code: {result}")
    sys.exit(result)



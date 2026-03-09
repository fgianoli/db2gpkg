#!/usr/bin/env python3
"""
Compile Qt .ts translation files to .qm binary format.
Run inside the QGIS Python environment (works with both PyQt5/Qt5 and PyQt6/Qt6):

    python compile_translations.py

Or from QGIS Python console:

    exec(open('/path/to/pg2gpkg/i18n/compile_translations.py').read())
"""

import os
import glob
import subprocess

def compile_translations():
    i18n_dir = os.path.dirname(os.path.abspath(__file__))
    ts_files = glob.glob(os.path.join(i18n_dir, "*.ts"))

    if not ts_files:
        print(f"No .ts files found in {i18n_dir}")
        return

    for ts_file in ts_files:
        qm_file = ts_file.replace(".ts", ".qm")
        try:
            result = subprocess.run(
                ["lrelease", ts_file, "-qm", qm_file],
                capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Compiled: {os.path.basename(qm_file)}")
            else:
                print(f"Failed to compile {os.path.basename(ts_file)}")
                if result.stderr:
                    print(result.stderr.strip())
                print("Install Qt Linguist tools and run: lrelease pg2gpkg_it.ts")
        except FileNotFoundError:
            print(f"Cannot compile {os.path.basename(ts_file)}: lrelease not found")
            print("Install Qt Linguist tools and run: lrelease pg2gpkg_it.ts")

if __name__ == "__main__":
    compile_translations()

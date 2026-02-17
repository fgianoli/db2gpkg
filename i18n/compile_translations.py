#!/usr/bin/env python3
"""
Compile Qt .ts translation files to .qm binary format.
Run inside the QGIS Python environment or any environment with PyQt5:

    python compile_translations.py

Or from QGIS Python console:

    exec(open('/path/to/pg2gpkg/i18n/compile_translations.py').read())
"""

import os
import glob

def compile_translations():
    i18n_dir = os.path.dirname(os.path.abspath(__file__))
    ts_files = glob.glob(os.path.join(i18n_dir, "*.ts"))

    if not ts_files:
        print(f"No .ts files found in {i18n_dir}")
        return

    # Try lrelease first (system command)
    for ts_file in ts_files:
        qm_file = ts_file.replace(".ts", ".qm")
        ret = os.system(f'lrelease "{ts_file}" -qm "{qm_file}"')
        if ret == 0:
            print(f"Compiled: {os.path.basename(qm_file)}")
        else:
            # Fallback: use PyQt5
            try:
                from PyQt5.QtCore import QProcess
                p = QProcess()
                p.start("lrelease", [ts_file, "-qm", qm_file])
                p.waitForFinished()
                if p.exitCode() == 0:
                    print(f"Compiled: {os.path.basename(qm_file)}")
                else:
                    print(f"Failed to compile {os.path.basename(ts_file)}")
                    print("Run 'lrelease' manually or install Qt Linguist tools.")
            except Exception as e:
                print(f"Cannot compile {os.path.basename(ts_file)}: {e}")
                print("Install Qt Linguist tools and run: lrelease pg2gpkg_it.ts")

if __name__ == "__main__":
    compile_translations()

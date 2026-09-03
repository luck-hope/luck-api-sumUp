"""
跨平台打包脚本 —— Windows 出 .exe，macOS 出 .app bundle
用法（Win）: python build_exe.py
用法（Mac）: python build_exe.py
"""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

is_mac = sys.platform == "darwin"
is_win = sys.platform == "win32"

name = f"TokenTrackerGateway-{('Mac' if is_mac else 'Win')}"
onefile = not is_mac  # Windows 单文件；macOS 用 --onedir 生成 .app bundle

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onefile" if onefile else "--onedir",
    "--windowed",
    "--name", name,
    "--clean",
    "--hidden-import", "aiohttp",
    "--hidden-import", "PyQt6.QtWidgets",
    "--hidden-import", "PyQt6.QtCore",
    "--hidden-import", "PyQt6.QtGui",
]

if is_win:
    ico = os.path.join(ROOT, "assets", "hermes.ico")
    if os.path.exists(ico):
        cmd += ["--icon", ico]

cmd.append("main.py")

print("CMD:", " ".join(cmd))
subprocess.check_call(cmd)

out = os.path.join(ROOT, "dist", name)
if is_mac:
    bundle = out + ".app"
    print(f"macOS .app bundle -> {bundle}")
    print(f"To create DMG: hdiutil create -volname {name} -srcfolder {bundle} -ov -format UDZO dist/{name}.dmg")
elif is_win:
    print(f"Windows exe -> {out}.exe")
else:
    print(f"WARNING: Linux icon not configured, exe at {out}")

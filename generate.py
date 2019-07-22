import PyInstaller.__main__

files = [
    r"lmt_manipulator\lmt_manipulator.py",
    r"move-subspecies-script\move-subspecies.py",
    r"quest-sobj-script\quest-sobj-script.py" 
]

for f in files:
    PyInstaller.__main__.run([f, "--onefile"])
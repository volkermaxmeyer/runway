from setuptools import setup

APP = ["runway.py"]
OPTIONS = {
    "iconfile": "icon.icns",
    "plist": {
        "CFBundleName": "Runway",
        "CFBundleDisplayName": "Runway",
        "CFBundleIdentifier": "com.volkermaxmeyer.runway",
        "CFBundleShortVersionString": "1.0.0",
        "LSUIElement": True,  # Menubar-App: kein Dock-Icon
    },
    "packages": ["rumps"],
}

setup(
    app=APP,
    name="Runway",
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)

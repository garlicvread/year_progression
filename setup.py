from setuptools import setup

APP = ['flet_dday_app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'app_icon.icns',
    'packages': ['flet'],
    'plist': {
        'CFBundleName': '째깍째깍째깍째깍 feat. 똥방구쟁이',
        'CFBundleDisplayName': '째깍째깍째깍째깍 feat. 똥방구쟁이',
        'CFBundleGetInfoString': "째깍째깍째깍째깍 feat. 똥방구쟁이",
        'CFBundleIdentifier': "com.yourcompany.ticktock",
        'CFBundleVersion': "0.1.0",
        'CFBundleShortVersionString': "0.1.0",
        'NSHumanReadableCopyright': u"Copyright © 2025, AidALL Inc., All Rights Reserved"
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 
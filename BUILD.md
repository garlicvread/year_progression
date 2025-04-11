# 빌드 가이드: 실행 파일 만들기

이 문서는 D-Day & Year Progress 프로그램을 Windows(.exe)와 MacOS(.app)용 실행 파일로 빌드하는 방법을 설명합니다.

## Windows용 실행 파일(.exe) 만들기

### 1. 필요한 패키지 설치

```bash
pip install pyinstaller
```

### 2. 아이콘 파일 준비 (선택사항)
- 원하는 아이콘을 .ico 형식으로 준비하세요.
- ICO 변환 사이트: https://convertio.co/png-ico/

### 3. 실행 파일 생성

```bash
pyinstaller --name="D-Day_Year_Progress" --windowed --onefile flet_dday_app.py
```

아이콘을 사용하려면:

```bash
pyinstaller --name="D-Day_Year_Progress" --windowed --icon=app_icon.ico --onefile flet_dday_app.py
```

### 4. 생성된 실행 파일 확인
- 생성된 실행 파일은 `dist` 폴더에 있습니다.
- 이 파일을 배포하면 사용자는 Python이나 flet을 설치하지 않고도 프로그램을 실행할 수 있습니다.

## MacOS용 앱(.app) 만들기

### 1. 필요한 패키지 설치

```bash
pip install py2app
```

### 2. 아이콘 파일 준비 (선택사항)
- 원하는 아이콘을 .icns 형식으로 준비하세요.
- ICNS 변환 사이트: https://cloudconvert.com/png-to-icns

### 3. setup.py 파일 생성

프로젝트 루트에 `setup.py` 파일을 생성하고 다음 내용을 추가합니다:

```python
from setuptools import setup

APP = ['flet_dday_app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['flet'],
    'iconfile': 'app_icon.icns',  # 아이콘 파일 경로 (선택사항)
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

### 4. 앱 생성

```bash
python setup.py py2app
```

### 5. 생성된 앱 확인
- 생성된 앱은 `dist` 폴더에 있습니다.
- 이 앱을 배포하면 사용자는 Python이나 flet을 설치하지 않고도 프로그램을 실행할 수 있습니다.

## 주의사항

1. 각 OS용 앱은 해당 OS에서 빌드해야 합니다. 윈도우에서 macOS 앱을 만들거나 그 반대는 불가능합니다.

2. PyInstaller/py2app은 모든 필요한 의존성을 자동으로 감지하지 못할 수 있습니다. 오류가 발생하면 `--hidden-import` 옵션으로 필요한 모듈을 추가하세요.

3. 배포 전 여러 시스템에서 테스트하는 것이 좋습니다.

4. 빌드 과정에서 문제가 발생하면 다음 명령어로 의존성을 확인해보세요:

```bash
pip freeze > requirements.txt
```

이 파일을 참고하여 필요한 모든 패키지가 설치되어 있는지 확인하세요. 
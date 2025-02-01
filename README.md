# PlayReadyProxy-API
`PlayReadyProxy-API` is an API service designed to work alongside [PlayReadyProxy](https://github.com/ThatNotEasy/PlayReadyProxy) (Edge Extension), enabling seamless integration for handling `PlayReady DRM` operations.

## Installation
- Perform a `git clone`
```
git clone https://github.com/ThatNotEasy/PlayReadyProxy-API
```

- Create a Virtual Environment & Activate
```
python -m venv venv
```

- Wingay
```
venv\Scripts\activate
```

- Linux
```
source venv/bin/activate
```

- Install depencies
```
pip install -r requirements.txt
```

- Run Flask

```
flask run
```

- Rename the `.env.example` and `config.ini.example` files to `.env` and `config.ini`:
- Update and place your device `prd` file in the `config.ini`

## Credits & References:
- `WidevineProxy2` A project created by [DevLarLey](https://github.com/DevLARLEY)
- `DDownloader` A Python package for downloading and processing streams, integration with [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE) & [FFmpeg](https://www.ffmpeg.org/)


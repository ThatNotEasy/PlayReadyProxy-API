# PlayReady-ProxyAPI
`PlayReady-ProxyAPI` is an API service designed to work alongside [PlayReady-Proxy](https://github.com/ThatNotEasy/PlayReady-Proxy), enabling seamless integration for handling `PlayReady DRM` operations. It is based on `WidevineProxy2` but has been restructured and expanded to support `PlayReady DRM`

## Installation
- Perform a `git clone`

```
git clone https://github.com/ThatNotEasy/PlayReady-ProxyAPI
```

- Create, activate a virtual environment & install depencies

```
$ python -m venv venv

// For Wingay
$ venv\Scripts\activate

// For Linux
$ source venv/bin/activate

$ pip install -r requirements.txt
```

- Run Flask:

```
flask run
```

- Rename the `.env.example` and `config.ini.example` files to `.env` and `config.ini`:
- Update and place your device `prd` file in the `config.ini`

## Credits & References:
- `WidevineProxy2` A project created by [DevLarLey](https://github.com/DevLARLEY)
- `DDownloader` A Python package for downloading and processing streams, integration with [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE) & [FFmpeg](https://www.ffmpeg.org/)


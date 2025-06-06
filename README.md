# MovieClipper

MovieClipper scans a movie library and generates a short HEVC clip for each
movie.  It provides a small web UI and can be run either directly with Python
or inside a Docker container.

## Running locally

```
pip install -r requirements.txt
python run.py
```

The UI will be available on `http://localhost:8000`.

## Docker

```
docker build -t movieclipper .
docker run -p 8000:8000 -v /path/to/config:/config -v /movies:/movies \
    -e MOVIECLIPPER_CONFIG_DIR=/config movieclipper
```

`/config` is where the application stores its configuration file.  Mount your
movie library inside the container so it can read the files.

# MCP server image (used by Glama and other MCP directories to run and inspect the server).
# Builds spotify-soundtrack-mcp from this repository exactly as it is published to PyPI,
# then runs it over stdio.
#
#   docker build -t spotify-soundtrack-mcp .
#   docker run -i --rm -e SPOTIPY_CLIENT_ID=your_client_id spotify-soundtrack-mcp
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /src
COPY . .

RUN pip install build \
    && python packaging/build_packages.py --out /tmp/packages --dist /tmp/dist \
    && pip install /tmp/dist/spotify-soundtrack-mcp/*.whl \
    && pip uninstall -y build \
    && rm -rf /tmp/packages /tmp/dist /src

RUN useradd --create-home --uid 1000 mcp
USER mcp
WORKDIR /home/mcp

# Listing tools needs no Spotify login; a real SPOTIPY_CLIENT_ID (and TMDB key) is only
# needed to call them. Override these with `docker run -e ...`.
ENV SPOTIPY_CLIENT_ID=replace-with-your-spotify-client-id \
    SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback \
    SPOTIFY_TOOLSETS=all \
    OPEN_BROWSER=false

CMD ["spotify-soundtrack-mcp", "--transport", "stdio"]

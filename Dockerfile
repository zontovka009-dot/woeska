# BotHost single-container deployment for Wathis
FROM node:22-alpine AS frontend-build
WORKDIR /src/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/wathis

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor \
    && rm -f /etc/nginx/sites-enabled/default \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

COPY backend/app ./backend/app

COPY bot/requirements.txt ./bot/requirements.txt
RUN pip install --no-cache-dir -r ./bot/requirements.txt

COPY bot ./bot

COPY --from=frontend-build /src/frontend/dist /usr/share/nginx/html

COPY bot-host/nginx.conf /etc/nginx/conf.d/default.conf
COPY bot-host/supervisord.conf /etc/supervisor/conf.d/wathis.conf

EXPOSE 80

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]

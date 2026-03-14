FROM nginx:1.27-alpine

ARG API_UPSTREAM=api:8000

RUN apk add --no-cache gettext

COPY dashboard/ /usr/share/nginx/html/
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

RUN mkdir -p /usr/share/nginx/html/static && \
    cp /usr/share/nginx/html/app.js /usr/share/nginx/html/static/app.js && \
    cp /usr/share/nginx/html/style.css /usr/share/nginx/html/static/style.css && \
    cp /usr/share/nginx/html/styles.css /usr/share/nginx/html/static/styles.css

ENV API_UPSTREAM=${API_UPSTREAM}

EXPOSE 80

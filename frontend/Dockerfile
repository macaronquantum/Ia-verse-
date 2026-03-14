FROM nginx:1.27-alpine

COPY . /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh

RUN mkdir -p /usr/share/nginx/html/static && \
    cp /usr/share/nginx/html/app.js /usr/share/nginx/html/static/app.js && \
    cp /usr/share/nginx/html/style.css /usr/share/nginx/html/static/style.css && \
    cp /usr/share/nginx/html/styles.css /usr/share/nginx/html/static/styles.css && \
    chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]

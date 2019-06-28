FROM node:alpine

RUN adduser -D -g '' appuser

RUN apk upgrade --update-cache --available && \
    apk add chromium && \
    apk add openssl && \
    apk add ca-certificates && \
    rm -rf /var/cache/apk/*

RUN npm i -g @ui5/cli && \
    npm i -g concurrently

COPY app /app/
WORKDIR /app

RUN npm i --no-optional && \ 
    npm run-script build && \
    rm -rf webapp/

RUN chown -R appuser:appuser /app/ && \
    chmod 755 /app/

USER appuser

EXPOSE 8080 8081 8000

CMD [ "concurrently", "--no-color", "--kill-others", "\"node ui5server.js\"", "\"node exposedserver.js\"", "\"node dummyclient.js\"", "\"node tools/waitForServer.js && node orderroutine.js\"" ]
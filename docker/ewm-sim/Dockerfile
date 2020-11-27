FROM node:lts-alpine AS build

#RUN apk upgrade --update-cache --available && \
#    apk add python && \
#    apk add make && \
#    apk add g++ && \
#    rm -rf /var/cache/apk/*

WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install --production

FROM node:lts-alpine

WORKDIR /usr/src/app
COPY . .
COPY --from=build /usr/src/app/node_modules ./node_modules
#RUN du -sh ./node_modules

EXPOSE 8080
CMD [ "npm", "start" ]

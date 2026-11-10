FROM node:22.13

WORKDIR /root
COPY package.json package-lock.json /root/
RUN npm ci
COPY index.js /root/

CMD ["node", "index.js"]

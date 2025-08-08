FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN [ -f package.json ] && npm ci || true
COPY . .
RUN [ -f package.json ] && npm run build || true
EXPOSE 3000
CMD ["npm","start"]

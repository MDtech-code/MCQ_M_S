# frontend/Dockerfile
FROM node:18.20.4-alpine3.20

WORKDIR /app

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Add these environment variables
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true

CMD ["npm", "run", "dev"]
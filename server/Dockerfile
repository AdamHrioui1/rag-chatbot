FROM node:20-slim

WORKDIR /app

# Copy only the dependency manifests first, and install before copying the
# rest of the code. Docker caches each instruction as a "layer" - as long
# as package*.json don't change, Docker reuses the cached install layer
# instead of re-running `npm install` every time you edit a controller or
# route file, which makes rebuilds during development much faster.
COPY package*.json ./
RUN npm install --omit=dev

COPY . .

EXPOSE 5000

# Run Node directly, not through nodemon - nodemon's file-watching/restart
# behavior is a development convenience, not something a production
# container needs (and it's not installed anyway, since it's a
# devDependency and we used --omit=dev above).
CMD ["node", "index.js"]

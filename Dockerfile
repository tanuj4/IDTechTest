# Stage 1: Build the Vue frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python / Flask API
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config.py run.py seed.py entrypoint.sh ./

# Copy built frontend from stage 1 into Flask static folder
COPY --from=frontend-builder /frontend/dist ./app/static/dist/

EXPOSE 5000

CMD ["sh", "entrypoint.sh"]

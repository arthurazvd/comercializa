FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY --chown=appuser:appuser backend/ ./
COPY --from=frontend --chown=appuser:appuser /build/dist /app/frontend_dist
RUN chown appuser:appuser /app && chmod +x /app/docker-entrypoint.sh
USER appuser
EXPOSE 8000
CMD ["/app/docker-entrypoint.sh"]

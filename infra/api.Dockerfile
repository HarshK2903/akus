FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade zlib1g && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY apps/api/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r requirements.lock
COPY apps/api /app/apps/api
RUN pip install --no-cache-dir --no-deps -e /app/apps/api && python -m pip uninstall -y pip
ENV PYTHONDONTWRITEBYTECODE=1
USER 65532:65532
CMD ["uvicorn", "akus.main:create_app", "--factory", "--no-access-log", "--host", "0.0.0.0", "--port", "8000"]

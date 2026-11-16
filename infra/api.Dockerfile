FROM python:3.13-slim
WORKDIR /app
COPY apps/api/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r requirements.lock
COPY apps/api /app/apps/api
RUN pip install --no-cache-dir --no-deps -e /app/apps/api
CMD ["uvicorn", "akus.main:create_app", "--factory", "--no-access-log", "--host", "0.0.0.0", "--port", "8000"]

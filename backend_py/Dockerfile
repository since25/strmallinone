FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

WORKDIR /app/backend_py

COPY backend_py/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
  && mkdir -p /data/strm /data/backend

COPY backend_py/app ./app
COPY backend_py/scripts ./scripts

EXPOSE 3000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]

# AutoFlow backend — Render (Docker) ke liye
# Render Dockerfile use kare ga agar render.yaml me docker env ho,
# warna render.yaml ka native Python plan bhi kaam kare ga.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# Render $PORT env var deta hai; shell form is liye hai ke $PORT expand ho.
CMD sh -c "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"

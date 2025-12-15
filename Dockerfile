# Dockerfile para app_slu (Python)
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt || true
CMD ["python", "-m", "streamlit_app"]

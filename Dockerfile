FROM python:3.15-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY services ./services
COPY eval ./eval
ENV QUERYX_DATA_DIR=/srv/data
EXPOSE 8000
# Monolith by default. docker-compose.yml overrides the command for each microservice.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

RUN pip install flask prometheus_client requests

COPY exporter.py /exporter.py

CMD ["python", "/exporter.py"]

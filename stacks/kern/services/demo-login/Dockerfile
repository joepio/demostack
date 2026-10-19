FROM python:3.13-alpine
RUN pip install --no-cache-dir requests==2.32.5
COPY app.py /app/app.py
USER 1000
EXPOSE 8080
CMD ["python", "/app/app.py"]

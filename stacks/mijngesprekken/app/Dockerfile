FROM python:3.13-slim
RUN pip install --no-cache-dir "pyjwt[crypto]==2.10.1" "requests==2.32.3"
WORKDIR /app
COPY app.py medewerker.html regie.html ./
CMD ["python", "-u", "app.py"]

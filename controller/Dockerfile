FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV FLASK_APP=controller.app:app
EXPOSE 8000
CMD ["python", "-m", "controller.app"]

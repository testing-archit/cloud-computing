FROM python:3.11-slim
WORKDIR /app/agent
COPY requirements.txt /app/
RUN pip install --no-cache-dir flask docker
COPY agent /app/agent
EXPOSE 5000
CMD ["python", "agent.py"]

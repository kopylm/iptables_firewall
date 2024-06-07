FROM python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y iptables

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]

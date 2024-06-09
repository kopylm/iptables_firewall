FROM python:3.11

WORKDIR /app

COPY . /app

RUN apt-get update && \
    apt-get install -y iptables cron && \
    pip install --no-cache-dir -r requirements.txt

RUN echo "0 * * * * python /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/iptables-cron && \
    chmod 0644 /etc/cron.d/iptables-cron && \
    crontab /etc/cron.d/iptables-cron && \
    touch /var/log/cron.log

CMD ["python", "main.py"]
#Command for run in k8s cluster
#CMD ["cron", "-f"]

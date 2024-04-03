FROM python:3.10-alpine
WORKDIR /usr/src/app
COPY requirements.txt .
COPY init_mongo_replica_set.sh /docker-entrypoint-initdb.d/

RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "app.py"]
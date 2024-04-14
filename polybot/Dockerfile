FROM ubuntu:rolling

# Set the working directory
WORKDIR /usr/src/app

# Install Python3 and pip
RUN apt update && \
    apt install -y python3 python3-pip



# Upgrade pip
RUN apt install --upgrade pip

# Copy requirements.txt and install dependencies
COPY requirements.txt .
COPY init_mongo_replica_set.sh /docker-entrypoint-initdb.d/

RUN pip install -r requirements.txt

# Copy the rest of the application files
COPY . .

# Specify the command to run the application
CMD ["python3", "app.py"]

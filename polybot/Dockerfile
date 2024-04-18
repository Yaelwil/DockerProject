From python:alpine3.19

# Set the working directory
WORKDIR /usr/src/app

# Copy requirements.txt and install dependencies
COPY requirements.txt .

RUN pip install -r requirements.txt

# Copy the rest of the application files
COPY . .

# Specify the command to run the application
CMD ["python3", "app.py"]

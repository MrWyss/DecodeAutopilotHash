# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Install uWSGI
RUN apt-get update && apt-get install -y build-essential && \
    pip install uwsgi && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y

# Copy the rest of the application code into the container at /app
COPY . /app

# Expose port 5000 for the Flask app to listen on
EXPOSE 5000

# Use uWSGI as the production server to run the Flask app
CMD ["uwsgi", "--http", ":5000", "--wsgi-file", "app.py", "--callable", "app"]

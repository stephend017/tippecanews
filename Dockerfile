# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.7

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .

# Install production dependencies.
RUN pip install Flask gunicorn google-cloud-firestore atoma python-dotenv bs4 python-twitter

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec export GOOGLE_APPLICATION_CREDENTAILS=auth.json
CMD exec source envfile
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 main:tippecanews

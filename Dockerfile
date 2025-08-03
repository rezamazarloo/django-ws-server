FROM python:3.12.11

# EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install pip requirements
COPY ws-server-backend /app
RUN apt update && apt install gettext -y
RUN python -m pip install -r requirements.txt
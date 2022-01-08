# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster

# Setting working dir
WORKDIR /usr/local/src/buybook

# Install dependt libs
COPY requirements.txt  ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app to workdir
COPY buybook  ./





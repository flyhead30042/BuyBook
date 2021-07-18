# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster
WORKDIR /usr/local/BuyBook
COPY .  ./
RUN pip install -r requirements.txt





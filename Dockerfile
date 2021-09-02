FROM python:3.9-slim

WORKDIR /usr/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

CMD [ "python", "./price_checker.py", "--config", "/config/config.yaml" ]

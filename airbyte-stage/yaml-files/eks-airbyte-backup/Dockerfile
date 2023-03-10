FROM python:3.9
RUN python -m pip install requests
RUN python -m pip install boto3
WORKDIR /app
COPY . /app
CMD ["python", "main.py"]

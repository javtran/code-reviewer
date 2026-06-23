FROM public.ecr.aws/lambda/python:3.11

COPY main.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["main.handler"]

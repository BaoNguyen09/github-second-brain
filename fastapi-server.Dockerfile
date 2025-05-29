FROM python:3.11

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --upgrade -r /code/requirements.txt

COPY ./app /code/app

EXPOSE 8080

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8080"]
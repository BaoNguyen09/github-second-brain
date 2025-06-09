FROM python:3.12-alpine3.17

WORKDIR /code

COPY ./tools /code/tools
COPY ./main.py /code
COPY ./requirements.txt /code

RUN pip install uv

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["uv", "--directory", "/code", "run", "main.py"]
FROM python:3.12-alpine3.17

WORKDIR /code

COPY . /code

RUN pip install uv

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV GHSB_API_ENDPOINT="https://ghsb-fastapi-tiolb.ondigitalocean.app/"

CMD ["uv", "--directory", "/code", "run", "mcp_server.py"]
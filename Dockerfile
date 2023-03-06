FROM python:3.10.10-slim

WORKDIR /tmp

ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get install --no-install-recommends -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false

COPY ./backend/ /tmp/

RUN poetry install

WORKDIR /tmp/sns

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8000", "--reload"]

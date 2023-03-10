FROM python:3.10.10-slim

ENV HOME "/root"
ENV APP_HOME "$HOME/app"

RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install poetry
ENV PATH "$HOME/.local/bin:$PATH"
RUN apt-get update && apt-get install --no-install-recommends -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false

# install python packages
COPY . ./backend
WORKDIR $APP_HOME/backend
RUN poetry install

# run app
WORKDIR $APP_HOME/backend/sns

# run app
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]


FROM ubuntu

ARG DEBIAN_FRONTEND=noninteractive

ENV OPENAI_API_KEY=your_openai_api_key
ENV CLLM_DIR=/main/.cllm

# Install the necessary system packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    pipx \
    jq \
    curl

# Install and setup poetry
ENV PATH="/root/.local/bin:$PATH"
RUN pipx install poetry

WORKDIR /main

# Install dependencies
COPY poetry.lock /main
COPY pyproject.toml /main
RUN poetry config virtualenvs.create false && \
poetry install --no-interaction --no-ansi --no-root

# Install source code
COPY . /main
RUN poetry install --no-interaction --no-ansi

ENTRYPOINT ["poetry", "run", "cllm"]

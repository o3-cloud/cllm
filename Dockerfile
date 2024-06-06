FROM ubuntu

ENV OPENAI_API_KEY=your_openai_api_key
ENV CLLM_PATH=/main/.cllm

# Install the necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip && \
    pip install poetry

COPY . /main
WORKDIR /main
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

ENTRYPOINT ["cllm"]


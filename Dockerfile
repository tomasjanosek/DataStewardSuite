FROM python:3.12-slim

# git: VaultWriter shells out to it via GitPython to init/commit the vault repo.
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x scripts/entrypoint.sh

ENTRYPOINT ["scripts/entrypoint.sh"]
CMD ["pytest"]

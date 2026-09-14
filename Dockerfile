FROM python:3.12-slim

# git: VaultWriter shells out to it via GitPython to init/commit the vault repo.
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# TODO(mvp, milestone 3): entrypoint becomes `streamlit run src/ui/app.py` once the
# Session/UI milestone lands.
CMD ["pytest"]

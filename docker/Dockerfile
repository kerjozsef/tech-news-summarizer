FROM python:3.12-slim

# Install Infisical CLI
RUN apt-get update && apt-get install -y curl gnupg bash \
    && curl -1sLf "https://artifacts-cli.infisical.com/setup.deb.sh" | bash \
    && apt-get update && apt-get install -y infisical \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
RUN touch /var/log/summarizer.log

CMD ["/bin/bash", "-c", "export INFISICAL_TOKEN=$(infisical login --method=universal-auth --client-id=$INFISICAL_UNIVERSAL_AUTH_CLIENT_ID --client-secret=$INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET --silent --plain) && infisical run --domain=$INFISICAL_API_URL --env=$INF_ENV --projectId=$INF_PROJECT_ID -- python3 main.py --schedule --email --ntfy"]

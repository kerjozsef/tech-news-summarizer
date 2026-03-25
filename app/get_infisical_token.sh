#!/bin/bash

if [ -z "${INF_DOMAIN}" ]; then
  echo "Error: INF_DOMAIN is not set. Set INF_DOMAIN in the environment (e.g. docker-compose or Gitea Actions)." >&2
  exit 1
fi
if [ -z "${INF_CLIENT_ID}" ]; then
  echo "Error: INF_CLIENT_ID is not set. Set INF_CLIENT_ID in the environment (e.g. docker-compose or Gitea Actions)." >&2
  exit 1
fi
if [ -z "${INF_CLIENT_SECRET}" ]; then
  echo "Error: INF_CLIENT_SECRET is not set. Set CLIENT_SECRET in the environment (e.g. docker-compose or Gitea Actions)." >&2
  exit 1
fi
if [ -z "${INF_PROJECT_ID}" ]; then
  echo "Error: INF_PROJECT_ID is not set. Set INF_PROJECT_ID in the environment (e.g. docker-compose or Gitea Actions)" >&2
  exit 1
fi
echo "Domain: ${INF_DOMAIN}"
echo "Client ID: ${INF_CLIENT_ID}"
echo "Client secret: ${INF_CLIENT_SECRET}"
echo "Project ID: ${INF_PROJECT_ID}"
export INFISICAL_TOKEN=$(infisical login --domain=${INF_DOMAIN} --method=universal-auth --client-id=${INF_CLIENT_ID} --client-secret=${INF_CLIENT_SECRET} --silent --plain)
echo "Infisical token: ${INFISICAL_TOKEN}"

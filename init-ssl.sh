#!/bin/bash
# Initialize Let's Encrypt SSL certificate for task-flow.work.gd
# Run once on the server BEFORE starting docker-compose

set -e

DOMAIN="task-flow.work.gd"

mkdir -p data/certbot/conf data/certbot/www

# Obtain certificate using standalone mode (port 80 must be free)
docker run -it --rm \
  -p 80:80 \
  -v "$(pwd)/data/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/data/certbot/www:/var/www/certbot" \
  certbot/certbot:latest \
  certonly --standalone \
    --register-unsafely-without-email \
    -d "$DOMAIN" \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal

echo "SSL certificate obtained for $DOMAIN"
echo "Now run: docker compose -f docker-compose.prod.yml up -d"

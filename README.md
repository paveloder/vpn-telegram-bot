# Телеграм бот для выдачи ключей VPN.

## Запуск

```bash
docker compose -f docker-compose.yml
      -f docker/docker-compose.prod.yml
      config > docker-compose.deploy.yml
docker compose -f docker-compose.deploy.yml up -d --build
```
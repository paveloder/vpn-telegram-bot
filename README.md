# Телеграм бот для выдачи ключей VPN


## Деплой на сервере

### Первичные настройки

Для начала нужно создать бота и определить токен. Об этом полно ссылок в интернете, не будем об этом писать. 

Далее необходимо склонировать репозиторий:
```bash
git clone https://github.com/paveloder/vpn-telegram-bot.git
cd vpn-telegram-bot
```

Далее скопируем локальный файл с секретами:
```bash
cp ./config/.env.template ./config/.env
```

Нужно определить реальными значениями все секреты в файле `.env`. 

Что там есть:
- TELEGRAM_BOT_TOKEN — токен бота
- VPN_TELEGRAM_BOT_CHANNEL_ID — специальная группа, куда нужно добавить бота (как админа), и куда будем добавлять пользователей, подтверждая что им можно выдать ключи
- BILLING_ACCOUNT_URL="https://www.tinkoff.ru/cf/xxxxxxxxx" — твой счет куда можно отправлять деньги за пользование

### Сборка и запуск

```bash
docker compose -f docker-compose.yml -f docker/docker-compose.prod.yml config > docker-compose.deploy.yml
docker compose -f docker-compose.deploy.yml up -d --build
``` 

### Добавление серверов

Чтобы добавить сервер откроем БД sqlite:
```bash
sudo sqlite3 /var/lib/docker/volumes/vpn-telegram-bot_bot_service_data/_data/db.sqlite3
```

Далее выполним вставку в таблицу (замените реальными значениями):
```sql
insert into server(country_code, ip_address, api_url, is_active)
values ('Russia', '192.168.0.1', '****', 1);
```

create table bot_user (
  telegram_id bigint primary key,
  telegram_name  varchar(80),
  telegram_fullname  varchar(80),
  is_active   integer
  created_at timestamp default current_timestamp not null
);



create table user_key(
  id            integer primary key AUTOINCREMENT,
  telegram_id   bigint,
  key_name      varchar(60),
  key_body      varchar(255)
);

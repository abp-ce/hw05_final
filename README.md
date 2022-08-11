# Yatube

Социальная сеть для публикации дневников.

*Разработан по классической MVT архитктуре. Используется пагинация постов и кэширование. Регистрация реализована с верификацией данных, сменой и восстановлением пароля через email. Написаны тесты, проверяющие работу сервиса.*


#

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/abp-ce/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Создать директории:

```
mkdir yatube/static yatube/media yatube/sent_emails
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```

### Стек:
- Django 2.2.16
# Yatube_blog
### Описание
Блог "Yatube" это проект на котором пользователи могут публиковать посты, а также смотреть и комментировать чужие.
### Возможности
- Зарегистрировать свою учетную запись; 
- Публиковать посты;
- Добавлять картинки к постам; 
- Комментировать чужие посты;
- Подписываться/отписываться на избранных авторов;
- Есть возможность разбиения постов по группам.
### Технологии
- Python 3.7
- Django 2.2.6
- SQLite

### Зайдите на север и клонируйте проект 
```
git clone git@github.com:Kirill1709/Yatube_blog.git
```
### Запуск проекта

- Примените миграции
```bash
python manage.py migrate
``` 
- Создайте суперпользователя и введите данные
```bash
python manage.py createsuperuser
```
- Запустите проект
```bash
python manage.py runserver
```


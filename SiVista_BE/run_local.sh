export DJANGO_ENV=.env.local

# python manage.py makemigrations
# python manage.py migrate
# python manage.py setup

# sudo systemctl stop redis
redis-server --daemonize yes
# celery -A SiVista_BE worker --loglevel=debug --detach

python manage.py runserver
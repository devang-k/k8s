export DJANGO_ENV=.env.dev
source SiVista_BE/.env.dev
JSON_CONTENT=$(cat "$GOOGLE_APPLICATION_CREDENTIALS_DEV" | jq -c .)
export GOOGLE_APPLICATION_CREDENTIALS_DEV="$JSON_CONTENT"

# python manage.py makemigrations
# python manage.py migrate
# python manage.py setup

# sudo systemctl stop redis
# redis-server --daemonize yes
# celery -A SiVista_BE worker --loglevel=debug --detach

python3 manage.py runserver
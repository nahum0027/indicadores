web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py crear_grupos && gunicorn config.wsgi --bind 0.0.0.0:$PORT --workers 2 --log-file -

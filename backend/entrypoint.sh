echo "Applying migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Starting Daphne..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
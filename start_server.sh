cd backend
gunicorn -w 1 -b 127.0.0.1:8000 wsgi:app
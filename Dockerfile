# Django (módulo de administración: catálogo, mermas y reportes)
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# Servidor de desarrollo: suficiente para la demo local. Con DJANGO_DEBUG=True sirve también los estáticos del admin.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

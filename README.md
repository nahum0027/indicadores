# Indicadores semanales

Cada dirección (Operaciones, Administración, Jurídica) captura sus indicadores de la semana anterior
antes del **lunes a las 10:00**. El tablero muestra quién entregó, KPIs con variación contra la semana
anterior y gráficas de las últimas 12 semanas.

## Local
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
set DEBUG=True   # o export DEBUG=True
python manage.py migrate
python manage.py crear_grupos
python manage.py createsuperuser
python manage.py datos_demo --sin-ultima   # opcional: 11 semanas de prueba
python manage.py runserver
```

## Usuarios
En `/admin/` → Usuarios: crea uno por director y asígnale su grupo
(`Operaciones`, `Administracion`, `Juridico`). El grupo `Direccion` solo consulta el tablero.

## Variables en Railway
| Variable | Valor |
|---|---|
| `SECRET_KEY` | cadena larga aleatoria |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_PASSWORD` | admin inicial (se crea solo en el primer arranque) |
| `BLOQUEAR_TARDE` | `True` para impedir capturas después del límite (por defecto se aceptan marcadas "tarde") |
| `HORA_LIMITE` | `10` |

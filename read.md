docker exec -it chefchefe-web bash
python manage.py createsuperuser
python manage.py migrate

DATABASE_URL=postgresql://chefchefe:27ddef04919c3ad70e936c3af9920d2e@postgres:5432/chefchefe
DEBUG=True
POSTGRES_DB=chefchefe
POSTGRES_PASSWORD=27ddef04919c3ad70e936c3af9920d2e
POSTGRES_USER=chefchefe
TZ=America/Araguaina
LANGUAGE_CODE=pt-br
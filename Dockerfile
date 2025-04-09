FROM python:3.13-slim-bullseye AS production

ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR.UTF-8 \
    LC_ALL=pt_BR.UTF-8 \
    PYTHONUNBUFFERED=1

WORKDIR /srv


EXPOSE 8000



CMD ["uvicorn", "chefchefe.asgi:application", "--host", "0.0.0.0", "--port", "8000"]

# Instala dependências de sistema
RUN echo "$LANG UTF-8" > /etc/locale.gen && \
    useradd -M -d /srv srv && \
    chown -R srv: /srv && \
    apt update && \
    apt upgrade -y && \
    apt install -y \
        curl \
        dumb-init \
        locales \
        python3-pil \
        python3-pip \
        libpq-dev \
        gcc && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Atualiza pip, setuptools e wheel antes de instalar os requisitos
RUN pip install --upgrade pip setuptools wheel

# Copia os arquivos de requisitos e instala as dependências
RUN mkdir -p /srv/requirements
COPY --chown=srv:srv ./requirements/base.txt /srv/requirements/base.txt
COPY --chown=srv:srv ./requirements/dev.txt /srv/requirements/dev.txt
COPY --chown=srv:srv ./requirements/prod.txt /srv/requirements/prod.txt
RUN pip install --no-cache-dir -r /srv/requirements/prod.txt

# Define o usuário e copia o código-fonte
USER srv
COPY --chown=srv:srv ./src /srv

RUN python manage.py collectstatic --noinput
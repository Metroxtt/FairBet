# Usamos una imagen base ligera pero completa 
FROM python:3.12-slim

# Configuraciones de entorno 
ENV PYTHONDONTWRITEBYTECODE=1
# Asegura que la salida de la consola (logs, prints) se envíe directamente al terminal sin buffer
ENV PYTHONUNBUFFERED=1

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema operativo 
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo de dependencias
COPY requirements.txt /app/

# Instalamos las dependencias de Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiamos el resto del código fuente al contenedor 
COPY ./src /app/
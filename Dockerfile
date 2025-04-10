# Usamos una imagen base de Python 3.11
FROM python:3.11-slim

# Instalamos las dependencias del sistema necesarias, incluyendo el controlador ODBC para SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean

# Establecemos el directorio de trabajo en el contenedor
WORKDIR /app

# Copiamos el archivo requirements.txt al contenedor
COPY requirements.txt /app/

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código fuente
COPY . /app/

# Exponemos el puerto 10000
EXPOSE 10000

# Comando para ejecutar la aplicación
CMD ["python", "API-Crossover-Quiter.py"]

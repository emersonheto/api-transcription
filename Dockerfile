# Imagen base: Python 3.11 (slim para ser pequeña)
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Instalar uv (más rápido que pip)
RUN pip install --no-cache-dir uv

# Copiar archivos de configuración
COPY pyproject.toml ./
COPY uv.lock ./

# Crear entorno virtual e instalar dependencias con uv
# --no-dev para instalar solo lo necesario para producción
RUN uv sync --no-dev --frozen

# Copiar el código fuente
COPY . .

# Exponer puerto 8000
EXPOSE 8000

# Comando para ejecutar la app
# uvicorn corre app.main:app en host 0.0.0.0 (requerido por Docker/Render)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
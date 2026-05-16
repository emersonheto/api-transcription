# Usar imagen oficial de uv con Python 3.11
FROM ghcr.io/astral-sh/uv:python3.11-slim

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración
COPY pyproject.toml ./

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
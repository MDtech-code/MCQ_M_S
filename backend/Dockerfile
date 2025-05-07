FROM python:3.11-slim-bullseye

WORKDIR /app


RUN echo "deb http://deb.debian.org/debian bullseye main" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bullseye-security main" >> /etc/apt/sources.list


RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev-compat \
    libssl-dev \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \ 
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# # Copy SSL certificates
# COPY ssl/ /app/ssl/

# Use entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

CMD ["sh","./entrypoint.sh"]
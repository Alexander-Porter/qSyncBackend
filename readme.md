# QSyncBackend
QSyncBackend is a simple backend written in Python for syncing files between two directories. It is designed to be used with [QSyncUi](https://github.com/LawPlusThree/QSyncUi).

## Run from source
1. Clone the repository
2. Install the requirements using `pip install -r requirements.txt`
3. Create a `.env` file in the root directory of the repository with .env.example as a template
4. Run the backend using `gunicorn -w 4 -b 127.0.0.1：8080 app:app`

## Run from Docker
1. Set your mysql, and create user and database.

2. Run the backend using Docker with the following command, replacing the placeholders with your actual values:

    ```bash
    docker run -d -p 8099:8080 -e DB_USER=your_username -e DB_PASSWORD=your_password -e DB_NAME=your_database_name -e DB_HOST=your_database_host -e SECRET_KEY=your_secret_key_here -e NEED_CAPTCHA=True ghcr.io/alexander-porter/qsyncbackend:main
    ```

## Run from Docker Compose
1. Set the environment variables in a `.env` file
2. Docker-Compose
```yaml
version: '3.8'
services:
  mysql:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: "${DB_PASSWORD}"
      MYSQL_DATABASE: "${DB_NAME}"
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-p${DB_PASSWORD}"]
      interval: 30s
      timeout: 30s
      retries: 5

  web:
    image: ghcr.io/alexander-porter/qsyncbackend:main
    ports:
      - "8099:8080"
    environment:
      SECRET_KEY: "${SECRET_KEY}"
      DB_PASSWORD: "${DB_PASSWORD}"
      DB_NAME: "${DB_NAME}"
    depends_on:
      mysql:
          condition: service_healthy



volumes:
  mysql-data:
```
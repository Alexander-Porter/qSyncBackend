# QSyncBackend
QSyncBackend is a simple backend written in Python for syncing files between two directories. It is designed to be used with QSyncUi.

## Run from source
1. Clone the repository
2. Install the requirements using `pip install -r requirements.txt`
3. Create a `.env` file in the root directory of the repository with .env.example as a template
4. Run the backend using `gunicorn -w 4 -b 127.0.0.1：8080 app:app`

## Run from Docker
1. Modify the `.env` file to set your MySQL database credentials:

    ```bash
    DB_USER=your_username
    DB_PASSWORD=your_password
    DB_NAME=your_database_name
    DB_HOST=your_database_host
    SECRET_KEY=your_secret_key_here
    NEED_CAPTCHA=True
    ```

2. Run
    ```bash
    docker run -d -p 8099:8080 --env-file .env  ghcr.io/alexander-porter/qsyncbackend:main
    ```

## Run from Docker Compose
1. Clone the repository
2. Run
    ```bash
    docker-compose up -d
    ```
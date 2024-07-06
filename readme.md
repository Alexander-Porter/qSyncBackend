# QSyncBackend
QSyncBackend is a simple backend written in Python for syncing files between two directories. It is designed to be used with QSyncUi.

## Run from source
1. Clone the repository
2. Install the requirements using `pip install -r requirements.txt`
3. Create a `.env` file in the root directory of the repository with .env.example as a template
4. Run the backend using `gunicorn -w 4 -b 127.0.0.1：8080 app:app`

## Run from Docker

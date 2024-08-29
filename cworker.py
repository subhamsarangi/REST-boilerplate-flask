from app import create_app, celery

app=create_app(config_class='development')

celery = celery  # Ensure this is the same Celery instance used in the app

if __name__ == '__main__':
    celery.start(argv=['worker', '-E', '-lINFO', '-Psolo'])

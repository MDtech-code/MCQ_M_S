1- to run django server on local host
python manage.py runsslserver --certificate C:\Users\ROCK_MD\localhost.pem --key C:\Users\ROCK_MD\localhost-key.pem




import logging
logger = logging.getLogger(__name__)

def my_view(request):
    logger.debug("Processing request from %s", request.user)
    logger.info("Order created: %d", order.id)
    logger.error("Payment failed: %s", error)


python -m celery -A config worker --pool=threads --loglevel=info


python manage.py runsslserver 0.0.0.0:8000 --certificate /app/ssl/localhost.pem --key /app/ssl/localhost-key.pem
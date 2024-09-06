import logging
import time

from app import celery, create_app
from app.mongo_models import ArticleLikeCount

logger = logging.getLogger(__name__)

@celery.task()
def article_task(param):
    try:
        # from app.models import Article
        # app = create_app(config_class='development')
        # with app.app_context():
        #     pass
        time.sleep(3)
        logger.info("Task completed: %s", param)
    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        import traceback
        traceback.print_exc()

@celery.task()
def update_like_count(article_id, value):
    try:
        article_likes = ArticleLikeCount(article_id)
        article_likes.update(value)
        logger.info("Like count for article %s updated", article_id)
    except Exception as e:
        logger.error("Error updating like count: %s", str(e))
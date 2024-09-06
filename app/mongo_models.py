from flask_pymongo import PyMongo

from app import mongo

class ArticleLikeCount:
    def __init__(self, article_id):
        self.article_id = article_id
        if mongo is None:
            raise RuntimeError("MongoDB is not initialized.")
        self.collection = mongo.db.article_like_counts
    
    def get_like_count(self):
        like_count = self.collection.find_one({'article_id': self.article_id})
        return like_count['count'] if like_count else 0
    
    def update(self, count):
        self.collection.update_one(
            {'article_id': self.article_id},
            {'$inc': {'count': count}},
            upsert=True
        )
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

from app.models import Article, User, Like


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True


class ArticleSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Article
        load_instance = True
        exclude = ('search_vector',)

    search_vector = fields.Method("get_search_vector")

    def get_search_vector(self, obj):
        return str(obj.search_vector)
    

class LikeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Like
        load_instance = True


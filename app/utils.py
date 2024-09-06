from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import IntegrityError
import graphene

from app.models import Article
from app.exceptions import NotFoundException

def article_ownership_required(f):
    @wraps(f)
    def decorated_function(article_id, *args, **kwargs):
        user_id = get_jwt_identity()['id']
        article_user_id = Article.get_user_id(article_id)
        
        if article_user_id and user_id != article_user_id:
            return jsonify({'error': 'Article unauthorized'}), 403
        
        return f(article_id, *args, **kwargs)
    return decorated_function

def success_response(message, data=None, status_code=200):
    response = {'status': 'success', 'message': str(message)}
    if data:
        response.update({'data': data})
    return jsonify(response), status_code

def error_response(message, status_code):
    return jsonify({'status': 'error', 'message': str(message)}), status_code



# Response type for success or error messages
class ResponseType(graphene.ObjectType):
    status = graphene.String()
    message = graphene.String()
    data = graphene.String()  # Optional: Adjust based on what type of data you expect to return.

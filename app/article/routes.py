from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db, socketio
from app.models import Article, Like
from app.schemas import ArticleSchema, LikeSchema
from app.utils import article_ownership_required, error_response, success_response
from app.tasks import update_like_count


article_bp = Blueprint('article_bp', __name__)

article_schema = ArticleSchema()
articles_schema = ArticleSchema(many=True)
like_schema = LikeSchema()

@article_bp.route('/', methods=['GET'])
def get_all_public_articles():
    articles = Article.query.filter_by(is_public=True).all()
    return success_response("all public articles fetched", articles_schema.dump(articles))


@article_bp.route('/user/published/', methods=['GET'])
@jwt_required()
def get_all_published_articles():
    user = get_jwt_identity()
    articles = Article.query.filter_by(is_public=True, user_id=user['id']).all()
    return success_response("users published articles fetched", articles_schema.dump(articles))

@article_bp.route('/user/private/', methods=['GET'])
@jwt_required()
def get_all_draft_articles():
    user = get_jwt_identity()
    articles = Article.query.filter_by(is_public=False, user_id=user['id']).all()
    return success_response("users draft articles fetched", articles_schema.dump(articles))


@article_bp.route('/search/', methods=['POST'])
def search_public_articles():
    data = request.get_json()
    query = data.get('q')
    if not query:
        return jsonify([])

    results = Article.query.filter(
        Article.is_public == True,
        Article.search_vector.match(query)
    ).all()

    return success_response("searched articles fetched", articles_schema.dump(results))


@article_bp.route('/<string:slug>/', methods=['GET'])
@jwt_required()
def get_article_by_slug(slug):
    article = Article.query.filter_by(slug=slug).first_or_404()
    if article.is_public or get_jwt_identity()['id'] == article.user_id:
        return success_response("article fetched", article_schema.dump(article))
    else:
        return error_response("you dont have permission to view this one", 401)


@article_bp.route('/', methods=['POST'])
@jwt_required()
def create_article():
    data = request.get_json()
    user_id = get_jwt_identity()['id']
    article = Article.add(
        data['title'],
        data['content'],
        data.get('hero_image') or None,
        data.get('is_public', False),
        user_id
    )
    return success_response("article created", article_schema.dump(article), 201)


@article_bp.route('/<int:article_id>/', methods=['PUT'])
@jwt_required()
@article_ownership_required
def update_article(article_id):
    data = request.get_json()
    Article.update(
        article_id,
        title=data.get('title'),
        content=data.get('content'),
        hero_image=data.get('hero_image'),
    )

    return success_response("article updated")


@article_bp.route('/<int:article_id>/public/', methods=['PUT'])
@jwt_required()
@article_ownership_required
def make_article_public(article_id):
    Article.update(article_id, is_public=True)
    return success_response("article made public")
    


@article_bp.route('/<int:article_id>/private/', methods=['PUT'])
@jwt_required()
@article_ownership_required
def make_article_private(article_id):
    Article.update(article_id, is_public=False)
    return success_response("article made private/draft")


@article_bp.route('/<int:article_id>/', methods=['DELETE'])
@jwt_required()
@article_ownership_required
def delete_article(article_id):
    Article.delete(article_id)
    return success_response("article trashed")


@article_bp.route('/<int:article_id>/like/', methods=['GET'])
@jwt_required()
def like_article(article_id):
    user_id = get_jwt_identity()['id']
    Like.add(user_id, article_id)
    task = update_like_count.delay(article_id, 1)
    socketio.emit('message', {'data': f"Task {task.id} has started."})
    return success_response("article liked")

@article_bp.route('/<int:article_id>/unlike/', methods=['GET'])
@jwt_required()
def unlike_article(article_id):
    user_id = get_jwt_identity()['id']
    Like.delete(user_id, article_id)
    task = update_like_count.delay(article_id, -1)
    socketio.emit('message', {'data': f"Task {task.id} has started."})
    return success_response("article unliked")

from datetime import datetime
from slugify import slugify
import secrets
import string

from sqlalchemy import event, select, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm.attributes import get_history

from app import db
from app.exceptions import NotFoundException


class User(db.Model):
    __tablename__ = 'flask_user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(150), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    @classmethod
    def get_user_data(cls, user_id):
        user = cls.query.filter_by(id=user_id).first()
        if not user:
            raise NotFoundException("user not registered.")
        
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'is_admin': user.is_admin
        }

    @classmethod
    def get_user_by_email(cls, email):
        user = cls.query.filter_by(email=email).first()
        if not user:
            raise NotFoundException("user not registered.")
        
        return user

    @classmethod
    def add(cls, name, email, password, is_admin=False):
        new_user = cls(
            name=name,
            email=email,
            password=password,
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user


class Article(db.Model):
    __tablename__ = 'flask_article'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    hero_image = db.Column(db.String(200), nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('flask_user.id'), nullable=False)
    user = db.relationship('User', backref='articles')
    search_vector = db.Column(TSVECTOR)

    __table_args__ = (
        UniqueConstraint('user_id', 'title', name='unique_user_title'),
        db.Index('ix_article_search_vector', 'search_vector', postgresql_using='gin'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.slug:
            self.generate_slug()


    def generate_slug(self):
        base_str = slugify(self.title)
        random_str = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        self.slug = f"{base_str}-{random_str}"

    def save(self):
        if not self.id:
            self.generate_slug()
        elif self.title_changed:
            self.generate_slug()
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_user_id(cls, article_id):
        stmt = select(cls.user_id).filter_by(id=article_id)
        return db.session.execute(stmt).scalar_one_or_none()

    @classmethod
    def add(cls, title, content, hero_image, is_public, user_id):
        new_article = cls(
            title=title,
            content=content,
            hero_image=hero_image,
            is_public=is_public,
            user_id=user_id
        )
        new_article.save()
        return new_article

    @classmethod
    def update(cls, article_id, title=None, content=None, hero_image=None, is_public=None):
        article = cls.query.get(article_id)
        if not article:
            raise NotFoundException("article not found.")
        if title is not None:
            article.title = title
        if content is not None:
            article.content = content
        if hero_image is not None:
            article.hero_image = hero_image
        if is_public is not None:
            article.is_public = is_public
        
        article.save()


    @classmethod
    def delete(cls, article_id):
        article = cls.query.get(article_id)
        if not article:
            raise NotFoundException("article not found.")
        db.session.delete(article)
        db.session.commit()

    @staticmethod
    def generate_search_vector(mapper, connection, target):
        target.search_vector = db.func.to_tsvector('english', target.title + ' ' + target.content)

    @property
    def title_changed(self):
        history = get_history(self, 'title')
        return history.has_changes()

event.listen(Article, 'before_insert', Article.generate_search_vector)
event.listen(Article, 'before_update', Article.generate_search_vector)


class Like(db.Model):
    __tablename__ = 'flask_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('flask_user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('flask_article.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint('user_id', 'article_id', name='unique_user_article_like'),
    )

    @classmethod
    def add(cls, user_id, article_id):
        new_like = cls(
            user_id=user_id,
            article_id=article_id
        )
        db.session.add(new_like)
        db.session.commit()

    @classmethod
    def delete(cls, user_id, article_id):
        like_obj = cls.query.filter_by(user_id=user_id, article_id=article_id).first()
        if not like_obj:
            raise NotFoundException("like not found.")
        db.session.delete(like_obj)
        db.session.commit()

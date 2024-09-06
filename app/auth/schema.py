import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

from app import db, bcrypt
from app.models import User
from app.utils import ResponseType

# SQLAlchemy UserType for GraphQL
class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User

# User Schema for registering new users and validating their data
class RegisterInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String(required=True)

# Mutation for Registering a User
class RegisterUser(graphene.Mutation):
    response = graphene.Field(ResponseType)

    class Arguments:
        input = RegisterInput(required=True)

    def mutate(self, info, input):
        existing_user = User.query.filter_by(email=input.email).first()
        if existing_user:
            return RegisterUser(response=ResponseType(status="error", message="User with this email already exists"))

        hashed_password = bcrypt.generate_password_hash(input.password).decode('utf-8')
        new_user = User(name=input.name, email=input.email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return RegisterUser(response=ResponseType(status="success", message="User registered successfully"))


# Mutation for Logging in a User
class LoginUser(graphene.Mutation):
    response = graphene.Field(ResponseType)
    access_token = graphene.String()
    refresh_token = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            return LoginUser(response=ResponseType(status="error", message="Invalid credentials"))

        access_token = create_access_token(identity={'id': user.id, 'is_admin': user.is_admin})
        refresh_token = create_refresh_token(identity={'id': user.id, 'is_admin': user.is_admin})

        return LoginUser(
            response=ResponseType(status="success", message="Logged in successfully"),
            access_token=access_token,
            refresh_token=refresh_token
        )



# Query for fetching the current user's profile
class Query(graphene.ObjectType):
    profile = graphene.Field(UserType)
    response = graphene.Field(ResponseType)

    @jwt_required()
    def resolve_profile(self, info):
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        if not user:
            return None
        return user

    @jwt_required()
    def resolve_response(self, info):
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        if not user:
            return ResponseType(status="error", message="User not found")
        return ResponseType(status="success", message="Profile fetched successfully")


# Mutation for Refreshing Access Token
class RefreshToken(graphene.Mutation):
    access_token = graphene.String()
    message = graphene.String()

    @jwt_required(refresh=True)
    def mutate(self, info):
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user)
        return RefreshToken(
            access_token=new_access_token,
            message="Token refreshed successfully"
        )


# Root Mutation for handling user actions (register, login, refresh token)
class Mutation(graphene.ObjectType):
    register = RegisterUser.Field()
    login = LoginUser.Field()
    refresh_token = RefreshToken.Field()

# Combine Queries and Mutations into the GraphQL Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
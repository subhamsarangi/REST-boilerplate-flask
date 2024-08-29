from sqlalchemy.exc import IntegrityError
from flask import jsonify


class NotFoundException(Exception):
    pass

def handle_exception(e):
    response = {'status': 'error', 'message': 'An unexpected error occurred.'}
    status_code = 500
    if isinstance(e, NotFoundException):
        response['message'] = str(e)
        status_code = 404
    elif isinstance(e, IntegrityError):
        if 'unique_user_title' in str(e.orig):
            response['message'] =  'You have already created an article with this title before.'
            status_code = 400
        elif "user_email_key" in str(e.orig):
            response['message'] =  "Email is taken"
            status_code = 400
        elif "unique_user_article_like" in str(e.orig):
            response['message'] =  "you have already liked this"
            status_code = 400
        else:
            response['message'] = f'Database integrity error. {str(e)}'
    else:
        response['message'] = f'An unexpected error occurred. {str(e)}'
    return jsonify(response), status_code

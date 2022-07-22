from main.models import AuthModel, BookModel
from flask import request, make_response, jsonify, render_template
from main.config import Config_app
from flask_jwt_extended import get_jwt_identity, jwt_required, current_user, create_access_token, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash

from main import app, db, jwt_app

import redis
jwt_redis_blocklist = redis.StrictRedis(
    host="redis-14313.c239.us-east-1-2.ec2.cloud.redislabs.com", port=14313, db=0, decode_responses=True, password=Config_app.cloud_redis_pwd
)

@jwt_app.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None

@jwt_app.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt_app.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return AuthModel.query.filter_by(id=identity).one_or_none()

@app.route('/api/register', methods=['POST'])
def signup_user():
    dataUsername = request.form.get('username')
    dataPassword = request.form.get('password')
    dataIsactive = request.form.get('active')
    hashed_password = generate_password_hash(password=dataPassword, method='pbkdf2:sha256', salt_length=8)

    user = AuthModel.query.filter_by(username=dataUsername).first()
    if not user:
        if dataUsername and dataPassword:
            dataModel = AuthModel(username=dataUsername, password=hashed_password, active=int(dataIsactive))
            db.session.add(dataModel)
            db.session.commit()
            return make_response(jsonify({"msg": "Register Success"}), 200)
        return jsonify({"msg": "Username / Password cannot empty"})
    else:
        return jsonify({"msg": "Username registered"})

@app.route('/api/login', methods=['POST'])
def login_user():
    dataUsername = request.form.get('username')
    dataPassword = request.form.get('password')

    user = AuthModel.query.filter_by(username=dataUsername).one_or_none()

    if not user:
        return jsonify({"msg": "User not Registered, please register !!!"})
    if not check_password_hash(user.password, dataPassword):
        return jsonify({"msg": "Wrong Password, please try again !!!"})
    else:
        access_token = create_access_token(identity=user)
        return jsonify(access_token=access_token)

@app.route('/api/logout', methods=('GET', 'POST'))
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    jwt_redis_blocklist.set(jti, "", ex=Config_app.ACCESS_EXPIRES)
    return jsonify(msg="logout success")

@app.route('/api/addbook', methods=['POST'])
@jwt_required()
def add_book():
    dataTitle = request.form.get('title')
    dataDescription = request.form.get('description')
    dataContent = request.form.get('content')
    dataOwnedby = current_user.id

    if dataTitle :
        dataModel = BookModel(title=dataTitle, description=dataDescription, content=dataContent, create_by_id=dataOwnedby)
        db.session.add(dataModel)
        db.session.commit()
        return make_response(jsonify({"msg": "add book success"}), 200)
    return jsonify({"msg": "failed adding book"})

@app.route('/api/edit_book/<int:id>', methods=["GET", "POST"])
@jwt_required()
def edit_book(id):
    book_to_edit = BookModel.query.get(id)

    dataTitle = request.form.get('title')
    dataDescription = request.form.get('description')
    dataContent = request.form.get('content')

    book_to_edit.title = dataTitle
    book_to_edit.description = dataDescription
    book_to_edit.content = dataContent

    db.session.commit()
    return make_response(jsonify({"msg":"data_edited"}), 200)

@app.route('/api/getallbook', methods=['GET'])
@jwt_required()
def get_all_book():

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)

    books = BookModel.query.paginate(page=page, per_page=per_page)

    output = []

    for book in books.items:
        output.append({
            'id': book.id,
            "title" : book.title,
             "content" : book.content,
             "description" : book.description,
             "created_at" : book.created_at,
             "deleted" : book.deleted,
             "create_by_id" : book.create_by_id
        })

    meta = {
        "page": books.page,
        'pages': books.pages,
        'total_count_data': books.total,
        'prev_page': books.prev_num,
        'next_page': books.next_num,
        'has_next': books.has_next,
        'has_prev': books.has_prev,
        'count_data_per_page' : books.per_page,

    }
    return make_response(jsonify({'data': output, "meta": meta}), 200)

@app.route('/api/getbookbyid/<int:id>', methods=['GET'])
@jwt_required()
def get_book_by_id(id):
    data = BookModel.query.filter_by(id=id).all()
    id = [o.id for o in data]
    title = [x.title for x in data]
    content = [x.content for x in data]
    description = [x.description for x in data]
    created_at = [x.created_at for x in data]
    deleted = [x.deleted for x in data]
    create_by_id = [x.create_by_id for x in data]
    data_output = []
    for data in range(len(id)):
        output = {
            "id": id[data],
            "title": title[data],
            "content": content[data],
            "description": description[data],
            "created_at": created_at[data],
            "deleted": deleted[data],
            "create_by_id": create_by_id[data]
        }
        data_output.append(output)
    print(data_output)
    return make_response(jsonify(data_output), 200)

@app.route('/api/delete_book/<int:id>', methods=['POST'])
@jwt_required()
def delete_book(id):
    activity_to_delete = BookModel.query.get(id)
    dataDeleted = request.form.get('delete')
    activity_to_delete.deleted = dataDeleted

    db.session.commit()
    return make_response(jsonify({"msg":"data_status_is_deleted"}), 200)
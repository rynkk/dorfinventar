import os
import uuid
import pathlib
import datetime

from passlib.hash import argon2
from flask import jsonify, request, Blueprint
from backend import app, db
from backend.models import User, Category, Article, Conversation, Message
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def error(msg):
    """Helper function to create consistent JSON error messages"""
    return jsonify({"error": msg})

@app.route("/dashboard")
def dashboard():
    return error("Admin template. No data to retrieve"), 400

# The blueprint allows the grouping of multiple request. During registration a prefix for all
# urls can be specified
api = Blueprint("api", __name__)

@api.route("auth/register", methods=["POST"])
def register():
    #if not request.is_json:
     #   return error("Expected data to be JSON encoded"), 400
    
    #data = request.get_json()
    username = request.form.get("username", "").lower() # to normalize usernames
    password = request.form.get("password", "")
    email    = request.form.get("email", "")

    password = argon2.hash(password)


    if not (username and password and email):
        return error("Please set a username, password and email address for the registration"), 400

    if User.query.filter((User.username==username) | (User.email==email)).first():
        return error(f"An account with username '{username}' or email address '{email}' already exists"), 400

    user = User(username=username, password=password, email=email)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.serialize), 201


@api.route("auth/login", methods=['POST'])
def login():
    user = request.form.get("username", "")
    password = request.form.get("password", "")

    if not password or not user:
        return error("Please enter a username and password."), 400
    
    user_obj = User.query.filter(User.username == user).one_or_none()
    print(user_obj)
    if user_obj is None or not argon2.verify(password, user_obj.password):
        return error("Wrong username or password."), 401
    
    # login
    return "login", 200

@api.route("categories/", methods=["GET"])
def get_categories():
    return jsonify([c.serialize for c in Category.query.all()]), 200

@api.route("articles/", methods=["GET"])
def get_articles():
    query = Article.query
    if request.args['name']:
        query = query.filter(Article.name.ilike("%"+request.args['name']+"%"))
    if request.args['desc']:
        query = query.filter(Article.name.ilike("%"+request.args['desc']+"%"))
    if request.args['category']:
        query = query.filter(Article.category.ilike(request.args['category']))
    if request.args['status']:
        query = query.filter(Article.status.ilike(request.args['status']))

    return jsonify([c.serialize for c in query.filter().all()]), 200

@api.route("articles/", methods=["PUT"])
def update_article():
    id = request.form.get('id', -1)

    article = Article.query.filter(Article.id == id).one_or_none()
    if article is None:
        return error("Article with id %s not found." % id), 404
    if "name" in request.form:
        article.name = request.form["name"]
    if "desc" in request.form:
        article.desc = request.form["desc"]        
    if "price" in request.form:
        article.price = request.form["price"]        
    if "status" in request.form:
        article.status = request.form["status"]

    db.session.commit()
    return jsonify(article.serialize), 200

@api.route("article/", methods=["POST"])
def create_article():
    name = request.form.get('name', '')
    category = request.form.get('category', '')
    desc = request.form.get('desc', '')
    price = request.form.get('price', 0.0)
    # need middleware here
    owner = "Albert"
    
    if not (name and category and desc and price and owner):
        return error("Name, description, category, price and owner must be specified"), 401

    if not request.files:
        return error("Need at least one image to create article"), 401

    img_folder_uuid = uuid.uuid4().hex
    os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], img_folder_uuid))

    article = Article(status='active', name=name, desc=desc, img_folder=img_folder_uuid, owner=owner,category=category)
    db.session.add(article)
    db.session.commit()

    for index, image in enumerate(request.files):
        image = request.files[image]
        if image and allowed_file(image.filename):
            new_filename = "img%s.%s" %(index, secure_filename(image.filename).split(".")[-1])
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], img_folder_uuid, new_filename))

    return jsonify(article.serialize), 201

@api.route("chat/messages/", methods=['POST'])
def send_message():
    # not sure if data inside form or plain json
    msg = request.form.get("message", "")
    subject = request.form.get("subject", "")
    #origin_user = "token.get_username" v debugging
    origin_user = request.form.get("user1", "")
    other_user = request.form.get("user2", "")
    # step0: check if subject and message are not None
    if not subject:
        return error("Cannot fetch article title"), 400
    if not msg:
        return error("Message cannot be empty"), 400
    # step1: check if origin and other participant exist
    origin_user_obj = User.query.filter(User.username == origin_user).one_or_none()
    other_user_obj = User.query.filter(User.username == other_user).one_or_none()

    if origin_user_obj is None:
        return error("Could not find sender in db: %s" % origin_user), 404
    if other_user_obj is None:
        return error("Could not find participant in db: %s" % other_user), 404

    # step2: check if conversation between origin and participant already exist

    conv = Conversation.query.filter(Conversation.user1.in_([origin_user, other_user]) & \
                                     Conversation.user2.in_([origin_user, other_user]))\
                                    .one_or_none()
    
    # step2.1: falls ja: message zur conversation hinzufügen
    if conv:
        msg_obj = Message(conversation_id=conv.id, message=msg, message_date=datetime.datetime.now())
        db.session.add(msg_obj)    
    # step2.2: falls nein: create conversation, add message to conversation
    else:
        conv_obj = Conversation(subject=subject, user1=origin_user_obj.username, user2=other_user_obj.username)
        db.session.add(conv_obj)
        db.session.flush()
        msg_obj = Message(conversation_id=conv_obj.id, message=msg, sender=origin_user_obj.username,\
                          recipient=other_user_obj.username, message_date=datetime.datetime.now())
        db.session.add(msg_obj)

    db.session.commit()
    return "lol"
        
    
@api.route("/search", methods=["GET"])
def search():
    """
    Suche durchfuhrbar mit Url-Parameter q, z.B. /api/search?q=spachtel
    !!! Achte darauf, dass spachtel nicht von Anführungszeichen umgeben ist, Sonst gibt es keine Suchergebnisse
    Filtern nach status bzw category z.B. via /api/search?q=spachtel&status=active
    """
    query = "%{}%".format(request.args.get("q", ""))
    status = request.args.get("status")
    category = request.args.get("category")
    sql = Article.query.filter(Article.name.like(query) | Article.desc.like(query))

    if status:
        sql = sql.filter(Article.status == status) 

    if category:
        sql = sql.filter(Article.category == category) 

    return jsonify([r.serialize for r in sql.all()]), 200
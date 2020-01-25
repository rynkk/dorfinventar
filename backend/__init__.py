from flask import Flask, json
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import timedelta
import os

app = Flask(__name__, static_folder='file_storage')
UPLOAD_FOLDER = os.path.join(app.static_folder, 'images')
app.config['SECRET_KEY'] = 'f03b64dca19c7e6e86b419e8c3abf4db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dorfinv.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 # 4 MB UploadSize Limit
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=30)
app.config['JWT_AUTH_URL_RULE'] = "/api/auth/login" # url to get jwt token
db = SQLAlchemy(app)


from backend import models
from backend import routes

admin = Admin(app, 'Database')

from backend.models import User, Category, Article, Image, Conversation, Message

class UserView(ModelView):
    column_display_pk = True
    column_list = ('id', 'username', 'email', 'password')
    #form_columns = ('id', 'status', 'group_id', 'position', 'workers')

class CategoryView(ModelView):
    #column_exclude_list = ('layout')
    column_display_pk = True
    column_list = ('id', 'name', 'desc')

class ArticleView(ModelView):
    column_display_pk = True
    column_list = ('id', 'status', 'name', 'desc', 'img_folder', 'owner', 'category', 'pub_date')
    
class ImageView(ModelView):
    column_display_pk = True
    column_list = ('id', 'path', 'item')

class ConversationView(ModelView):
    column_list = ('id', 'subject', 'user1', 'user2', 'messages')
    column_display_pk = True

class MessageView(ModelView):
    column_display_pk = True
    column_list = ('id', 'sender', 'recipient', 'message', 'pub_date', 'conversation_id')
    form_columns = ('id', 'sender', 'recipient', 'message', 'pub_date', 'conversation_id')

admin.add_view(UserView(User, db.session, 'User'))
admin.add_view(CategoryView(Category, db.session, 'Category'))
admin.add_view(ArticleView(Article, db.session, 'Article'))
admin.add_view(ImageView(Image, db.session, 'Image'))
admin.add_view(ConversationView(Conversation, db.session, 'Conversation'))
admin.add_view(MessageView(Message, db.session, 'Message'))

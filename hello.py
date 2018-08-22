from flask import Flask, render_template, session, redirect, url_for,flash,logging
from flask_script import Manager,Shell
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_migrate import Migrate,MigrateCommand
from wtforms import StringField, SubmitField 
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry
from flask_mail import Mail,Message
from threading import Thread
import os


#全局变量
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
RAVEN_CONFIG = {}
sentry = Sentry(app, dsn='')
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
manager = Manager(app)
migrate = Migrate(app, db)

#数据库迁移
manager.add_command('db', MigrateCommand)


#创建应用
def create_app():
    sentry.init_app(app)   
    return app




#配置更新
#database config
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(basedir, 'data.sqlite') 
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config.update(
    TESTING=True,
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/'
)

#email config
app.config['MAIL_DEBUG'] = True 
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_SERVER'] = 'smtp.126.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
#app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
#app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
#app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

app.config['MAIL_USERNAME'] = 'ZQ050314@126.com'
#授权密码，不是账户密码-网易
app.config['MAIL_PASSWORD'] = 'ZQ050314'
app.config['MAIL_DEFAULT_SENDER'] = 'ZQ050314@126.com'
app.config['FLASKY_MAIL_SENDER'] = 'ZQ050314@126.com'
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_ADMIN'] = '2601841766@qq.com'

#在设置config之后
mail = Mail(app)
#网页路由规则
@app.route('/',methods = ['GET','POST'])
def index():
    app.logger.info('here 1')
    form = NameForm()
    if form.validate_on_submit():
        app.logger.info('here 2')
        user = User.query.filter_by(username=form.name.data).first() 
        if user is None:
            app.logger.info('here 4')
            user = User(username = form.name.data)
            db.session.add(user)
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'],'New User',\
                'mail/new_user',user = user)
        else:
            app.logger.info('here 3')
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html',\
            form = form, name = session.get('name'),
            known = session.get('known', False))

@app.route('/user/<name>')
def user(name):
    return render_template('user.html',name=name)



class NameForm(FlaskForm):
    name = StringField('What is Your name?',validators = [Required()])
    submit = SubmitField('Submit')

#数据模型
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
def __repr__(self):
    return '<User %r>' % self.username

#数据迁移2
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))



#定义错误界面及处理方法
@app.errorhandler(404)
def page_not_found(error):
    app.logger.info('here')
    return render_template('404.html'),404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'),500

@app.errorhandler(400)
def handle_bad_request(error):
    return render_template('400.html'),400

app.register_error_handler(404, page_not_found)
app.register_error_handler(500, internal_server_error)  
app.register_error_handler(400, handle_bad_request)


#邮件发送函数
def send_async_email(app, msg):
         with app.app_context():
             mail.send(msg)

def send_email(to,subject,template,**kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr

#应用入口函数
if __name__ == '__main__':
    app = create_app()
    if app.debug: use_debugger = True
    manager.run()
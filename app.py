import datetime
import flask
import flask_login
import os
import uuid
import logging  # Add this line to import the logging module
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from s3Utils import S3Utils

load_dotenv() 
app = flask.Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # 从.env文件读取

# 使用环境变量配置数据库
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_host = os.getenv("DB_HOST")
if db_host==None:
    db_host="mysql"
if db_user==None:
    db_user="root"

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}"
logger = logging.getLogger(__name__)  # Add this line to define the logger object

myS3=S3Utils(os.getenv("S3_SECRET_ID"), os.getenv("S3_SECRET_KEY"), os.getenv("S3_BUCKET"), os.getenv("S3_REGION"))



login_manager = flask_login.LoginManager()
login_manager.init_app(app)
db = SQLAlchemy(app)


from werkzeug.security import generate_password_hash,check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar_url = db.Column(db.String(200))
    tasks = db.relationship('SyncTask', backref='user', lazy=True)
    devices = db.relationship('Device', backref='user', lazy=True)
    is_active = db.Column(db.Boolean, default=True)
    __table_args__ = { 'mysql_charset' : 'utf8mb4'}
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def get_id(self):
        return self.id
    def is_authenticated(self):
        return True

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deviceName = db.Column(db.String(100), nullable=False)
    lastOnline = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    __table_args__ = { 'mysql_charset' : 'utf8mb4'}

class SyncTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    localDir = db.Column(db.String(200), nullable=False)
    s3Dir = db.Column(db.String(200), nullable=False)
    #syncType is an integer
    syncType = db.Column(db.Integer, nullable=False)
    usedSize = db.Column(db.BigInteger, nullable=False)
    totalSize = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = { 'mysql_charset' : 'utf8mb4'}

@login_manager.user_loader
def user_loader(id):
    return db.session.get(User, id)

@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        email = flask.request.form["email"]
        password = flask.request.form["password"]
        print(email,password,generate_password_hash(password))
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash,password):
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("profile"))
        else:
            #403
            return flask.jsonify({"code": 403, "message": "Email or password incorrect", "data": {}}), 403
    else:
        #method not allowed
        # Set status code to 405
        return flask.jsonify({"code": 405, "message": "Method Not Allowed", "data": {}}), 405

@app.route("/info", methods=["GET"])
@flask_login.login_required
def profile():
    user=flask_login.current_user
    if(user.avatar_url==None):
        avatarUrl=None
    else:
        avatarUrl=myS3.getPreSignUrl(user.avatar_url)
    data={
        "username":user.username,
        "email":user.email,
        "avatar_url":avatarUrl,
        "tasks":[]
    }
    return flask.jsonify({"code": 200, "message": "success", "data": data})

@app.route("/updateInfo", methods=["POST"])
@flask_login.login_required
def updateInfo():
    user=flask_login.current_user
    username = flask.request.form["username"]
    password = flask.request.form["password"]
    user.username=username
    user.set_password(password)
    db.session.commit()
    #200
    return flask.jsonify({"code": 200, "message": "success", "data": {}})

@app.route("/updateAvatar", methods=["POST"])
@flask_login.login_required
def updateAvatar():
    #base64 encoded image
    user=flask_login.current_user
    avatar=flask.request.form.get("avatar")
    if avatar:
        thisUUid=uuid.uuid1()
        uuidStr=str(thisUUid)
        fileType=avatar.split(";")[0].split("/")[1]
        with open(f"{uuidStr}.{fileType}", "wb") as f:
            import base64
            avatar=avatar.split(",")[1]
            avatar=avatar.replace(" ","+")
            avatar = base64.b64decode(avatar)
            f.write(avatar)
        if not fileType in ["png","gif","jpeg"]:
            return flask.jsonify({"code": 403, "message": "Bad Avatar File Type", "data": {}}), 403
        myS3.uploadObject(f"avatars/{uuidStr}.{fileType}",f"{uuidStr}.{fileType}")
        user.avatar_url=f"avatars/{uuidStr}.{fileType}"
        import os
        os.remove(f"{uuidStr}.{fileType}")
    db.session.commit()
    if user.avatar_url==None:
        avatarUrl=None
    else:
        avatarUrl=myS3.getPreSignUrl(user.avatar_url)
    data={
        "avatar_url":avatarUrl
    }
    #200
    return flask.jsonify({"code": 200, "message": "success", "data": data})

@app.route("/register", methods=["POST"])
def register():
    #step=flask.request.form["step"]
    username = flask.request.form["username"]
    email = flask.request.form["email"]

    password = flask.request.form["password"]
    #如果有avatar字段
    avatar=flask.request.form.get("avatar")
    if User.query.filter_by(email=email).first():
        #409
        return flask.jsonify({"code": 409, "message": "Email already exists", "data": {}}), 409
    user = User(username=username, email=email)
    if avatar:
        
        thisUUid=uuid.uuid1()
        uuidStr=str(thisUUid)
        fileType=avatar.split(";")[0].split("/")[1]
        with open(f"{uuidStr}.{fileType}", "wb") as f:
            import base64
            avatar=avatar.split(",")[1]
            avatar=avatar.replace(" ","+")
            avatar = base64.b64decode(avatar)
            f.write(avatar)
        if not fileType in ["png","gif","jpeg"]:
            return flask.jsonify({"code": 403, "message": "Bad Avatar File Type", "data": {}}), 403
        myS3.uploadObject(f"avatars/{uuidStr}.{fileType}",f"{uuidStr}.{fileType}")
        user.avatar_url=f"avatars/{uuidStr}.{fileType}"
        import os
        os.remove(f"{uuidStr}.{fileType}")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    #201
    return flask.jsonify({"code": 201, "message": "success", "data": {}}), 201

@app.route("/deleteAccount",methods=["get"])
@flask_login.login_required
def deleteAccount():
    user=flask_login.current_user
    db.session.delete(user)
    db.session.commit()
    #200
    return flask.jsonify({"code": 200, "message": "success", "data": {}})

@app.route("/tasks",methods=["get"])
@flask_login.login_required
def getTasks():
    user=flask_login.current_user
    tasks=SyncTask.query.filter_by(user_id=user.id)
    data=[]
    for task in tasks:
        data.append({
            "localDir":task.localDir,
            "s3Dir":task.s3Dir,
            "syncType":task.syncType,
            "usedSize":task.usedSize,
            "totalSize":task.totalSize,
            "created_at":task.created_at,
            "id":task.id
        })
    return flask.jsonify({"code": 200, "message": "success", "data": data})

@app.route("/addTask",methods=["post"])
@flask_login.login_required
def addTask():
    user=flask_login.current_user
    localDir=flask.request.form["localDir"]
    s3Dir=flask.request.form["s3Dir"]
    syncType=flask.request.form["syncType"]
    usedSize=flask.request.form["usedSize"]
    totalSize=flask.request.form["totalSize"]
    #判断数据库中S3目录是否被其他用户拥有过
    tasks = SyncTask.query.filter(SyncTask.s3Dir == s3Dir, SyncTask.user_id != user.id).all()
    if tasks:
        # dir is already occupied by other users
        return flask.jsonify({"code": 409, "message": "Directory already occupied", "data": {}}), 409
    #否则，检查S3目录是否存在
    if not myS3.isValidDir(s3Dir):
        return flask.jsonify({"code": 403, "message": "Bad S3 Dir Name", "data": {}}), 403
    if not myS3.isObjectExist(s3Dir):
        try:
            myS3.createDir(s3Dir)
        except Exception as e:
            return flask.jsonify({"code": 500, "message": e, "data": {}}), 500
    mySameTask=SyncTask.query.filter_by(localDir=localDir, s3Dir=s3Dir, user_id=user.id).first()
    if mySameTask:
        return flask.jsonify({"code": 201, "message": "Same Task Already Exists", "data": {}}), 201
    created_at = datetime.datetime.now()
    task = SyncTask(localDir=localDir, s3Dir=s3Dir, syncType=syncType, usedSize=usedSize, totalSize=totalSize, user_id=user.id, created_at=created_at)
    db.session.add(task)
    db.session.commit()
    #get this task and return
    task = SyncTask.query.filter_by(localDir=localDir, s3Dir=s3Dir, user_id=user.id).first()
    data={
        "localDir":task.localDir,
        "s3Dir":task.s3Dir,
        "syncType":task.syncType,
        "usedSize":task.usedSize,
        "totalSize":task.totalSize,
        "created_at":task.created_at,
        "id":task.id
    }
    #201
    return flask.jsonify({"code": 201, "message": "success", "data": data}), 201

@app.route("/deleteTask",methods=["get"])
@flask_login.login_required
def deleteTask():
    user=flask_login.current_user
    task_id=flask.request.args.get("task_id")
    task=SyncTask.query.filter_by(id=task_id).first()
    if task.user_id!=user.id:
        return flask.jsonify({"code": 403, "message": "Permission Denied", "data": {}}), 403
    db.session.delete(task)
    db.session.commit()
    #200
    return flask.jsonify({"code": 200, "message": "success", "data": {}})

@app.route("/getTaskToken",methods=["get"])
@flask_login.login_required
def getTaskToken():
    user=flask_login.current_user
    task_id=flask.request.args.get("task_id")
    task=SyncTask.query.filter_by(id=task_id).first()
    if task.user_id!=user.id:
        return flask.jsonify({"code": 403, "message": "Permission Denied", "data": {}}), 403
    allow_prefix=[task.s3Dir,task.s3Dir+"*"]
    if(task.syncType==1):
        role="upload_download"
    elif(task.syncType==2):
        role="upload"
    else:
        role="download"
    try:
        data=myS3.get_credential_demo(allow_prefix,role)
    except Exception as e:
        return flask.jsonify({"code": 500, "message": e, "data": {}}), 500
    return flask.jsonify({"code": 200, "message": "success", "data": data})

@app.route("/getTaskTokenByS3Dir",methods=["get"])
@flask_login.login_required
def getTaskTokenByS3Dir():
    user=flask_login.current_user
    s3Dir=flask.request.args.get("s3Dir")
    task=SyncTask.query.filter_by(s3Dir=s3Dir,user_id=user.id).first()
    if task==None:
        return flask.jsonify({"code": 404, "message": f"Task {s3Dir} Not Found", "data": {}}), 404
    allow_prefix=[task.s3Dir,task.s3Dir+"*"]
    if(task.syncType==1):
        role="upload_download"
    elif(task.syncType==2):
        role="download"
    else:
        role="upload"
    try:
        data=myS3.get_credential_demo(allow_prefix,role)
    except Exception as e:
        return flask.jsonify({"code": 500, "message": e, "data": {}}), 500
    return flask.jsonify({"code": 200, "message": "success", "data": data})


@app.route("/updateDevice",methods=["post"])
@flask_login.login_required
def updateDevice():
    user=flask_login.current_user
    deviceName=flask.request.form["deviceName"]
    #import time and use standard ts
    import datetime
    lastOnline=datetime.datetime.now()
    device=Device.query.filter_by(user_id=user.id,deviceName=deviceName).first()
    if device:
        device.lastOnline=lastOnline
    else:
        device=Device(deviceName=deviceName,lastOnline=lastOnline,user_id=user.id)
        db.session.add(device)
    db.session.commit()
    #201
    return flask.jsonify({"code": 201, "message": "success", "data": {}}), 201

@app.route("/getDevices",methods=["get"])
@flask_login.login_required
def getDevices():
    user=flask_login.current_user
    devices=Device.query.filter_by(user_id=user.id)
    data=[]
    for device in devices:
        data.append({
            "deviceName":device.deviceName,
            "lastOnline":device.lastOnline
        })
    return flask.jsonify({"code": 200, "message": "success", "data": data})

@app.route("/deleteDevice",methods=["get"])
@flask_login.login_required
def deleteDevice():
    user=flask_login.current_user
    deviceName=flask.request.args.get("deviceName")
    device=Device.query.filter_by(user_id=user.id,deviceName=deviceName).first()
    if device:
        db.session.delete(device)
        db.session.commit()
    #200
    return flask.jsonify({"code": 200, "message": "success", "data": {}})

@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    #200
    return flask.jsonify({"code": 200, "message": "success", "data": {}})


#全局修饰器，程序抛出异常会返回500
@app.errorhandler(500)
def internal_error(error):
    #转成字符串
    error=str(error)
    return flask.jsonify({"code": 500, "message": error, "data": {}}), 500

with app.app_context():
    db.create_all()



if __name__ == "__main__":
    
    app.run(debug=True)

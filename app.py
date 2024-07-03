import flask
import flask_login
from flask_sqlalchemy import SQLAlchemy

app = flask.Flask(__name__)
app.secret_key = "super secret string"  # Change this!

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://syncUser:GWjBsdEQBaerdh3Z@localhost:3307/syncUser'
db = SQLAlchemy(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


from werkzeug.security import generate_password_hash

#stand api response
#{"code":200,"message":"success","data":{}}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar_url = db.Column(db.String(200))
    tasks = db.relationship('SyncTask', backref='user', lazy=True)
    devices = db.relationship('Device', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deviceName = db.Column(db.String(100), nullable=False)
    lastOnline = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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

@login_manager.user_loader
def user_loader(id):
    return User.query.get(id)

@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        email = flask.request.form["email"]
        password = flask.request.form["password"]

        user = User.query.filter_by(id=email).first()
        if user and user.password == password:
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("profile"))
        else:
            #403
            return flask.jsonify({"code": 403, "message": "Email or password incorrect", "data": {}}), 403
    else:
        #method not allowed
        # Set status code to 405
        return flask.jsonify({"code": 405, "message": "Method Not Allowed", "data": {}}), 405

@app.route("/info")
@flask_login.login_required
def profile():
    user=flask_login.current_user
    data={
        "username":user.username,
        "email":user.email,
        "avatar_url":user.avatar_url,
        "tasks":[]
    }
    return flask.jsonify({"code": 200, "message": "success", "data": data})

@app.route("/register", methods=["POST"])
def register():
    step=flask.request.form["step"]
    username = flask.request.form["username"]
    email = flask.request.form["email"]

    password = flask.request.form["password"]
    user = User(username=username, email=email)
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
            "totalSize":task.totalSize
        })
    return flask.jsonify({"code": 200, "message": "success", "data": data})


@app.route("/logout")
def logout():
    flask_login.logout_user()
    #200
    return flask.jsonify({"code": 200, "message": "success", "data": {}})

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from supabase import create_client, Client

# Initialize extensions
login_manager = LoginManager()
socketio = SocketIO()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class User(UserMixin):
    def __init__(self, id_, email):
        self.id = id_
        self.email = email

    @staticmethod
    def get(user_id):
        response = supabase.table("users").select("*").eq("id", user_id).single().execute()
        data = response.data
        if data:
            return User(data["id"], data["email"])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.login_view = 'login'
    login_manager.login_message = 'कृपया लॉगिन करें। Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @app.route("/")
    def home():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]
            response = supabase.table("users").select("*").eq("email", email).single().execute()
            user_data = response.data
            if user_data and user_data.get("password") == password:  # WARNING: Store passwords securely in production!
                user = User(user_data["id"], user_data["email"])
                login_user(user)
                return redirect(url_for("index"))
            else:
                flash("Invalid credentials", "danger")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/index")
    @login_required
    def index():
        response = supabase.table("users").select("id,email").execute()
        users = response.data
        return render_template("index.html", users=users)

    return app

app = create_app()
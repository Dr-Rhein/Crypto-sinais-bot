from flask import Blueprint, render_template

bp = Blueprint('routes', __name__)

@bp.route('/')
def dashboard():
    return render_template('dashboard.html')

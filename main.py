from flask import Flask
from app.routes import bp
from app.trading_bot import iniciar_bot_em_thread

app = Flask(__name__)
app.register_blueprint(bp)

if __name__ == '__main__':
    iniciar_bot_em_thread()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

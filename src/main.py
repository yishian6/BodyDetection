from flask import Flask
import sys
from config import ROOT

sys.path.append(ROOT)
from views import dehaze_view, detect_view, realtime_view, upload_view


app = Flask(__name__, static_url_path="/")


app.register_blueprint(dehaze_view.dehaze_bp)
app.register_blueprint(detect_view.detect_bp)
app.register_blueprint(realtime_view.realtime_bp)
app.register_blueprint(upload_view.upload_dp)


@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True)

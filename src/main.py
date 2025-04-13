import os
from flask import Flask, abort, send_file, request, render_template
import sys

from config import ROOT, UPLOAD_FOLDER

sys.path.append(ROOT)
from views import dehaze_view, detect_view, realtime_view, upload_view, task_view, val_view

app = Flask(__name__, static_folder=os.path.join(ROOT, 'front', 'dist'),  # 设置静态文件夹目录
            template_folder=os.path.join(ROOT, 'front', 'dist'),
            static_url_path="")

app.register_blueprint(dehaze_view.dehaze_bp)
app.register_blueprint(detect_view.detect_bp)
app.register_blueprint(realtime_view.realtime_bp)
app.register_blueprint(upload_view.upload_dp)
app.register_blueprint(task_view.task_bp)
app.register_blueprint(val_view.val_bp)


@app.route("/")
def index():
    return render_template('index.html', name='index')


@app.route('/download')
def download_file():
    # 获取参数
    filename = request.args.get('filename')
    filetype = request.args.get('filetype')
    print("filename:", filename)
    print("filetype:", filetype)

    # 指定文件存储的目录
    filepath = os.path.join(UPLOAD_FOLDER, filetype, filename)
    print("filepath:", filepath)

    # 确保文件存在
    if not os.path.exists(filepath):
        print("File does not exist:", filepath)
        abort(404)

    # 根据文件扩展名设置 MIME 类型
    mimetype = 'application/octet-stream'  # 默认二进制流
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        mimetype = 'image/jpeg'
    elif filename.endswith('.png'):
        mimetype = 'image/png'
    elif filename.endswith('.gif'):
        mimetype = 'image/gif'
    elif filename.endswith('.mp4'):
        mimetype = 'video/mp4'
    elif filename.endswith('.avi'):
        mimetype = 'video/x-msvideo'
    elif filename.endswith('.mov'):
        mimetype = 'video/quicktime'
    elif filename.endswith('.mkv'):
        mimetype = 'video/x-matroska'
    elif filename.endswith('.webm'):
        mimetype = 'video/webm'
    elif filename.endswith('.pdf'):  # 添加对 PDF 文件的支持
        mimetype = 'application/pdf'

    # 发送文件，并设置下载的文件名
    return send_file(filepath, as_attachment=True, mimetype=mimetype)


if __name__ == "__main__":
    app.run(debug=False)

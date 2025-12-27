import os
from flask import Flask, render_template
from config import Config
from routes.upload import upload_bp

def create_app():
    # 兼容性环境变量（建议在导入 PaddleOCR 前设置）
    os.environ.setdefault("HUB_DATASET_ENDPOINT", Config.HUB_DATASET_ENDPOINT)

    app = Flask(__name__)
    app.config.from_object(Config)

    # 确保 uploads 目录存在
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # 注册蓝图
    app.register_blueprint(upload_bp)

    # 简单健康检查
    @app.get("/health")
    def health():
        return {"status": "ok"}

    # 临时首页（后续让 B 同学完善 templates/static）
    # @app.get("/")
    @app.get("/")
    def index():
        return render_template("index.html")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

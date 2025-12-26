"""
Flask 擴充功能初始化
避免循環導入問題
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# 初始化擴充功能（稍後在 app.py 中綁定到 app）
db = SQLAlchemy()
jwt = JWTManager()








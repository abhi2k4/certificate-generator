import os

class Config:
    CERTIFICATE_FOLDER = "certificates"
    TEMPLATE_PATH = "static/certificate_template.png"
    FONT_PATH = "static/Adamiya.ttf"
    FONT_SIZE = 100
    TEXT_COLOR = "black"
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
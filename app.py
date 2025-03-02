from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
import pandas as pd
import os
import re
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Create folder to store generated certificates
os.makedirs(Config.CERTIFICATE_FOLDER, exist_ok=True)

# Load student data
try:
    student_data = pd.read_excel("student_data.xlsx")
    # Ensure required columns exist
    required_columns = ['Moodle ID', 'Name', 'Event Name']
    if not all(col in student_data.columns for col in required_columns):
        raise ValueError("Excel file must contain 'Moodle ID', 'Name', and 'Event Name' columns")
except FileNotFoundError:
    student_data = pd.DataFrame(columns=["Moodle ID", "Name", "Event Name"])
except ValueError as e:
    app.logger.error(f"Excel file error: {e}")
    student_data = pd.DataFrame(columns=["Moodle ID", "Name", "Event Name"])

def validate_student_id(student_id):
    """Validate student ID format (assuming numeric ID)."""
    app.logger.debug(f"Validating student ID: {student_id}")
    is_valid = bool(re.match("^[0-9]+$", student_id))
    app.logger.debug(f"Is valid: {is_valid}")
    return is_valid

def validate_moodle_id(moodle_id):
    """Validate Moodle ID format (assuming numeric ID)."""
    app.logger.debug(f"Validating Moodle ID: {moodle_id}")
    is_valid = bool(re.match("^[0-9]+$", moodle_id))
    app.logger.debug(f"Is valid: {is_valid}")
    return is_valid

def get_student_name(student_id):
    """Get student name from ID."""
    try:
        # Convert student_id to integer for comparison
        student_id = int(student_id)
        app.logger.debug(f"Looking up student ID: {student_id}")
        app.logger.debug(f"Available IDs: {student_data['Moodle ID'].values}")
        student = student_data[student_data['Moodle ID'] == student_id].iloc[0]
        return student['Name']
    except (IndexError, KeyError, ValueError) as e:
        app.logger.error(f"Error getting student name: {e}")
        return None

def get_student_name(moodle_id):
    """Get student name from Moodle ID."""
    try:
        # Convert moodle_id to integer for comparison
        moodle_id = int(moodle_id)
        app.logger.debug(f"Looking up Moodle ID: {moodle_id}")
        app.logger.debug(f"Available IDs: {student_data['Moodle ID'].values}")
        student = student_data[student_data['Moodle ID'] == moodle_id].iloc[0]
        return student['Name']
    except (IndexError, KeyError, ValueError) as e:
        app.logger.error(f"Error getting student name: {e}")
        return None

def get_student_info(moodle_id):
    """Get student name and event from Moodle ID."""
    try:
        moodle_id = int(moodle_id)
        app.logger.debug(f"Looking up Moodle ID: {moodle_id}")
        student = student_data[student_data['Moodle ID'] == moodle_id].iloc[0]
        return student['Name'], student['Event Name']
    except (IndexError, KeyError, ValueError) as e:
        app.logger.error(f"Error getting student info: {e}")
        return None, None

def validate_name(name):
    """Validate student name."""
    return bool(re.match("^[a-zA-Z ]+$", name))

def generate_certificate(name, event):
    """Generate certificate for a given name and event."""
    cert_path = os.path.join(Config.CERTIFICATE_FOLDER, f"{secure_filename(name)}_{secure_filename(event)}_certificate.png")
    
    if os.path.exists(cert_path):
        return cert_path

    try:
        # Select template based on event
        if event.lower() == "aiml bootcamp":
            template_path = os.path.join("templates", "aiml_template.png")
        elif event.lower() == "dsa bootcamp":
            template_path = os.path.join("templates", "dsa_template.png")
        else:
            raise ValueError(f"Invalid event: {event}")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Certificate template not found at {template_path}")
        if not os.path.exists(Config.FONT_PATH):
            raise FileNotFoundError(f"Font file not found at {Config.FONT_PATH}")

        # Load certificate template
        image = Image.open(template_path)
        draw = ImageDraw.Draw(image)
        
        # Load font
        font = ImageFont.truetype(Config.FONT_PATH, Config.FONT_SIZE)
        
        # Get image dimensions
        image_width, image_height = image.size
        
        # Get text size using textbbox instead of deprecated textsize
        text_bbox = draw.textbbox((0, 0), name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Set position (centered)
        x_position = (image_width - text_width) // 2
        y_position = (image_height - text_height) // 2
        
        # Draw name on certificate
        draw.text((x_position, y_position), name, font=font, fill=Config.TEXT_COLOR)
        
        # Save certificate
        image.save(cert_path)
        return cert_path
    
    except FileNotFoundError as e:
        app.logger.error(f"File error: {e}")
        return None
    except Exception as e:
        app.logger.error(f"Unexpected error generating certificate: {e}")
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    moodle_id = request.form.get("moodle_id", "").strip()
    
    if not moodle_id or not validate_moodle_id(moodle_id):
        return "Invalid Moodle ID provided", 400
    
    student_name, event_name = get_student_info(moodle_id)
    if student_name and event_name:
        cert_path = generate_certificate(student_name, event_name)
        if cert_path:
            try:
                return send_file(cert_path, as_attachment=True)
            except Exception as e:
                app.logger.error(f"Error sending file: {e}")
                return "Error downloading certificate. Please try again.", 500
        else:
            return "Error generating certificate. Please try again.", 500
    else:
        return "Moodle ID not found or no event associated. Please check your ID and try again.", 404

if __name__ == "__main__":
    app.run(debug=True)

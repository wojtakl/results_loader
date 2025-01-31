from flask import Flask, request, render_template, redirect, url_for
import os
import logging
import requests

app = Flask(__name__)

FILE_PROCESSOR_URL = os.getenv('FILE_PROCESSOR_URL', 'http://127.0.0.2:5000/')
QUARRY_URL = os.getenv('QUARRY_URL', 'http://127.0.0.3:8003/')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

logger.info(f"{FILE_PROCESSOR_URL=}")
logger.info(f"{QUARRY_URL=}")
ALLOWED_EXTENSIONS = {'csv', 'txt'}
app.config['FILE_PROCESSOR_URL'] = FILE_PROCESSOR_URL

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part in the request', 400
    file = request.files['file']

    if file.filename == '':
        return 'No file selected for uploading', 400

    if file and allowed_file(file.filename):
        try:
            # Forward the file to the FileProcessor microservice
            files = {'file': (file.filename, file.stream, file.content_type)}
            response = requests.post(f"{app.config['FILE_PROCESSOR_URL']}process-file", files=files)
            logger.info(response)
            if response.status_code == 200:
                return render_template("index.html", feedback=f"File {file.filename} successfully processed by FileProcessor! {response.text}")
            else:
                return render_template("index.html", feedback=f"Error from FileProcessor: {response.text}; {response.status_code}")
        except requests.exceptions.RequestException as e:
            return render_template("index.html", feedback=f"Failed to connect to FileProcessor service: {str(e)}")
    else:
        return 'File type not allowed', 400
    
@app.route("/query-order", methods=["POST"])
def query_order():
    order_number = request.form.get("order_number")
    if not order_number:
        return render_template("index.html", results="Order number is required.")

    try:
        response = requests.get(f"{QUARRY_URL}find_results/{order_number}")
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as e:
        return render_template("index.html", results=f"Error querying database: {e}")

    return render_template("index.html", results=results)

@app.route("/query-plot", methods=["POST"])
def query_plot():
    result_id = request.form.get("result_id")

    if not result_id:
        return render_template("index.html", plot_html=None, error="Query parameter is required.")
    try:
        response = requests.get(f"{QUARRY_URL}/get-plot/{result_id}")
        # print(response.json())
        if response.status_code == 200:
            return render_template("index.html", plot_html=response.json().get("plot_html"))
        else:
            return render_template("index.html", plot_html=None, error=f"Generation failed: {response}")
    except requests.RequestException as e:
        return render_template("index.html", plot_html=None, error=f"Error: {e}")

if __name__ == '__main__':
    app.run(debug=True)

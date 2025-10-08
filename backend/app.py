import os
from flask import Flask, request, jsonify, render_template
from .RAGAgent import RAGAgent, PDF_UPLOADS_DIR
from .SearchAgents import WebSearchAgent, ArxivSearchAgent
from .ControllerAgent import ControllerAgent

app = Flask(__name__)

# Instantiate all agents
ragAgent = RAGAgent()
webSearchAgent = WebSearchAgent()
arxivSearchAgent = ArxivSearchAgent()
controller = ControllerAgent(ragAgent, webSearchAgent, arxivSearchAgent)

@app.route('/')
def Index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def Ask():
    userQuery = request.get_json().get('query')
    if not userQuery:
        return jsonify({"error": "Query is missing"}), 400
    response = controller.RouteQuery(userQuery)
    return jsonify(response)

@app.route('/uploadPdf', methods=['POST'])
def UploadPDF():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "No selected file or not a PDF"}), 400

    filepath = os.path.join(PDF_UPLOADS_DIR, file.filename)
    file.save(filepath)
    wasSuccessful = ragAgent.ProcessPDF(filepath)

    if wasSuccessful:
        controller.SetPdfUploadTime()
        return jsonify({"message": f"File '{file.filename}' processed successfully."})
    else:
        return jsonify({"error": "Failed to process the PDF file."}), 500

@app.route('/logs', methods=['GET'])
def Logs():
    try:
        # Note: The path for Gunicorn is relative to the project root
        with open('backend/logs/controller_trace.log', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except FileNotFoundError:
        return "Log file not found.", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)


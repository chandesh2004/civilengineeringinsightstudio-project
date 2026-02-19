import os
from flask import Flask, request, jsonify
from google.cloud import vision
from google.cloud import storage
from google.cloud import aiplatform
import google.generativeai as genai

app = Flask(__name__)

vision_client = vision.ImageAnnotatorClient()
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'YOUR_GCP_PROJECT_ID')
LOCATION = 'us-central1'
BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'YOUR_BUCKET_NAME')

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def upload_to_gcs(file_stream, filename):
    """Upload image to Google Cloud Storage"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_file(file_stream)
    return f'gs://{BUCKET_NAME}/{filename}'

def detect_labels(image_uri):
    """Detect labels in image using Google Vision API"""
    image = vision.Image(source=vision.ImageSource(image_uri=image_uri))
    response = vision_client.label_detection(image=image)
    labels = []
    for label in response.label_annotations:
        labels.append({
            "description": label.description,
            "confidence": float(label.score),
        })
    return labels

def detect_text(image_uri):
    """Detect text annotations in image"""
    image = vision.Image(source=vision.ImageSource(image_uri=image_uri))
    response = vision_client.text_detection(image=image)
    texts = [text.description for text in response.text_annotations]
    return texts

def detect_objects(image_uri):
    """Detect objects with localization"""
    image = vision.Image(source=vision.ImageSource(image_uri=image_uri))
    response = vision_client.object_localization(image=image)
    objects = []
    for obj in response.localized_object_annotations:
        objects.append({
            "name": obj.name,
            "confidence": float(obj.score),
            "bounding_box": obj.bounding_poly.normalized_vertices
        })
    return objects

def generate_structural_description(scenario, detected_labels, detected_objects, detected_text):
    """Generate detailed description using Google Generative AI (Gemini)"""
    
    model = genai.GenerativeModel('gemini-pro-vision')
    
    scenario_prompts = {
        "Material Identification": """
You are a civil engineering expert. Based on the detected features, provide:
1. List of identified materials (concrete, steel, bricks, glass, etc.)
2. Estimated quantity or coverage area for each material
3. Location within the structure
4. Material quality assessment based on visual inspection
5. Any notable features or concerns

Detected features: {labels}
Detected objects: {objects}
Detected text: {text}

Provide a structured JSON response.
        """,
        "Project Documentation": """
You are a construction project manager documenting site progress. Provide:
1. Summary of construction phase
2. Completed structural elements with descriptions
3. Materials in use
4. Dimensions and measurements (if visible)
5. Construction methods observed
6. Planned next phases (if visible in documentation)
7. Any risks or concerns identified

Detected features: {labels}
Detected objects: {objects}
Detected text: {text}

Format as a professional project report.
        """,
        "Structural Analysis": """
You are a structural engineer analyzing a bridge. Provide:
1. Identification of key structural components:
   - Beams (type, material, estimated size)
   - Columns (number, material, spacing)
   - Trusses (type, configuration)
   - Cables/Supports
2. Material analysis
3. Dimensions estimation
4. Construction method analysis
5. Notable engineering features
6. Observable defects or areas of concern
7. Load path analysis (if visible)

Detected features: {labels}
Detected objects: {objects}
Detected text: {text}

Provide detailed structural analysis.
        """
    }
    
    prompt_template = scenario_prompts.get(
        scenario,
        "Analyze the image and provide detailed insights about the civil engineering structure."
    )
    
    prompt = prompt_template.format(
        labels=detected_labels,
        objects=detected_objects,
        text=detected_text
    )
    
    response = model.generate_content(prompt)
    return response.text

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/analyze', methods=['POST'])
def analyze_image():
    """Main endpoint to analyze civil engineering images"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        f = request.files['image']
        scenario = request.form.get('scenario', 'Material Identification')
        
        if f.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        filename = f'civil-eng/{scenario.replace(" ", "_")}/{f.filename}'
        gcs_uri = upload_to_gcs(f, filename)
        
        labels = detect_labels(gcs_uri)
        objects = detect_objects(gcs_uri)
        texts = detect_text(gcs_uri)
        
        description = generate_structural_description(
            scenario, labels, objects, texts
        )
        
        return jsonify({
            "success": True,
            "scenario": scenario,
            "detected_labels": labels,
            "detected_objects": objects,
            "detected_text": texts,
            "ai_analysis": description,
            "image_uri": gcs_uri
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/batch-analyze', methods=['POST'])
def batch_analyze():
    """Batch analyze multiple images from the same project"""
    try:
        files = request.files.getlist('images')
        scenario = request.form.get('scenario', 'Project Documentation')
        
        results = []
        for file in files:
            filename = f'civil-eng/batch/{file.filename}'
            gcs_uri = upload_to_gcs(file, filename)
            
            labels = detect_labels(gcs_uri)
            objects = detect_objects(gcs_uri)
            texts = detect_text(gcs_uri)
            
            description = generate_structural_description(
                scenario, labels, objects, texts
            )
            
            results.append({
                "filename": file.filename,
                "detected_labels": labels,
                "ai_analysis": description
            })
        
        return jsonify({
            "success": True,
            "scenario": scenario,
            "analyzed_images": len(results),
            "results": results
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

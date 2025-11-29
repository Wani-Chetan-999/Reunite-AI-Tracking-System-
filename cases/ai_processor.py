# cases/ai_processor.py

import os
import cv2
import numpy as np

from django.conf import settings
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import ObjectDoesNotExist

from .models import FaceEmbedding  # Import the model to fetch vectors

# InsightFace (RetinaFace + ArcFace)
from insightface.app import FaceAnalysis

# --- AI Model Initialization ---

RETINAFACE_MODEL = None  # Holds the FaceAnalysis instance
ARCFACE_MODEL = None     # Alias for RETINAFACE_MODEL

# Realistic threshold for cosine similarity of face embeddings.
MATCH_THRESHOLD = 0.70  # IMPORTANT: Using a realistic value now
VECTOR_DIMENSION = 512


def load_ai_models():
    """
    Initializes RetinaFace (detection) + ArcFace (embedding) using InsightFace.
    """
    global RETINAFACE_MODEL
    global ARCFACE_MODEL

    # Check if models are already loaded
    if RETINAFACE_MODEL is not None: 
        return

    try:
        print("AI Processor: Loading RetinaFace + ArcFace (InsightFace FaceAnalysis)...")

        # InsightFace will internally handle detection (RetinaFace) and embeddings (ArcFace).
        app = FaceAnalysis(
            name="buffalo_l",
            # Ensure the provider is correct for your environment (e.g., CUDAExecutionProvider for GPU)
            providers=["CPUExecutionProvider"],
        )
        # Prepare the model with desired detection resolution
        app.prepare(ctx_id=0, det_size=(640, 640))

        RETINAFACE_MODEL = app
        ARCFACE_MODEL = app

        print("AI Processor: Models loaded successfully.")

    except Exception as e:
        RETINAFACE_MODEL = None
        ARCFACE_MODEL = None
        print(f"AI Processor: FAILED to load models. Make sure 'insightface', 'onnxruntime', 'opencv-python' are installed: {e}")
        # Crash the application/worker if models cannot load
        raise


# Ensure models are loaded when this module is imported
load_ai_models()


# --- Internal Helper for Extraction ---

def _extract_face_data(img_bgr, model):
    """
    Internal helper to detect and extract face data using the shared model.
    Returns: (embedding_vector, bbox_normalized) or None
    """
    if model is None: return None

    # InsightFace expects BGR numpy image
    faces = model.get(img_bgr)

    if not faces:
        # print("AI Processor: No face detected in image.")
        return None, None

    # Strategy: pick the largest face (by area)
    largest_face = max(
        faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
    )

    # ArcFace embedding (already L2-normalized)
    embedding_vector = largest_face.normed_embedding

    # Bounding box in pixel coordinates [x1, y1, x2, y2]
    bbox = largest_face.bbox.astype(int) 
    x1, y1, x2, y2 = bbox.tolist()

    # Normalize bbox to [0, 1] for frontend overlay
    h, w, _ = img_bgr.shape
    box_normalized = [
        x1 / w,
        y1 / h,
        (x2 - x1) / w,  # width
        (y2 - y1) / h,  # height
    ]

    return embedding_vector, box_normalized


# --- 1. NON-BLOCKING TASK FUNCTION (Case Registration) ---

def generate_embedding_from_image(image_relative_path):
    """
    Called asynchronously by Celery. Generates 512D ArcFace embedding.
    """
    if RETINAFACE_MODEL is None:
        print("AI Processor: Models not loaded. Cannot generate embedding.")
        return None

    try:
        image_path = os.path.join(settings.MEDIA_ROOT, image_relative_path)
        image = cv2.imread(image_path)
        if image is None:
            print(f"AI Processor: Failed to read image at {image_path}")
            return None

        # Extract the vector (box is ignored for storage)
        embedding_vector, _ = _extract_face_data(image, RETINAFACE_MODEL)
        
        if embedding_vector is None:
             print("AI Processor: Failed to extract embedding (No face found).")
             return None

        print(f"AI Processor: Generated {embedding_vector.shape[0]}D embedding for storage.")
        return embedding_vector.tolist()

    except Exception as e:
        print(f"AI Processing error during case registration: {e}")
        return None


# --- 2. SYNCHRONOUS MATCHING FUNCTION (Called by Surveillance API) ---

def match_live_face_to_db(live_image_bytes):
    if RETINAFACE_MODEL is None:
        print("AI Processor: Models not loaded. Cannot perform live match.")
        return None

    try:
        np_arr = np.frombuffer(live_image_bytes, np.uint8)
        live_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if live_img is None:
            return None

        faces = RETINAFACE_MODEL.get(live_img)
        if not faces:
            return None

    except Exception as e:
        print(f"Live image processing failed: {e}")
        return None

    # DB embeddings
    database = FaceEmbedding.objects.all()
    if not database:
        return None

    matches_found = []

    for face in faces:
        embedding = face.normed_embedding.reshape(1, -1)

        bbox = face.bbox.astype(int).tolist()
        h, w, _ = live_img.shape
        normalized_box = [
            bbox[0] / w,
            bbox[1] / h,
            (bbox[2] - bbox[0]) / w,
            (bbox[3] - bbox[1]) / h,
        ]

        best_match = None
        max_similarity = -1

        for db_embed in database:
            try:
                db_vector = np.array(db_embed.embedding_vector, dtype=np.float32).reshape(1, -1)
                similarity = cosine_similarity(embedding, db_vector)[0][0]

                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = {
                        "case_id": db_embed.case.complaint_id,
                        "similarity": float(similarity),
                        "box": normalized_box,
                    }

            except Exception:
                continue

        if best_match and max_similarity >= MATCH_THRESHOLD:
            print(f"MATCH: {best_match['case_id']} similarity={max_similarity:.4f}")
            matches_found.append(best_match)

    return matches_found if matches_found else None

    """
    Performs real-time search against the database of missing persons.
    """
    if RETINAFACE_MODEL is None:
        print("AI Processor: Models not loaded. Cannot perform live match.")
        return None

    try:
        # 1. Decode bytes to OpenCV BGR image
        np_arr = np.frombuffer(live_image_bytes, np.uint8)
        live_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if live_img is None:
            return None

        # 2. Extract live embedding and box
        live_embedding_vec, box_normalized = _extract_face_data(live_img, RETINAFACE_MODEL)
        
        if live_embedding_vec is None:
            return None

        live_embedding = live_embedding_vec.reshape(1, -1)
        
    except Exception as e:
        print(f"Live image processing failed: {e}")
        return None

    
    # 3. Fetch all stored embeddings from DB
    all_embeddings = FaceEmbedding.objects.all()
    if not all_embeddings:
        print("LIVE DEBUG: No embeddings in database to compare.")
        return None

    best_match = None
    max_similarity = -1.0 

    # 4. Compare live embedding with all stored embeddings
    for db_embed in all_embeddings:
        try:
            # Note: We specify dtype=np.float32 to ensure consistency with the live vector
            db_vector = np.array(db_embed.embedding_vector, dtype=np.float32).reshape(1, -1)

            # Cosine similarity
            similarity = cosine_similarity(live_embedding, db_vector)[0][0]

            if similarity > max_similarity:
                max_similarity = similarity
                best_match = {
                    "case_id": db_embed.case.complaint_id,
                    "similarity": float(similarity),
                    "box": box_normalized,
                }

        except (ValueError, ObjectDoesNotExist, IndexError, TypeError) as e:
            # Skip corrupt vectors or invalid relations
            continue

    # 5. Apply threshold
    if best_match and max_similarity >= MATCH_THRESHOLD:
        print(
            f"LIVE MATCH FOUND: Case {best_match['case_id']} "
            f"with similarity={max_similarity:.4f} (threshold={MATCH_THRESHOLD})"
        )
        return best_match

    # print(f"LIVE DEBUG: No match above threshold. Best={max_similarity:.4f}, Threshold={MATCH_THRESHOLD}")
    return None


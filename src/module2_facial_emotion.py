# src/module2_facial_emotion.py
# ─────────────────────────────────────────────────────────────
# Module 2 — Facial Emotion Recognition
# Uses DeepFace pretrained model (no training needed)
# Run: python src/module2_facial_emotion.py --image path/to/photo.jpg
#   or: python src/module2_facial_emotion.py  (uses webcam)
# ─────────────────────────────────────────────────────────────

import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from deepface import DeepFace
from src.config import *

print('=' * 55)
print('  MODULE 2 — Facial Emotion Recognition')
print('=' * 55)


def predict_facial(image_path: str) -> dict:
    """
    Predict mood from a face image using DeepFace.
    Returns mood, confidence, all scores.
    """
    try:
        result = DeepFace.analyze(
            img_path         = image_path,
            actions          = ['emotion'],
            enforce_detection= False,
            silent           = True,
        )
        if isinstance(result, list):
            result = result[0]

        dominant = result['dominant_emotion']
        scores   = result['emotion']
        mood     = DEEPFACE_TO_MOOD.get(dominant, 'neutral')

        # Aggregate raw scores into mood categories
        mood_scores = {m: 0.0 for m in MOOD_LABELS}
        for em, sc in scores.items():
            mapped = DEEPFACE_TO_MOOD.get(em, 'neutral')
            mood_scores[mapped] += sc

        return {
            'success'         : True,
            'dominant_emotion': dominant,
            'mood_category'   : mood,
            'confidence'      : round(scores[dominant], 2),
            'all_scores'      : {k: round(v, 2) for k, v in mood_scores.items()},
            'tasks'           : TASK_RECOMMENDATIONS[mood],
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def capture_from_webcam(save_path: str) -> str:
    """Capture a photo from webcam and save it."""
    print('\n  Opening webcam... Press SPACE to capture, Q to quit.')
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print('  ❌ Could not open webcam.')
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Webcam — Press SPACE to capture', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            cv2.imwrite(save_path, frame)
            print(f'  ✅ Photo saved: {save_path}')
            break
        elif key == ord('q'):
            print('  Cancelled.')
            save_path = None
            break

    cap.release()
    cv2.destroyAllWindows()
    return save_path


def visualize_result(image_path: str, result: dict):
    """Show the photo and emotion scores side by side."""
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Facial Emotion Analysis', fontsize=14, fontweight='bold')

    # Photo
    axes[0].imshow(img)
    axes[0].axis('off')
    mood  = result['mood_category']
    color = MOOD_COLORS[mood]
    axes[0].set_title(
        f'Detected: {result["dominant_emotion"].upper()}\n'
        f'Mood: {mood.upper()} {MOOD_EMOJI[mood]}',
        fontsize=12, fontweight='bold', color=color,
    )

    # Scores
    scores  = result['all_scores']
    sorted_ = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    labels  = [s[0] for s in sorted_]
    values  = [s[1] for s in sorted_]
    colors  = [MOOD_COLORS[l] for l in labels]
    bars    = axes[1].barh(labels[::-1], values[::-1],
                           color=colors[::-1], edgecolor='white')
    for bar, val in zip(bars, values[::-1]):
        axes[1].text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                     f'{val:.1f}%', va='center', fontsize=9, fontweight='bold')
    axes[1].set_title('Mood Confidence Scores', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Score (%)')
    axes[1].grid(axis='x', alpha=0.3)

    plt.tight_layout()
    chart_path = os.path.join(CHARTS_DIR, '03_facial_result.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f'  Chart saved: {chart_path}')


def log_result(result: dict, image_path: str):
    """Append result to facial emotion log."""
    entry = pd.DataFrame([{
        'timestamp'       : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'image_path'      : image_path,
        'dominant_emotion': result.get('dominant_emotion', 'N/A'),
        'mood_category'   : result.get('mood_category', 'N/A'),
        'confidence'      : result.get('confidence', 0),
    }])
    log_path = os.path.join(LOGS_DIR, 'facial_emotion_log.csv')
    if os.path.exists(log_path):
        existing = pd.read_csv(log_path)
        entry    = pd.concat([existing, entry], ignore_index=True)
    entry.to_csv(log_path, index=False)


def save_config():
    """Save facial model config."""
    config = {
        'model'           : 'DeepFace (pretrained)',
        'emotion_to_mood' : DEEPFACE_TO_MOOD,
        'mood_labels'     : MOOD_LABELS,
        'version'         : '1.0',
        'created_at'      : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    config_path = os.path.join(MODELS_DIR, 'facial_emotion', 'facial_model_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f'  Config saved: {config_path}')


def print_result(result: dict):
    print('\n' + '=' * 50)
    print('  RESULT')
    print('=' * 50)
    print(f'  Detected Emotion : {result["dominant_emotion"].upper()}')
    print(f'  Mood Category    : {result["mood_category"].upper()} {MOOD_EMOJI[result["mood_category"]]}')
    print(f'  Confidence       : {result["confidence"]:.1f}%')
    print(f'\n  Mood Scores:')
    for m, sc in sorted(result['all_scores'].items(), key=lambda x: -x[1]):
        bar    = '█' * int(sc / 5)
        marker = ' ← dominant' if m == result['mood_category'] else ''
        print(f'    {m:12s} {sc:5.1f}%  {bar}{marker}')
    print(f'\n  Recommended Tasks:')
    for i, task in enumerate(result['tasks'], 1):
        print(f'    {i}. {task}')
    print('=' * 50)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facial Emotion Recognition')
    parser.add_argument('--image', type=str, default=None,
                        help='Path to image file. If not given, uses webcam.')
    args = parser.parse_args()

    if args.image:
        if not os.path.exists(args.image):
            print(f'❌ Image not found: {args.image}')
            sys.exit(1)
        image_path = args.image
    else:
        save_path  = os.path.join(DATA_DIR, 'facial', 'webcam_captures',
                                  f'capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
        image_path = capture_from_webcam(save_path)
        if not image_path:
            sys.exit(0)

    print(f'\n  Analyzing: {image_path}')
    result = predict_facial(image_path)

    if result['success']:
        print_result(result)
        log_result(result, image_path)
        visualize_result(image_path, result)
        save_config()
        print('\n✅ Module 2 complete!')
    else:
        print(f'❌ Error: {result["error"]}')

# src/config.py
# ─────────────────────────────────────────────────────────────
# Shared config for all modules
# ─────────────────────────────────────────────────────────────

import os

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, 'data')
MODELS_DIR   = os.path.join(BASE_DIR, 'models')
LOGS_DIR     = os.path.join(BASE_DIR, 'logs')
OUTPUTS_DIR  = os.path.join(BASE_DIR, 'outputs')
CHARTS_DIR   = os.path.join(BASE_DIR, 'eda', 'charts')

TEXT_MODEL_PATH   = os.path.join(MODELS_DIR, 'text_emotion', 'best_model')
FACIAL_CONFIG     = os.path.join(MODELS_DIR, 'facial_emotion', 'facial_model_config.json')
SPEECH_CONFIG     = os.path.join(MODELS_DIR, 'speech_emotion', 'speech_model_config.json')
FUSION_CONFIG     = os.path.join(MODELS_DIR, 'fusion', 'fusion_config.json')
EMPLOYEE_CSV      = os.path.join(DATA_DIR, 'employees.csv')
MOOD_LOG_CSV      = os.path.join(LOGS_DIR, 'mood_history_log.csv')

# ── Mood labels ────────────────────────────────────────────────
MOOD_LABELS = ['positive', 'negative', 'neutral', 'energetic', 'stressed', 'focused']

MOOD_EMOJI = {
    'positive' : '😊',
    'negative' : '😔',
    'neutral'  : '😐',
    'energetic': '⚡',
    'stressed' : '😰',
    'focused'  : '🎯',
}

MOOD_COLORS = {
    'positive' : '#4CAF50',
    'negative' : '#F44336',
    'neutral'  : '#9E9E9E',
    'energetic': '#FF9800',
    'stressed' : '#E91E63',
    'focused'  : '#2196F3',
}

TASK_RECOMMENDATIONS = {
    'positive' : ['Lead a team meeting', 'Work on creative tasks', 'Mentor a colleague', 'Brainstorm new ideas'],
    'negative' : ['Take a short break', 'Do simple admin tasks', 'Review documents', 'Reach out to HR if needed'],
    'neutral'  : ['Handle routine tasks', 'Reply to emails', 'Update project tracker', 'Attend scheduled meetings'],
    'energetic': ['Tackle challenging problems', 'Start a new project', 'Deep-focus coding', 'Run a workshop'],
    'stressed' : ['Take a 10-min break', 'Do breathing exercises', 'Low-priority tasks only', 'Talk to your manager'],
    'focused'  : ['Write documentation', 'Code review', 'Data analysis', 'Research tasks'],
}

# ── Emotion → Mood mappings ────────────────────────────────────
DEEPFACE_TO_MOOD = {
    'happy'   : 'positive',
    'surprise': 'energetic',
    'neutral' : 'neutral',
    'sad'     : 'negative',
    'angry'   : 'negative',
    'disgust' : 'negative',
    'fear'    : 'stressed',
}

SPEECH_TO_MOOD = {
    'calm'     : 'neutral',
    'happy'    : 'positive',
    'sad'      : 'negative',
    'angry'    : 'negative',
    'fearful'  : 'stressed',
    'disgust'  : 'negative',
    'surprised': 'energetic',
    'neutral'  : 'neutral',
    'fear'     : 'stressed',
    'surprise' : 'energetic',
    'joy'      : 'positive',
    'excited'  : 'energetic',
    'boredom'  : 'neutral',
}

# ── Model names ────────────────────────────────────────────────
SPEECH_MODEL_NAME = 'ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition'
TEXT_BASE_MODEL   = 'distilbert-base-uncased'

# ── Fusion weights ─────────────────────────────────────────────
BASE_WEIGHTS = {
    'text'  : 0.40,
    'facial': 0.35,
    'speech': 0.25,
}

# ── Audio ──────────────────────────────────────────────────────
TARGET_SR = 16000

# ── Training ───────────────────────────────────────────────────
TRAIN_EPOCHS    = 4
TRAIN_BATCH     = 8
LEARNING_RATE   = 2e-5
MAX_SEQ_LEN     = 64

# ── API ────────────────────────────────────────────────────────
API_HOST = '0.0.0.0'
API_PORT = 8000

# ── Burnout ────────────────────────────────────────────────────
STRESS_MOODS      = ['stressed', 'negative']
BURNOUT_THRESHOLD = 3

# ── Create dirs on import ──────────────────────────────────────
for d in [DATA_DIR, MODELS_DIR, LOGS_DIR, OUTPUTS_DIR, CHARTS_DIR,
          TEXT_MODEL_PATH, os.path.join(MODELS_DIR, 'facial_emotion'),
          os.path.join(MODELS_DIR, 'speech_emotion'),
          os.path.join(MODELS_DIR, 'fusion'),
          os.path.join(DATA_DIR, 'speech', 'recordings'),
          os.path.join(DATA_DIR, 'facial', 'webcam_captures'),
          os.path.join(DATA_DIR, 'processed')]:
    os.makedirs(d, exist_ok=True)

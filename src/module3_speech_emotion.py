# src/module3_speech_emotion.py
# ─────────────────────────────────────────────────────────────
# Module 3 — Speech Emotion Recognition
# Uses wav2vec2 pretrained model (no training needed)
# Run: python src/module3_speech_emotion.py --audio path/to/audio.wav
#   or: python src/module3_speech_emotion.py  (records from mic)
# ─────────────────────────────────────────────────────────────

import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
import pandas as pd
import librosa
import matplotlib.pyplot as plt
import sounddevice as sd
import soundfile as sf
from datetime import datetime
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
from src.config import *

print('=' * 55)
print('  MODULE 3 — Speech Emotion Recognition')
print('=' * 55)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'  Device : {DEVICE}')


# ── Load model (once) ──────────────────────────────────────────
print(f'  Loading model: {SPEECH_MODEL_NAME}')
feature_extractor = AutoFeatureExtractor.from_pretrained(SPEECH_MODEL_NAME)
speech_model      = AutoModelForAudioClassification.from_pretrained(SPEECH_MODEL_NAME).to(DEVICE)
speech_model.eval()
print('  ✅ Model loaded!\n')


def predict_speech(audio_path: str) -> dict:
    """
    Predict mood from a WAV audio file using wav2vec2.
    """
    try:
        audio_input, _ = librosa.load(audio_path, sr=TARGET_SR)
        inputs = feature_extractor(
            audio_input,
            sampling_rate=TARGET_SR,
            return_tensors='pt',
            padding=True,
        )
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

        with torch.no_grad():
            logits = speech_model(**inputs).logits

        probs      = torch.softmax(logits, dim=-1)[0].cpu().numpy()
        id2label   = speech_model.config.id2label
        top_idx    = np.argmax(probs)
        dominant   = id2label[top_idx].lower()
        mood       = SPEECH_TO_MOOD.get(dominant, 'neutral')

        # Aggregate into mood scores
        mood_scores = {m: 0.0 for m in MOOD_LABELS}
        for i, prob in enumerate(probs):
            em     = id2label[i].lower()
            mapped = SPEECH_TO_MOOD.get(em, 'neutral')
            mood_scores[mapped] += float(prob) * 100

        all_emotion_scores = {
            id2label[i].lower(): round(float(probs[i]) * 100, 2)
            for i in range(len(probs))
        }

        return {
            'success'          : True,
            'dominant_emotion' : dominant,
            'mood_category'    : mood,
            'confidence'       : round(float(probs[top_idx]) * 100, 2),
            'all_scores'       : {k: round(v, 2) for k, v in mood_scores.items()},
            'emotion_scores'   : all_emotion_scores,
            'tasks'            : TASK_RECOMMENDATIONS[mood],
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def record_from_mic(duration: int = 5, save_path: str = None) -> str:
    """Record audio from microphone and save as WAV."""
    if save_path is None:
        save_path = os.path.join(
            DATA_DIR, 'speech', 'recordings',
            f'recording_{datetime.now().strftime("%Y%m%d_%H%M%S")}.wav'
        )
    print(f'\n  🎙️  Recording for {duration} seconds...')
    print('  Speak clearly about how you are feeling!\n')

    for i in range(3, 0, -1):
        print(f'  Starting in {i}...', end='\r')
        import time; time.sleep(1)

    print('  🔴 Recording NOW...')
    audio = sd.rec(int(duration * TARGET_SR), samplerate=TARGET_SR,
                   channels=1, dtype='float32')
    sd.wait()
    audio = audio.flatten()
    sf.write(save_path, audio, TARGET_SR)
    print(f'  ✅ Saved: {save_path}')
    return save_path


def visualize_result(audio_path: str, result: dict):
    """Visualize waveform and emotion scores."""
    audio, sr = librosa.load(audio_path, sr=TARGET_SR)
    t         = np.linspace(0, len(audio)/sr, len(audio))
    mood      = result['mood_category']
    color     = MOOD_COLORS[mood]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle('Speech Emotion Analysis', fontsize=14, fontweight='bold')

    # Waveform
    axes[0].plot(t, audio, color=color, linewidth=0.5, alpha=0.85)
    axes[0].fill_between(t, audio, alpha=0.15, color=color)
    axes[0].set_title(
        f'Voice Waveform\n{result["dominant_emotion"].upper()} → {mood.upper()} {MOOD_EMOJI[mood]}',
        fontsize=11, fontweight='bold', color=color,
    )
    axes[0].set_xlabel('Time (s)')
    axes[0].set_ylabel('Amplitude')
    axes[0].grid(alpha=0.3)

    # Scores
    scores  = result['all_scores']
    sorted_ = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    labels  = [s[0] for s in sorted_]
    values  = [s[1] for s in sorted_]
    colors  = [MOOD_COLORS[l] for l in labels]
    axes[1].barh(labels[::-1], values[::-1], color=colors[::-1], edgecolor='white')
    for i, (l, v) in enumerate(zip(labels[::-1], values[::-1])):
        axes[1].text(v + 0.3, i, f'{v:.1f}%', va='center', fontsize=9)
    axes[1].set_title('Mood Confidence Scores', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Score (%)')
    axes[1].set_xlim(0, max(values) * 1.2)
    axes[1].grid(axis='x', alpha=0.3)

    plt.tight_layout()
    chart_path = os.path.join(CHARTS_DIR, '05_speech_result.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f'  Chart saved: {chart_path}')


def log_result(result: dict, audio_path: str):
    entry = pd.DataFrame([{
        'timestamp'       : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'audio_path'      : audio_path,
        'dominant_emotion': result.get('dominant_emotion', 'N/A'),
        'mood_category'   : result.get('mood_category', 'N/A'),
        'confidence'      : result.get('confidence', 0),
    }])
    log_path = os.path.join(LOGS_DIR, 'speech_emotion_log.csv')
    if os.path.exists(log_path):
        existing = pd.read_csv(log_path)
        entry    = pd.concat([existing, entry], ignore_index=True)
    entry.to_csv(log_path, index=False)


def save_config():
    config = {
        'model'          : SPEECH_MODEL_NAME,
        'sample_rate'    : TARGET_SR,
        'emotion_to_mood': SPEECH_TO_MOOD,
        'mood_labels'    : MOOD_LABELS,
        'version'        : '1.0',
        'created_at'     : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    config_path = os.path.join(MODELS_DIR, 'speech_emotion', 'speech_model_config.json')
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
    parser = argparse.ArgumentParser(description='Speech Emotion Recognition')
    parser.add_argument('--audio',    type=str, default=None,
                        help='Path to WAV audio file. If not given, records from mic.')
    parser.add_argument('--duration', type=int, default=5,
                        help='Recording duration in seconds (default: 5)')
    args = parser.parse_args()

    if args.audio:
        if not os.path.exists(args.audio):
            print(f'❌ Audio file not found: {args.audio}')
            sys.exit(1)
        audio_path = args.audio
    else:
        audio_path = record_from_mic(duration=args.duration)

    print(f'\n  Analyzing: {audio_path}')
    result = predict_speech(audio_path)

    if result['success']:
        print_result(result)
        log_result(result, audio_path)
        visualize_result(audio_path, result)
        save_config()
        print('\n✅ Module 3 complete!')
    else:
        print(f'❌ Error: {result["error"]}')

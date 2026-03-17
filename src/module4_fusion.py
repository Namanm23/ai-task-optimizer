# src/module4_fusion.py
# ─────────────────────────────────────────────────────────────
# Module 4 — Fusion Model
# Combines text + facial + speech predictions
# Run: python src/module4_fusion.py
# ─────────────────────────────────────────────────────────────

import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from transformers import pipeline
from src.config import *
from src.module2_facial_emotion import predict_facial
from src.module3_speech_emotion import predict_speech, feature_extractor, speech_model

print('=' * 55)
print('  MODULE 4 — Fusion Model')
print('=' * 55)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# ── Load text model ────────────────────────────────────────────
print('  Loading Text Model...')
if not os.path.exists(os.path.join(TEXT_MODEL_PATH, 'config.json')):
    print(f'  ❌ Text model not found at {TEXT_MODEL_PATH}')
    print('     Run Module 1 first: python src/module1_text_emotion.py')
    sys.exit(1)

text_classifier = pipeline(
    'text-classification',
    model     = TEXT_MODEL_PATH,
    tokenizer = TEXT_MODEL_PATH,
    device    = 0 if torch.cuda.is_available() else -1,
    top_k     = None,
)
print('  ✅ All models ready!\n')


# ── Individual predictors ──────────────────────────────────────

def predict_text(text: str) -> dict:
    try:
        results  = text_classifier(text)
        if isinstance(results[0], list):
            results = results[0]
        scores   = {r['label']: r['score'] for r in results}
        dominant = max(scores, key=scores.get)
        return {
            'success'   : True,
            'mood'      : dominant,
            'confidence': round(scores[dominant] * 100, 2),
            'all_scores': {k: round(v * 100, 2) for k, v in scores.items()},
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ── Fusion ─────────────────────────────────────────────────────

def fuse(text_res: dict, facial_res: dict, speech_res: dict,
         employee_id: str = 'anonymous') -> dict:
    """
    Weighted late fusion of all 3 models.
    Gracefully handles missing modalities.
    """
    available = {}
    if text_res.get('success'):   available['text']   = text_res
    if facial_res.get('success'): available['facial'] = facial_res
    if speech_res.get('success'): available['speech'] = speech_res

    if not available:
        return {'success': False, 'error': 'All models failed'}

    # Normalize weights
    total_w = sum(BASE_WEIGHTS[m] for m in available)
    norm_w  = {m: BASE_WEIGHTS[m] / total_w for m in available}

    # Weighted sum
    fused = {mood: 0.0 for mood in MOOD_LABELS}
    for modality, res in available.items():
        for mood in MOOD_LABELS:
            fused[mood] += norm_w[modality] * res['all_scores'].get(mood, 0.0)

    final_mood = max(fused, key=fused.get)

    return {
        'success'        : True,
        'employee_id'    : employee_id,
        'final_mood'     : final_mood,
        'emoji'          : MOOD_EMOJI[final_mood],
        'confidence'     : round(fused[final_mood], 2),
        'fused_scores'   : {k: round(v, 2) for k, v in fused.items()},
        'modalities_used': list(available.keys()),
        'weights_used'   : norm_w,
        'individual'     : {
            'text'  : text_res.get('mood', 'N/A'),
            'facial': facial_res.get('mood', 'N/A'),
            'speech': speech_res.get('mood', 'N/A'),
        },
        'tasks'          : TASK_RECOMMENDATIONS[final_mood],
        'timestamp'      : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def check_burnout(employee_id: str, current_mood: str) -> str:
    if not os.path.exists(MOOD_LOG_CSV):
        return 'none'
    df = pd.read_csv(MOOD_LOG_CSV)
    if 'employee_id' not in df.columns:
        return 'none'
    emp_log = df[df['employee_id'] == employee_id]['final_mood'].tolist()
    emp_log.append(current_mood)
    consec = 0
    for m in reversed(emp_log):
        if m in STRESS_MOODS: consec += 1
        else: break
    if consec >= BURNOUT_THRESHOLD: return 'high'
    elif consec == 2:               return 'medium'
    elif consec == 1:               return 'low'
    return 'none'


def log_fusion(fusion: dict, text_input: str = ''):
    entry = pd.DataFrame([{
        'employee_id' : fusion['employee_id'],
        'timestamp'   : fusion['timestamp'],
        'final_mood'  : fusion['final_mood'],
        'confidence'  : fusion['confidence'],
        'text_mood'   : fusion['individual']['text'],
        'facial_mood' : fusion['individual']['facial'],
        'speech_mood' : fusion['individual']['speech'],
        'text_input'  : text_input[:100],
    }])
    if os.path.exists(MOOD_LOG_CSV):
        existing = pd.read_csv(MOOD_LOG_CSV)
        entry    = pd.concat([existing, entry], ignore_index=True)
    entry.to_csv(MOOD_LOG_CSV, index=False)


def visualize_fusion(fusion: dict, text_res, facial_res, speech_res):
    mood  = fusion['final_mood']
    color = MOOD_COLORS[mood]

    fig = plt.figure(figsize=(16, 9))
    fig.suptitle(
        f'Fusion Result — {mood.upper()} {MOOD_EMOJI[mood]}',
        fontsize=15, fontweight='bold', color=color,
    )

    model_results = [
        ('Text',   text_res,   '📝'),
        ('Facial', facial_res, '📸'),
        ('Speech', speech_res, '🎙️'),
    ]

    for idx, (name, res, icon) in enumerate(model_results):
        ax = fig.add_subplot(2, 3, idx + 1)
        if res.get('success'):
            mood_sc   = {m: res['all_scores'].get(m, 0.0) for m in MOOD_LABELS}
            sorted_sc = sorted(mood_sc.items(), key=lambda x: x[1], reverse=True)
            labels    = [s[0] for s in sorted_sc]
            values    = [s[1] for s in sorted_sc]
            colors_   = [MOOD_COLORS[l] for l in labels]
            ax.barh(labels[::-1], values[::-1], color=colors_[::-1], edgecolor='white')
            ax.set_title(f'{icon} {name}\n→ {res["mood"].upper()}',
                         fontsize=11, fontweight='bold',
                         color=MOOD_COLORS.get(res.get('mood', 'neutral'), '#888'))
            ax.set_xlabel('Score (%)')
            ax.grid(axis='x', alpha=0.3)
        else:
            ax.text(0.5, 0.5, f'{icon} {name}\nUnavailable',
                    ha='center', va='center', fontsize=11, color='gray',
                    transform=ax.transAxes)

    # Fused scores
    ax4 = fig.add_subplot(2, 3, 4)
    fsc     = fusion['fused_scores']
    sorted_ = sorted(fsc.items(), key=lambda x: x[1], reverse=True)
    fl      = [s[0] for s in sorted_]
    fv      = [s[1] for s in sorted_]
    fc      = [MOOD_COLORS[l] for l in fl]
    bars    = ax4.bar(fl, fv, color=fc, edgecolor='white')
    for bar, val in zip(bars, fv):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 f'{val:.1f}%', ha='center', fontsize=9, fontweight='bold')
    ax4.set_title('🔀 Fused Mood Scores', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Score (%)')
    ax4.tick_params(axis='x', rotation=30)
    ax4.grid(axis='y', alpha=0.3)

    # Weights pie
    ax5 = fig.add_subplot(2, 3, 5)
    wts     = fusion['weights_used']
    wlabels = [f'{k}\n({v*100:.0f}%)' for k, v in wts.items()]
    wcolors = ['#2196F3', '#4CAF50', '#FF9800'][:len(wts)]
    ax5.pie(list(wts.values()), labels=wlabels, colors=wcolors,
            autopct='%1.0f%%', startangle=90, textprops={'fontsize': 10})
    ax5.set_title('⚖️ Weights', fontsize=11, fontweight='bold')

    # Tasks
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')
    task_text = f'Final Mood: {mood.upper()} {MOOD_EMOJI[mood]}\n\nTasks:\n\n'
    for i, t in enumerate(fusion['tasks'], 1):
        task_text += f'{i}. {t}\n'
    ax6.text(0.05, 0.95, task_text, transform=ax6.transAxes,
             fontsize=11, va='top', ha='left',
             bbox=dict(boxstyle='round', facecolor=MOOD_COLORS[mood], alpha=0.12))
    ax6.set_title('✅ Recommendations', fontsize=11, fontweight='bold')

    plt.tight_layout()
    chart_path = os.path.join(CHARTS_DIR, '07_fusion_result.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f'  Chart saved: {chart_path}')


def print_result(fusion: dict):
    mood = fusion['final_mood']
    print('\n' + '=' * 55)
    print('  FUSION RESULT')
    print('=' * 55)
    print(f'  Individual:')
    print(f'    Text    → {fusion["individual"]["text"].upper()}')
    print(f'    Facial  → {fusion["individual"]["facial"].upper()}')
    print(f'    Speech  → {fusion["individual"]["speech"].upper()}')
    print(f'\n  ► FINAL MOOD : {mood.upper()} {MOOD_EMOJI[mood]}')
    print(f'  ► Confidence : {fusion["confidence"]:.1f}%')
    print(f'\n  Fused Scores:')
    for m, sc in sorted(fusion['fused_scores'].items(), key=lambda x: -x[1]):
        bar    = '█' * int(sc / 3)
        marker = ' ◄' if m == mood else ''
        print(f'    {m:12s} {sc:5.1f}%  {bar}{marker}')
    print(f'\n  Tasks for {mood.upper()}:')
    for i, task in enumerate(fusion['tasks'], 1):
        print(f'    {i}. {task}')
    print('=' * 55)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fusion Model')
    parser.add_argument('--text',   type=str, default=None, help='Text input')
    parser.add_argument('--image',  type=str, default=None, help='Image file path')
    parser.add_argument('--audio',  type=str, default=None, help='Audio file path')
    parser.add_argument('--emp_id', type=str, default='anonymous', help='Employee ID')
    args = parser.parse_args()

    # Get text
    text = args.text or input('\n📝 How are you feeling today?\n> ')

    # Run models
    print('\n  Running models...')
    text_res   = predict_text(text)
    facial_res = predict_facial(args.image) if args.image else {'success': False, 'error': 'Not provided'}
    speech_res = predict_speech(args.audio) if args.audio else {'success': False, 'error': 'Not provided'}

    t = '✅' if text_res.get('success')   else '❌'
    f = '✅' if facial_res.get('success') else '❌'
    s = '✅' if speech_res.get('success') else '❌'
    print(f'  {t} Text   : {text_res.get("mood","N/A")}')
    print(f'  {f} Facial : {facial_res.get("mood","N/A")}')
    print(f'  {s} Speech : {speech_res.get("mood","N/A")}')

    fusion = fuse(text_res, facial_res, speech_res, args.emp_id)

    if fusion['success']:
        print_result(fusion)
        log_fusion(fusion, text)
        visualize_fusion(fusion, text_res, facial_res, speech_res)

        alert = check_burnout(args.emp_id, fusion['final_mood'])
        if alert != 'none':
            print(f'\n  🚨 Burnout Alert: {alert.upper()} risk for {args.emp_id}')

        # Save config
        config = {
            'fusion_strategy': 'weighted_late_fusion',
            'base_weights'   : BASE_WEIGHTS,
            'mood_labels'    : MOOD_LABELS,
            'version'        : '1.0',
            'created_at'     : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        config_path = os.path.join(MODELS_DIR, 'fusion', 'fusion_config.json')
        with open(config_path, 'w') as f_:
            json.dump(config, f_, indent=2)

        print('\n✅ Module 4 complete!')
    else:
        print(f'\n❌ Fusion failed: {fusion["error"]}')

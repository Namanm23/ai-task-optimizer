# src/module5_api.py
# ─────────────────────────────────────────────────────────────
# Module 5 — FastAPI Backend
# Run: python src/module5_api.py
# API docs: http://localhost:8000/docs
# ─────────────────────────────────────────────────────────────

import os, sys, json, tempfile
from fastapi.responses import FileResponse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
import pandas as pd
import librosa
from datetime import datetime
from typing import Optional
from deepface import DeepFace
from transformers import (
    pipeline,
    AutoFeatureExtractor,
    AutoModelForAudioClassification,
)
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from src.config import *
from src.module4_fusion import (
    predict_text, fuse, check_burnout, log_fusion,
    text_classifier,
)
from src.module2_facial_emotion import predict_facial
from src.module3_speech_emotion import predict_speech

# ── FastAPI app ────────────────────────────────────────────────
app = FastAPI(
    title       = 'AI-Powered Task Optimizer API',
    description = 'Detects employee mood from text, facial, and speech inputs.',
    version     = '1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ['*'],
    allow_credentials = True,
    allow_methods     = ['*'],
    allow_headers     = ['*'],
)

# Serve frontend dashboard
DASHBOARD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'outputs')
if os.path.exists(DASHBOARD_PATH):
    app.mount('/static', StaticFiles(directory=DASHBOARD_PATH), name='static')


# ── Employee helpers ───────────────────────────────────────────

EMPLOYEE_COLUMNS = ['employee_id', 'name', 'email', 'department', 'role', 'joined_date']

def load_employees() -> pd.DataFrame:
    if os.path.exists(EMPLOYEE_CSV):
        return pd.read_csv(EMPLOYEE_CSV)
    return pd.DataFrame(columns=EMPLOYEE_COLUMNS)

def save_employees(df: pd.DataFrame):
    os.makedirs(os.path.dirname(EMPLOYEE_CSV), exist_ok=True)
    df.to_csv(EMPLOYEE_CSV, index=False)

def get_employee(employee_id: str) -> Optional[dict]:
    df  = load_employees()
    if df.empty or 'employee_id' not in df.columns:
        return None
    row = df[df['employee_id'] == employee_id]
    return row.iloc[0].to_dict() if not row.empty else None

def seed_employees():
    if os.path.exists(EMPLOYEE_CSV):
        return
    sample = pd.DataFrame([
        {'employee_id':'EMP001','name':'Arjun Sharma',  'email':'arjun@company.com',  'department':'Engineering',  'role':'Senior Developer', 'joined_date':'2022-03-15'},
        {'employee_id':'EMP002','name':'Priya Mehta',   'email':'priya@company.com',   'department':'Design',       'role':'UI/UX Designer',   'joined_date':'2021-07-01'},
        {'employee_id':'EMP003','name':'Rohan Verma',   'email':'rohan@company.com',   'department':'Engineering',  'role':'Junior Developer', 'joined_date':'2023-01-10'},
        {'employee_id':'EMP004','name':'Sneha Kapoor',  'email':'sneha@company.com',   'department':'HR',           'role':'HR Manager',       'joined_date':'2020-05-20'},
        {'employee_id':'EMP005','name':'Vikram Singh',  'email':'vikram@company.com',  'department':'Sales',        'role':'Sales Executive',  'joined_date':'2023-06-01'},
        {'employee_id':'EMP006','name':'Ananya Gupta',  'email':'ananya@company.com',  'department':'Data Science', 'role':'Data Analyst',     'joined_date':'2022-11-15'},
    ])
    save_employees(sample)
    print(f'✅ Sample employees seeded ({len(sample)} records)')

seed_employees()


# ── Mood log helpers ───────────────────────────────────────────

def log_mood(employee_id, mood, confidence, text_mood, facial_mood, speech_mood):
    emp     = get_employee(employee_id)
    new_row = pd.DataFrame([{
        'employee_id' : employee_id,
        'name'        : emp['name']       if emp else 'Unknown',
        'department'  : emp['department'] if emp else 'Unknown',
        'role'        : emp['role']       if emp else 'Unknown',
        'timestamp'   : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'final_mood'  : mood,
        'confidence'  : confidence,
        'text_mood'   : text_mood,
        'facial_mood' : facial_mood,
        'speech_mood' : speech_mood,
    }])
    if os.path.exists(MOOD_LOG_CSV):
        existing = pd.read_csv(MOOD_LOG_CSV)
        new_row  = pd.concat([existing, new_row], ignore_index=True)
    new_row.to_csv(MOOD_LOG_CSV, index=False)


def run_fusion_full(text_res, facial_res, speech_res, employee_id):
    available = {}
    if text_res.get('success'):   available['text']   = text_res
    if facial_res.get('success'): available['facial'] = facial_res
    if speech_res.get('success'): available['speech'] = speech_res
    if not available:
        return {'success': False, 'error': 'All models failed'}

    total_w = sum(BASE_WEIGHTS[m] for m in available)
    norm_w  = {m: BASE_WEIGHTS[m] / total_w for m in available}
    fused   = {mood: 0.0 for mood in MOOD_LABELS}
    for modality, res in available.items():
        for mood in MOOD_LABELS:
            fused[mood] += norm_w[modality] * res['all_scores'].get(mood, 0.0)

    final_mood  = max(fused, key=fused.get)
    alert_level = check_burnout(employee_id, final_mood)
    emp         = get_employee(employee_id)

    log_mood(employee_id, final_mood, round(fused[final_mood], 2),
             text_res.get('mood','N/A'),
             facial_res.get('mood','N/A'),
             speech_res.get('mood','N/A'))

    return {
        'success'        : True,
        'employee_id'    : employee_id,
        'employee_name'  : emp['name']       if emp else 'Unknown',
        'department'     : emp['department'] if emp else 'Unknown',
        'role'           : emp['role']       if emp else 'Unknown',
        'final_mood'     : final_mood,
        'emoji'          : MOOD_EMOJI[final_mood],
        'confidence'     : round(fused[final_mood], 2),
        'fused_scores'   : {k: round(v, 2) for k, v in fused.items()},
        'modalities_used': list(available.keys()),
        'individual'     : {
            'text'  : text_res.get('mood', 'N/A'),
            'facial': facial_res.get('mood', 'N/A'),
            'speech': speech_res.get('mood', 'N/A'),
        },
        'tasks'          : TASK_RECOMMENDATIONS[final_mood],
        'alert_level'    : alert_level,
        'timestamp'      : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get('/')
def root():
    path = os.path.join(BASE_DIR, 'outputs', 'dashboard.html')
    if os.path.exists(path):
        return FileResponse(path)
    return {'message': 'AI-Powered Task Optimizer API 🚀', 'docs': '/docs'}

@app.get('/dashboard')
def dashboard():
    path = os.path.join(BASE_DIR, 'outputs', 'dashboard.html')
    if os.path.exists(path):
        return FileResponse(path)
    return {'message': 'Dashboard not found'}

@app.get('/health')
def health():
    df = load_employees()
    return {
        'status'         : 'healthy',
        'models'         : {'text':'loaded','facial':'loaded','speech':'loaded'},
        'total_employees': len(df),
        'timestamp'      : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

# ── Employee endpoints ─────────────────────────────────────────

@app.get('/employees')
def get_all_employees():
    df = load_employees()
    return {'employees': df.to_dict('records'), 'total': len(df)}

@app.get('/employees/{employee_id}')
def get_one_employee(employee_id: str):
    emp = get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f'Employee {employee_id} not found')
    return emp

@app.post('/employees')
def add_employee(
    name       : str = Form(...),
    email      : str = Form(...),
    department : str = Form(...),
    role       : str = Form(...),
):
    df = load_employees()
    if not df.empty and email in df['email'].values:
        raise HTTPException(status_code=400, detail=f'Email {email} already exists')
    if df.empty:
        new_id = 'EMP001'
    else:
        existing_nums = df['employee_id'].str.replace('EMP','').astype(int)
        new_id        = f'EMP{str(existing_nums.max() + 1).zfill(3)}'
    new_row = pd.DataFrame([{
        'employee_id': new_id, 'name': name, 'email': email,
        'department': department, 'role': role,
        'joined_date': datetime.now().strftime('%Y-%m-%d'),
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_employees(df)
    return {'message': f'Employee {name} added!', 'employee_id': new_id}

@app.put('/employees/{employee_id}')
def update_employee(
    employee_id: str,
    name       : Optional[str] = Form(default=None),
    email      : Optional[str] = Form(default=None),
    department : Optional[str] = Form(default=None),
    role       : Optional[str] = Form(default=None),
):
    df = load_employees()
    if df.empty or employee_id not in df['employee_id'].values:
        raise HTTPException(status_code=404, detail=f'Employee {employee_id} not found')
    idx = df[df['employee_id'] == employee_id].index[0]
    if name:       df.at[idx, 'name']       = name
    if email:      df.at[idx, 'email']      = email
    if department: df.at[idx, 'department'] = department
    if role:       df.at[idx, 'role']       = role
    save_employees(df)
    return {'message': f'Employee {employee_id} updated!', 'employee': df.iloc[idx].to_dict()}

@app.delete('/employees/{employee_id}')
def delete_employee(employee_id: str):
    df = load_employees()
    if df.empty or employee_id not in df['employee_id'].values:
        raise HTTPException(status_code=404, detail=f'Employee {employee_id} not found')
    name = df[df['employee_id'] == employee_id].iloc[0]['name']
    df   = df[df['employee_id'] != employee_id].reset_index(drop=True)
    save_employees(df)
    return {'message': f'Employee {name} deleted!'}

# ── Analysis endpoints ─────────────────────────────────────────

@app.post('/analyze/text')
async def analyze_text(text: str = Form(...), employee_id: str = Form(default='anonymous')):
    if not text.strip():
        raise HTTPException(status_code=400, detail='Text cannot be empty')
    result = predict_text(text)
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    emp = get_employee(employee_id)
    return {
        'employee_id'  : employee_id,
        'employee_name': emp['name']       if emp else 'Unknown',
        'department'   : emp['department'] if emp else 'Unknown',
        'modality'     : 'text',
        'mood'         : result['mood'],
        'emoji'        : MOOD_EMOJI[result['mood']],
        'confidence'   : result['confidence'],
        'all_scores'   : result['all_scores'],
        'tasks'        : TASK_RECOMMENDATIONS[result['mood']],
        'timestamp'    : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

@app.post('/analyze/facial')
async def analyze_facial(image: UploadFile = File(...), employee_id: str = Form(default='anonymous')):
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp.write(await image.read())
        tmp_path = tmp.name
    result = predict_facial(tmp_path)
    os.unlink(tmp_path)
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    emp = get_employee(employee_id)
    return {
        'employee_id'  : employee_id,
        'employee_name': emp['name']       if emp else 'Unknown',
        'department'   : emp['department'] if emp else 'Unknown',
        'modality'     : 'facial',
        'mood'         : result['mood_category'],
        'emoji'        : MOOD_EMOJI[result['mood_category']],
        'confidence'   : result['confidence'],
        'all_scores'   : result['all_scores'],
        'tasks'        : TASK_RECOMMENDATIONS[result['mood_category']],
        'timestamp'    : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

@app.post('/analyze/speech')
async def analyze_speech(audio: UploadFile = File(...), employee_id: str = Form(default='anonymous')):
    suffix = os.path.splitext(audio.filename)[-1] or '.wav'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name
    wav_path = tmp_path.replace(suffix, '.wav')
    os.system(f'ffmpeg -y -i "{tmp_path}" -ar 16000 -ac 1 "{wav_path}" -loglevel quiet')
    result = predict_speech(wav_path if os.path.exists(wav_path) else tmp_path)
    os.unlink(tmp_path)
    if os.path.exists(wav_path): os.unlink(wav_path)
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    emp = get_employee(employee_id)
    return {
        'employee_id'  : employee_id,
        'employee_name': emp['name']       if emp else 'Unknown',
        'department'   : emp['department'] if emp else 'Unknown',
        'modality'     : 'speech',
        'mood'         : result['mood_category'],
        'emoji'        : MOOD_EMOJI[result['mood_category']],
        'confidence'   : result['confidence'],
        'all_scores'   : result['all_scores'],
        'tasks'        : TASK_RECOMMENDATIONS[result['mood_category']],
        'timestamp'    : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

@app.post('/analyze')
async def analyze_all(
    employee_id : str                  = Form(default='anonymous'),
    text        : Optional[str]        = Form(default=None),
    image       : Optional[UploadFile] = File(default=None),
    audio       : Optional[UploadFile] = File(default=None),
):
    if not text and not image and not audio:
        raise HTTPException(status_code=400, detail='At least one input required')

    text_res   = {'success': False, 'error': 'Not provided'}
    facial_res = {'success': False, 'error': 'Not provided'}
    speech_res = {'success': False, 'error': 'Not provided'}

    if text and text.strip():
        text_res = predict_text(text)

    if image:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(await image.read())
            img_path = tmp.name
        facial_res = predict_facial(img_path)
        os.unlink(img_path)

    if audio:
        suffix = os.path.splitext(audio.filename)[-1] or '.wav'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await audio.read())
            aud_path = tmp.name
        wav_path = aud_path.replace(suffix, '_c.wav')
        os.system(f'ffmpeg -y -i "{aud_path}" -ar 16000 -ac 1 "{wav_path}" -loglevel quiet')
        speech_res = predict_speech(wav_path if os.path.exists(wav_path) else aud_path)
        os.unlink(aud_path)
        if os.path.exists(wav_path): os.unlink(wav_path)

    fusion = run_fusion_full(text_res, facial_res, speech_res, employee_id)
    if not fusion['success']:
        raise HTTPException(status_code=500, detail=fusion['error'])
    return fusion

# ── History & alert endpoints ──────────────────────────────────

@app.get('/mood-history')
def mood_history(employee_id: Optional[str] = None, limit: int = 20):
    if not os.path.exists(MOOD_LOG_CSV):
        return {'history': [], 'total': 0}
    df = pd.read_csv(MOOD_LOG_CSV)
    if employee_id and 'employee_id' in df.columns:
        df = df[df['employee_id'] == employee_id]
    df = df.tail(limit)
    return {'history': df.to_dict('records'), 'total': len(df)}

@app.get('/mood-history/summary')
def mood_summary(employee_id: Optional[str] = None):
    if not os.path.exists(MOOD_LOG_CSV):
        return {'summary': {}, 'total_sessions': 0}
    df = pd.read_csv(MOOD_LOG_CSV)
    if employee_id and 'employee_id' in df.columns:
        df = df[df['employee_id'] == employee_id]
    summary = df['final_mood'].value_counts().to_dict() if not df.empty else {}
    return {
        'employee_id'      : employee_id or 'all',
        'total_sessions'   : len(df),
        'mood_distribution': summary,
        'most_common_mood' : df['final_mood'].mode()[0] if not df.empty else None,
    }

@app.get('/alerts')
def get_alerts():
    if not os.path.exists(MOOD_LOG_CSV):
        return {'alerts': [], 'total': 0}
    df = pd.read_csv(MOOD_LOG_CSV)
    if 'employee_id' not in df.columns:
        return {'alerts': [], 'total': 0}
    alerts = []
    for emp_id in df['employee_id'].unique():
        emp_log = df[df['employee_id'] == emp_id]['final_mood'].tolist()
        consec  = 0
        for mood in reversed(emp_log):
            if mood in STRESS_MOODS: consec += 1
            else: break
        if consec >= 2:
            emp = get_employee(emp_id)
            alerts.append({
                'employee_id'        : emp_id,
                'employee_name'      : emp['name']       if emp else 'Unknown',
                'department'         : emp['department'] if emp else 'Unknown',
                'role'               : emp['role']       if emp else 'Unknown',
                'consecutive_stress' : consec,
                'alert_level'        : 'high' if consec >= BURNOUT_THRESHOLD else 'medium',
                'last_mood'          : emp_log[-1],
                'recommended_action' : 'HR check-in required' if consec >= BURNOUT_THRESHOLD else 'Manager notification',
            })
    return {'alerts': alerts, 'total': len(alerts)}


# ── Run ────────────────────────────────────────────────────────

if __name__ == '__main__':
    print(f'\n✅ Starting API server...')
    print(f'   http://{API_HOST}:{API_PORT}')
    print(f'   Docs: http://localhost:{API_PORT}/docs')
    print(f'   Dashboard: http://localhost:{API_PORT}/dashboard\n')
    uvicorn.run('src.module5_api:app', host=API_HOST, port=API_PORT, reload=True)

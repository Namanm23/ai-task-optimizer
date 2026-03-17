# src/module6_frontend.py
# ─────────────────────────────────────────────────────────────
# Module 6 — Frontend Dashboard
# Fixes: black camera, image preview, mobile layout
# ─────────────────────────────────────────────────────────────

import os, sys, webbrowser
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import *

API_URL = f'http://localhost:{API_PORT}'

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<title>AI Task Optimizer</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<script src="https://unpkg.com/react@18/umd/react.development.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<style>
:root {
  --bg:#0a0a0f; --surface:#13131a; --surface2:#1c1c27; --border:#2a2a3a;
  --accent:#7c6af7; --accent2:#f06292; --text:#e8e8f0; --muted:#6b6b80;
  --positive:#4ade80; --negative:#f87171; --neutral:#94a3b8;
  --energetic:#fb923c; --stressed:#e879f9; --focused:#38bdf8;
  --sidebar-w: 220px;
}
* { margin:0; padding:0; box-sizing:border-box; }
html,body { height:100%; }
body { background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; min-height:100vh; }
h1,h2,h3,h4 { font-family:'Syne',sans-serif; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }

/* ── Shell ── */
.shell { display:flex; min-height:100vh; }

/* ── Sidebar ── */
.sidebar {
  width:var(--sidebar-w); min-height:100vh;
  background:var(--surface); border-right:1px solid var(--border);
  display:flex; flex-direction:column; padding:24px 0;
  position:fixed; top:0; left:0; bottom:0; z-index:200;
  transition: transform 0.25s ease;
}
.logo { padding:0 20px 20px; border-bottom:1px solid var(--border); margin-bottom:12px; }
.logo-title { font-family:'Syne',sans-serif; font-size:14px; font-weight:800; background:linear-gradient(135deg,#7c6af7,#f06292); -webkit-background-clip:text; -webkit-text-fill-color:transparent; line-height:1.3; }
.logo-sub { font-size:11px; color:var(--muted); margin-top:2px; }
.nav-item { display:flex; align-items:center; gap:10px; padding:10px 20px; cursor:pointer; font-size:13px; color:var(--muted); border-left:2px solid transparent; transition:all 0.15s; user-select:none; }
.nav-item:hover { color:var(--text); background:var(--surface2); }
.nav-item.active { color:var(--text); font-weight:500; border-left-color:var(--accent); background:rgba(124,106,247,0.08); }
.nav-icon { width:18px; text-align:center; font-size:14px; }

/* ── Mobile top bar ── */
.topbar { display:none; position:fixed; top:0; left:0; right:0; height:52px; background:var(--surface); border-bottom:1px solid var(--border); z-index:300; align-items:center; padding:0 16px; justify-content:space-between; }
.topbar-title { font-family:'Syne',sans-serif; font-size:13px; font-weight:800; background:linear-gradient(135deg,#7c6af7,#f06292); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hamburger { background:none; border:none; color:var(--text); font-size:22px; cursor:pointer; padding:4px 8px; }
.overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:150; }
.overlay.show { display:block; }

/* ── Main ── */
.main { margin-left:var(--sidebar-w); flex:1; padding:32px 36px; max-width:1180px; }
.page-header { margin-bottom:24px; }
.page-title { font-size:24px; font-weight:700; letter-spacing:-0.02em; }
.page-sub { font-size:13px; color:var(--muted); margin-top:3px; }

/* ── Cards ── */
.card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; }
.card-title { font-size:11px; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; color:var(--muted); margin-bottom:14px; }
.grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.grid-4 { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
.stat-card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:18px; }
.stat-label { font-size:11px; color:var(--muted); letter-spacing:0.06em; text-transform:uppercase; }
.stat-value { font-family:'Syne',sans-serif; font-size:26px; font-weight:700; margin:5px 0 2px; }
.stat-detail { font-size:12px; color:var(--muted); }

/* ── Mood ── */
.mood-badge { display:inline-flex; align-items:center; gap:5px; padding:3px 9px; border-radius:20px; font-size:12px; font-weight:500; }
.mood-bar-track { height:6px; background:var(--surface2); border-radius:3px; overflow:hidden; flex:1; }
.mood-bar-fill { height:100%; border-radius:3px; transition:width 0.6s ease; }

/* ── Form ── */
.input { background:var(--surface2); border:1px solid var(--border); border-radius:8px; color:var(--text); padding:10px 14px; font-size:13px; font-family:'DM Sans',sans-serif; outline:none; width:100%; transition:border-color 0.15s; }
.input:focus { border-color:var(--accent); }
.textarea { resize:vertical; min-height:72px; }
.select { background:var(--surface2); border:1px solid var(--border); border-radius:8px; color:var(--text); padding:10px 14px; font-size:13px; font-family:'DM Sans',sans-serif; outline:none; width:100%; cursor:pointer; }
.label { font-size:12px; color:var(--muted); margin-bottom:6px; display:block; }
.form-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px; }
.form-col { display:flex; flex-direction:column; }

/* ── Buttons ── */
.btn { display:inline-flex; align-items:center; justify-content:center; gap:6px; padding:9px 18px; border-radius:8px; font-size:13px; font-weight:500; font-family:'DM Sans',sans-serif; cursor:pointer; border:none; transition:all 0.15s; }
.btn-primary { background:var(--accent); color:#fff; }
.btn-primary:hover { background:#6b5ce7; transform:translateY(-1px); }
.btn-primary:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
.btn-ghost { background:transparent; color:var(--muted); border:1px solid var(--border); }
.btn-ghost:hover { color:var(--text); border-color:var(--muted); }
.btn-danger { background:rgba(248,113,113,0.12); color:#f87171; border:1px solid rgba(248,113,113,0.3); }
.btn-success { background:rgba(74,222,128,0.12); color:#4ade80; border:1px solid rgba(74,222,128,0.3); }

/* ── Capture boxes ── */
.capture-box { background:var(--surface2); border:1px solid var(--border); border-radius:10px; padding:14px; margin-bottom:12px; }
.capture-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
.capture-label { font-size:13px; font-weight:500; }
.capture-status { display:flex; align-items:center; gap:6px; font-size:12px; color:var(--muted); }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; }
.dot-green { background:#4ade80; animation:pulse 1.5s infinite; }
.dot-red { background:#f87171; animation:pulse 0.8s infinite; }
.dot-gray { background:var(--muted); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* Camera */
.cam-wrap { position:relative; width:100%; border-radius:8px; overflow:hidden; background:#000; }
.cam-wrap video { width:100%; display:block; max-height:200px; object-fit:cover; }
.cam-placeholder { width:100%; height:160px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; color:var(--muted); font-size:13px; border:2px dashed var(--border); border-radius:8px; }
.photo-preview { width:100%; border-radius:8px; max-height:180px; object-fit:cover; border:2px solid #4ade80; display:block; }

/* Audio */
.audio-player { width:100%; margin-top:8px; filter:invert(0.85) hue-rotate(180deg); }
.rec-timer { font-size:22px; font-weight:700; font-family:'Syne',sans-serif; color:#f87171; text-align:center; padding:12px 0; }

/* Result */
.result-box { background:var(--surface2); border:1px solid var(--border); border-radius:12px; padding:22px; animation:fadeUp 0.3s ease; }
@keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.result-mood { font-family:'Syne',sans-serif; font-size:30px; font-weight:800; letter-spacing:-0.02em; }
.task-chip { display:inline-block; background:rgba(124,106,247,0.1); border:1px solid rgba(124,106,247,0.2); border-radius:6px; padding:5px 11px; font-size:12px; margin:3px; }
.spinner { width:16px; height:16px; border:2px solid rgba(255,255,255,0.2); border-top-color:#fff; border-radius:50%; animation:spin 0.6s linear infinite; }
@keyframes spin { to{transform:rotate(360deg)} }

/* Modality chips */
.mod-chips { background:rgba(124,106,247,0.06); border:1px solid rgba(124,106,247,0.15); border-radius:8px; padding:10px 14px; margin-bottom:12px; display:flex; gap:12px; flex-wrap:wrap; font-size:12px; }
.mod-chip { display:flex; align-items:center; gap:5px; }
.mod-chip.on { color:#4ade80; }
.mod-chip.off { color:var(--muted); }

/* Alerts */
.alert-high { background:rgba(248,113,113,0.08); border:1px solid rgba(248,113,113,0.25); border-radius:10px; padding:14px 16px; display:flex; align-items:flex-start; gap:12px; margin-bottom:12px; }
.alert-medium { background:rgba(251,146,60,0.08); border:1px solid rgba(251,146,60,0.25); border-radius:10px; padding:14px 16px; display:flex; align-items:flex-start; gap:12px; margin-bottom:12px; }

/* Table */
.table { width:100%; border-collapse:collapse; font-size:13px; }
.table th { text-align:left; padding:9px 12px; font-size:11px; letter-spacing:0.07em; text-transform:uppercase; color:var(--muted); border-bottom:1px solid var(--border); font-weight:500; }
.table td { padding:11px 12px; border-bottom:1px solid rgba(42,42,58,0.5); }
.table tr:hover td { background:var(--surface2); }
.table-scroll { overflow-x:auto; }

/* ── MOBILE ── */
@media (max-width: 768px) {
  :root { --sidebar-w: 220px; }
  .topbar { display:flex; }
  .sidebar { transform:translateX(-100%); }
  .sidebar.open { transform:translateX(0); }
  .main { margin-left:0; padding:72px 16px 24px; }
  .grid-2 { grid-template-columns:1fr; }
  .grid-4 { grid-template-columns:1fr 1fr; }
  .form-row { grid-template-columns:1fr; }
  .page-title { font-size:20px; }
  .result-mood { font-size:24px; }
  .stat-value { font-size:22px; }
  .table th, .table td { padding:8px 10px; font-size:12px; }
  .cam-wrap video { max-height:240px; }
}
@media (max-width: 400px) {
  .grid-4 { grid-template-columns:1fr 1fr; }
  .main { padding:64px 12px 20px; }
}
</style>
</head>
<body>
<div id="root"></div>
<script type="text/babel">
"""

SCRIPT = r"""
const API = '__API_URL__';
const MOOD_COLORS = {positive:'#4ade80',negative:'#f87171',neutral:'#94a3b8',energetic:'#fb923c',stressed:'#e879f9',focused:'#38bdf8'};
const MOOD_EMOJI  = {positive:'😊',negative:'😔',neutral:'😐',energetic:'⚡',stressed:'😰',focused:'🎯'};

function MoodBadge({mood}) {
  if (!mood||mood==='N/A') return <span style={{color:'var(--muted)',fontSize:12}}>—</span>;
  const c=MOOD_COLORS[mood]||'#94a3b8';
  return <span className="mood-badge" style={{background:`${c}18`,color:c,border:`1px solid ${c}40`}}>{MOOD_EMOJI[mood]} {mood}</span>;
}
function MoodBar({mood,value}) {
  const c=MOOD_COLORS[mood]||'#94a3b8';
  return (
    <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:7}}>
      <span style={{width:68,fontSize:12,color:'#6b6b80'}}>{mood}</span>
      <div className="mood-bar-track"><div className="mood-bar-fill" style={{width:`${value}%`,background:c}}/></div>
      <span style={{width:38,fontSize:12,color:'#6b6b80',textAlign:'right'}}>{value.toFixed(1)}%</span>
    </div>
  );
}

// ── Analyze Page ────────────────────────────────────────────
function AnalyzePage({employees}) {
  const [empId,setEmpId]       = React.useState('');
  const [text,setText]         = React.useState('');
  const [loading,setLoading]   = React.useState(false);
  const [result,setResult]     = React.useState(null);
  const [error,setError]       = React.useState('');

  // Camera
  const videoRef               = React.useRef(null);
  const canvasRef              = React.useRef(null);
  const streamRef              = React.useRef(null);
  const [camOn,setCamOn]       = React.useState(false);
  const [camReady,setCamReady] = React.useState(false);
  const [photoBlob,setPhotoBlob] = React.useState(null);
  const [photoURL,setPhotoURL]   = React.useState(null);

  // Mic
  const recRef                 = React.useRef(null);
  const chunksRef              = React.useRef([]);
  const timerRef               = React.useRef(null);
  const [recording,setRecording]   = React.useState(false);
  const [audioBlob,setAudioBlob]   = React.useState(null);
  const [audioURL,setAudioURL]     = React.useState(null);
  const [recSecs,setRecSecs]       = React.useState(0);

  // ── Camera ─────────────────────────────────────────────
  async function openCam() {
    try {
      const constraints = {
        video: { facingMode: 'user', width:{ideal:640}, height:{ideal:480} }
      };
      const s = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = s;
      setCamOn(true);
      setCamReady(false);
      // Wait for next render then attach stream
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = s;
          videoRef.current.onloadedmetadata = () => {
            videoRef.current.play();
            setCamReady(true);
          };
        }
      }, 100);
    } catch(e) {
      setError('Camera error: ' + e.message);
    }
  }

  function closeCam() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t=>t.stop());
      streamRef.current = null;
    }
    setCamOn(false); setCamReady(false);
  }

  function takePhoto() {
    const v = videoRef.current;
    const c = canvasRef.current;
    if (!v || !camReady) return;
    c.width  = v.videoWidth  || 640;
    c.height = v.videoHeight || 480;
    c.getContext('2d').drawImage(v, 0, 0);
    c.toBlob(blob => {
      setPhotoBlob(blob);
      setPhotoURL(URL.createObjectURL(blob));
      closeCam();
    }, 'image/jpeg', 0.92);
  }

  function removePhoto() {
    setPhotoBlob(null);
    if (photoURL) URL.revokeObjectURL(photoURL);
    setPhotoURL(null);
  }

  // ── Microphone ──────────────────────────────────────────
  async function startRec() {
    try {
      const s   = await navigator.mediaDevices.getUserMedia({audio:true});
      const rec = new MediaRecorder(s, {mimeType:'audio/webm'});
      chunksRef.current = [];
      rec.ondataavailable = e => { if(e.data.size>0) chunksRef.current.push(e.data); };
      rec.onstop = () => {
        const blob = new Blob(chunksRef.current, {type:'audio/webm'});
        setAudioBlob(blob);
        setAudioURL(URL.createObjectURL(blob));
        s.getTracks().forEach(t=>t.stop());
      };
      rec.start(100);
      recRef.current = rec;
      setRecording(true);
      setRecSecs(0);
      timerRef.current = setInterval(()=>setRecSecs(s=>s+1), 1000);
    } catch(e) { setError('Mic error: '+e.message); }
  }

  function stopRec() {
    if (recRef.current) recRef.current.stop();
    clearInterval(timerRef.current);
    setRecording(false);
  }

  function removeAudio() {
    setAudioBlob(null);
    if (audioURL) URL.revokeObjectURL(audioURL);
    setAudioURL(null);
    setRecSecs(0);
  }

  // ── Submit ──────────────────────────────────────────────
  async function analyze() {
    if (!empId) { setError('Please select an employee'); return; }
    if (!text.trim() && !photoBlob && !audioBlob) {
      setError('Please provide at least one input'); return;
    }
    setError(''); setLoading(true); setResult(null);
    try {
      const fd = new FormData();
      fd.append('employee_id', empId);
      if (text.trim())  fd.append('text',  text);
      if (photoBlob)    fd.append('image', photoBlob, 'photo.jpg');
      if (audioBlob)    fd.append('audio', audioBlob, 'audio.webm');
      const res  = await fetch(`${API}/analyze`, {method:'POST',body:fd});
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail||'API error');
      setResult(data);
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  const mood = result?.final_mood;
  const mc   = MOOD_COLORS[mood]||'#7c6af7';

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Analyze Mood</h1>
        <p className="page-sub">Text + Webcam + Microphone — all 3 models fused</p>
      </div>

      <div className="grid-2">
        {/* ── LEFT: Inputs ── */}
        <div className="card">
          <div className="card-title">Input</div>

          {/* Employee */}
          <div style={{marginBottom:14}}>
            <label className="label">Employee</label>
            <select className="select" value={empId} onChange={e=>setEmpId(e.target.value)}>
              <option value="">— select employee —</option>
              {employees.map(e=>(
                <option key={e.employee_id} value={e.employee_id}>{e.name} ({e.department})</option>
              ))}
            </select>
          </div>

          {/* Text */}
          <div style={{marginBottom:14}}>
            <label className="label">📝 Text — How are you feeling?</label>
            <textarea className="input textarea"
              placeholder="e.g. I feel stressed and overwhelmed today..."
              value={text} onChange={e=>setText(e.target.value)}/>
          </div>

          {/* ── Camera ── */}
          <div className="capture-box">
            <div className="capture-header">
              <span className="capture-label">📸 Facial — Webcam</span>
              <span className="capture-status">
                <span className={`dot ${camOn?'dot-green':photoBlob?'dot-green':'dot-gray'}`}/>
                {camOn?(camReady?'Camera ready':'Starting...'):(photoBlob?'Photo captured':'No photo')}
              </span>
            </div>

            {/* Live camera feed */}
            {camOn && (
              <div>
                <div className="cam-wrap">
                  <video ref={videoRef} autoPlay playsInline muted
                    style={{width:'100%',display:'block',maxHeight:200,objectFit:'cover',
                            background:'#000',borderRadius:8}}/>
                  {!camReady && (
                    <div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',
                                 justifyContent:'center',background:'rgba(0,0,0,0.7)',borderRadius:8,
                                 color:'var(--muted)',fontSize:13}}>
                      ⏳ Starting camera...
                    </div>
                  )}
                </div>
                <canvas ref={canvasRef} style={{display:'none'}}/>
                <div style={{display:'flex',gap:8,marginTop:10}}>
                  <button className="btn btn-success" style={{flex:1}}
                    onClick={takePhoto} disabled={!camReady}>
                    📸 {camReady?'Capture Photo':'Waiting...'}
                  </button>
                  <button className="btn btn-danger" onClick={closeCam}>✕</button>
                </div>
              </div>
            )}

            {/* Photo preview */}
            {!camOn && photoURL && (
              <div>
                <img src={photoURL} className="photo-preview" alt="Captured"/>
                <div style={{display:'flex',gap:8,marginTop:8,alignItems:'center'}}>
                  <span style={{flex:1,fontSize:12,color:'#4ade80'}}>✅ Photo captured!</span>
                  <button className="btn btn-ghost" style={{fontSize:12,padding:'5px 10px'}}
                    onClick={()=>{removePhoto();openCam();}}>📷 Retake</button>
                  <button className="btn btn-danger" style={{fontSize:12,padding:'5px 10px'}}
                    onClick={removePhoto}>✕</button>
                </div>
              </div>
            )}

            {/* Open camera button */}
            {!camOn && !photoURL && (
              <button className="btn btn-ghost" style={{width:'100%',marginTop:4}}
                onClick={openCam}>
                📷 Open Camera
              </button>
            )}
          </div>

          {/* ── Microphone ── */}
          <div className="capture-box">
            <div className="capture-header">
              <span className="capture-label">🎙️ Speech — Microphone</span>
              <span className="capture-status">
                <span className={`dot ${recording?'dot-red':audioBlob?'dot-green':'dot-gray'}`}/>
                {recording?`🔴 ${recSecs}s`:audioBlob?`✅ ${recSecs}s recorded`:'No audio'}
              </span>
            </div>

            {recording && (
              <div>
                <div className="rec-timer">🔴 {recSecs}s</div>
                <button className="btn btn-danger" style={{width:'100%'}} onClick={stopRec}>
                  ⏹ Stop Recording
                </button>
              </div>
            )}

            {!recording && audioBlob && (
              <div>
                <audio controls src={audioURL} className="audio-player"/>
                <div style={{display:'flex',gap:8,marginTop:8}}>
                  <span style={{flex:1,fontSize:12,color:'#4ade80',display:'flex',alignItems:'center'}}>✅ Ready</span>
                  <button className="btn btn-ghost" style={{fontSize:12,padding:'5px 10px'}}
                    onClick={()=>{removeAudio();startRec();}}>🎙️ Re-record</button>
                  <button className="btn btn-danger" style={{fontSize:12,padding:'5px 10px'}}
                    onClick={removeAudio}>✕</button>
                </div>
              </div>
            )}

            {!recording && !audioBlob && (
              <button className="btn btn-ghost" style={{width:'100%',marginTop:4}} onClick={startRec}>
                🎙️ Start Recording
              </button>
            )}
          </div>

          {/* Active modalities */}
          <div className="mod-chips">
            <span className={`mod-chip ${text.trim()?'on':'off'}`}>📝 Text {text.trim()?'✓':'○'}</span>
            <span className={`mod-chip ${photoBlob?'on':'off'}`}>📸 Facial {photoBlob?'✓':'○'}</span>
            <span className={`mod-chip ${audioBlob?'on':'off'}`}>🎙️ Speech {audioBlob?'✓':'○'}</span>
          </div>

          {error && <p style={{color:'#f87171',fontSize:13,marginBottom:12}}>⚠️ {error}</p>}

          <button className="btn btn-primary" onClick={analyze} disabled={loading}
            style={{width:'100%',padding:'12px',fontSize:14}}>
            {loading?<><span className="spinner"/> Analyzing...</>:'⚡ Analyze Mood'}
          </button>
        </div>

        {/* ── RIGHT: Result ── */}
        <div>
          {result ? (
            <div className="result-box">
              <div style={{marginBottom:16}}>
                <div style={{fontSize:12,color:'#6b6b80',marginBottom:5}}>
                  {result.employee_name} · {result.department}
                </div>
                <div className="result-mood" style={{color:mc}}>
                  {MOOD_EMOJI[mood]} {mood?.toUpperCase()}
                </div>
                <div style={{fontSize:13,color:'#6b6b80',marginTop:4}}>
                  Confidence: {result.confidence?.toFixed(1)}%
                </div>
                <div style={{fontSize:12,color:'var(--muted)',marginTop:3}}>
                  Modalities: {result.modalities_used?.join(' + ')}
                </div>
              </div>

              {result.alert_level && result.alert_level!=='none' && (
                <div style={{background:'rgba(248,113,113,0.08)',border:'1px solid rgba(248,113,113,0.2)',
                             borderRadius:8,padding:'10px 14px',marginBottom:14,fontSize:13}}>
                  🚨 <strong>{result.alert_level?.toUpperCase()}</strong> burnout risk detected
                </div>
              )}

              <div style={{marginBottom:14}}>
                <div className="card-title">Individual Results</div>
                <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:12}}>
                  <span style={{fontSize:12,color:'var(--muted)'}}>📝</span>
                  <MoodBadge mood={result.individual?.text}/>
                  <span style={{fontSize:12,color:'var(--muted)'}}>📸</span>
                  <MoodBadge mood={result.individual?.facial}/>
                  <span style={{fontSize:12,color:'var(--muted)'}}>🎙️</span>
                  <MoodBadge mood={result.individual?.speech}/>
                </div>
                <div className="card-title">Fused Scores</div>
                {Object.entries(result.fused_scores||{}).sort((a,b)=>b[1]-a[1])
                  .map(([m,v])=><MoodBar key={m} mood={m} value={v}/>)}
              </div>

              <div>
                <div className="card-title">Recommended Tasks</div>
                {result.tasks?.map((t,i)=><span key={i} className="task-chip">{t}</span>)}
              </div>
            </div>
          ) : (
            <div className="card" style={{minHeight:360,display:'flex',alignItems:'center',
              justifyContent:'center',flexDirection:'column',gap:12,color:'var(--muted)'}}>
              <div style={{fontSize:48}}>🧠</div>
              <div style={{fontSize:13}}>Fill inputs then click Analyze</div>
              <div style={{fontSize:12,opacity:0.6}}>At least one input required</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Employees ───────────────────────────────────────────────
function EmployeesPage({employees,onRefresh}) {
  const [form,setForm]       = React.useState({name:'',email:'',department:'',role:''});
  const [loading,setLoading] = React.useState(false);
  const [msg,setMsg]         = React.useState('');

  async function add() {
    if (!form.name||!form.email||!form.department||!form.role){setMsg('⚠️ All fields required');return;}
    setLoading(true);setMsg('');
    try {
      const fd=new FormData();
      Object.entries(form).forEach(([k,v])=>fd.append(k,v));
      const res=await fetch(`${API}/employees`,{method:'POST',body:fd});
      const data=await res.json();
      if(!res.ok) throw new Error(data.detail);
      setMsg(`✅ ${data.message}`);
      setForm({name:'',email:'',department:'',role:''});
      onRefresh();
    } catch(e){setMsg(`❌ ${e.message}`);}
    finally{setLoading(false);}
  }

  async function del(id,name) {
    if(!confirm(`Delete ${name}?`))return;
    await fetch(`${API}/employees/${id}`,{method:'DELETE'});
    onRefresh();
  }

  return (
    <div>
      <div className="page-header"><h1 className="page-title">Employees</h1><p className="page-sub">Manage profiles</p></div>
      <div className="grid-2" style={{alignItems:'start'}}>
        <div className="card">
          <div className="card-title">Add Employee</div>
          <div className="form-row">
            <div className="form-col"><label className="label">Full Name</label><input className="input" placeholder="Arjun Sharma" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></div>
            <div className="form-col"><label className="label">Email</label><input className="input" placeholder="arjun@co.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></div>
          </div>
          <div className="form-row">
            <div className="form-col"><label className="label">Department</label><input className="input" placeholder="Engineering" value={form.department} onChange={e=>setForm({...form,department:e.target.value})}/></div>
            <div className="form-col"><label className="label">Role</label><input className="input" placeholder="Developer" value={form.role} onChange={e=>setForm({...form,role:e.target.value})}/></div>
          </div>
          {msg&&<p style={{fontSize:13,marginBottom:12,color:msg.startsWith('✅')?'#4ade80':'#f87171'}}>{msg}</p>}
          <button className="btn btn-primary" onClick={add} disabled={loading}>{loading?'Adding...':'+ Add Employee'}</button>
        </div>
        <div className="card">
          <div className="card-title">All Employees ({employees.length})</div>
          <div className="table-scroll">
            <table className="table">
              <thead><tr><th>Name</th><th>Dept</th><th>Role</th><th></th></tr></thead>
              <tbody>
                {employees.map(e=>(
                  <tr key={e.employee_id}>
                    <td><div style={{fontWeight:500}}>{e.name}</div><div style={{fontSize:11,color:'var(--muted)'}}>{e.employee_id}</div></td>
                    <td>{e.department}</td><td style={{color:'var(--muted)'}}>{e.role}</td>
                    <td><button className="btn btn-ghost" style={{padding:'3px 9px',fontSize:11}} onClick={()=>del(e.employee_id,e.name)}>Del</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── History ─────────────────────────────────────────────────
function HistoryPage({employees}) {
  const [history,setHistory] = React.useState([]);
  const [empId,setEmpId]     = React.useState('');
  React.useEffect(()=>{
    async function load(){
      const p=empId?`?employee_id=${empId}&limit=30`:'?limit=30';
      const res=await fetch(`${API}/mood-history${p}`);
      const d=await res.json();
      setHistory(d.history||[]);
    }
    load();
  },[empId]);
  return (
    <div>
      <div className="page-header"><h1 className="page-title">Mood History</h1><p className="page-sub">Past sessions</p></div>
      <div className="card">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:18,flexWrap:'wrap',gap:10}}>
          <div className="card-title" style={{marginBottom:0}}>Sessions</div>
          <select className="select" style={{width:200}} value={empId} onChange={e=>setEmpId(e.target.value)}>
            <option value="">All employees</option>
            {employees.map(e=><option key={e.employee_id} value={e.employee_id}>{e.name}</option>)}
          </select>
        </div>
        {history.length===0?<div style={{textAlign:'center',padding:'40px 0',color:'var(--muted)'}}>No history yet!</div>:(
          <div className="table-scroll">
            <table className="table">
              <thead><tr><th>Employee</th><th>Mood</th><th>Conf.</th><th>Text</th><th>Face</th><th>Speech</th><th>Time</th></tr></thead>
              <tbody>
                {history.slice().reverse().map((h,i)=>(
                  <tr key={i}>
                    <td style={{fontWeight:500}}>{h.name||h.employee_id}</td>
                    <td><MoodBadge mood={h.final_mood}/></td>
                    <td style={{color:'var(--muted)'}}>{h.confidence?.toFixed(1)}%</td>
                    <td><MoodBadge mood={h.text_mood}/></td>
                    <td><MoodBadge mood={h.facial_mood}/></td>
                    <td><MoodBadge mood={h.speech_mood}/></td>
                    <td style={{color:'var(--muted)',fontSize:11}}>{h.timestamp?.slice(0,16)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Alerts ──────────────────────────────────────────────────
function AlertsPage() {
  const [alerts,setAlerts]   = React.useState([]);
  const [loading,setLoading] = React.useState(true);
  React.useEffect(()=>{
    fetch(`${API}/alerts`).then(r=>r.json()).then(d=>{setAlerts(d.alerts||[]);setLoading(false);}).catch(()=>setLoading(false));
  },[]);
  return (
    <div>
      <div className="page-header"><h1 className="page-title">HR Alerts</h1><p className="page-sub">Burnout risk detection</p></div>
      {loading?<div style={{color:'var(--muted)'}}>Loading...</div>:
        alerts.length===0?(
          <div className="card" style={{textAlign:'center',padding:'50px 0',color:'var(--muted)'}}>
            <div style={{fontSize:40,marginBottom:10}}>✅</div>
            <div>No stress alerts. All employees are doing well!</div>
          </div>
        ):alerts.map((a,i)=>(
          <div key={i} className={a.alert_level==='high'?'alert-high':'alert-medium'}>
            <div style={{fontSize:22}}>{a.alert_level==='high'?'🚨':'🟠'}</div>
            <div style={{flex:1}}>
              <div style={{fontWeight:600,fontSize:13}}>{a.employee_name}
                <span style={{color:'var(--muted)',fontWeight:400,fontSize:12}}> · {a.department}</span>
              </div>
              <div style={{fontSize:12,color:'var(--muted)',marginTop:3}}>
                {a.consecutive_stress} stress sessions · <MoodBadge mood={a.last_mood}/>
              </div>
              <div style={{fontSize:12,marginTop:5,color:a.alert_level==='high'?'#f87171':'#fb923c'}}>
                👉 {a.recommended_action}
              </div>
            </div>
            <div style={{background:a.alert_level==='high'?'rgba(248,113,113,0.15)':'rgba(251,146,60,0.15)',
              padding:'3px 10px',borderRadius:6,fontSize:11,fontWeight:600,
              color:a.alert_level==='high'?'#f87171':'#fb923c',whiteSpace:'nowrap'}}>
              {a.alert_level.toUpperCase()}
            </div>
          </div>
        ))
      }
    </div>
  );
}

// ── Dashboard ────────────────────────────────────────────────
function DashboardPage({employees}) {
  const [summary,setSummary] = React.useState(null);
  const [alerts,setAlerts]   = React.useState([]);
  const [health,setHealth]   = React.useState(null);
  React.useEffect(()=>{
    Promise.all([
      fetch(`${API}/mood-history/summary`).then(r=>r.json()),
      fetch(`${API}/alerts`).then(r=>r.json()),
      fetch(`${API}/health`).then(r=>r.json()),
    ]).then(([s,a,h])=>{setSummary(s);setAlerts(a.alerts||[]);setHealth(h);}).catch(()=>{});
  },[]);
  const dist=summary?.mood_distribution||{},total=summary?.total_sessions||0,topMood=summary?.most_common_mood;
  const highRisk=alerts.filter(a=>a.alert_level==='high').length;
  return (
    <div>
      <div className="page-header"><h1 className="page-title">Overview</h1><p className="page-sub">Workplace mood at a glance</p></div>
      <div className="grid-4" style={{marginBottom:20}}>
        <div className="stat-card"><div className="stat-label">Employees</div><div className="stat-value">{employees.length}</div><div className="stat-detail">registered</div></div>
        <div className="stat-card"><div className="stat-label">Sessions</div><div className="stat-value">{total}</div><div className="stat-detail">analyses</div></div>
        <div className="stat-card"><div className="stat-label">Top Mood</div><div className="stat-value" style={{color:MOOD_COLORS[topMood]||'var(--accent)'}}>{topMood?MOOD_EMOJI[topMood]:'—'}</div><div className="stat-detail">{topMood||'no data'}</div></div>
        <div className="stat-card"><div className="stat-label">Alerts</div><div className="stat-value" style={{color:highRisk>0?'#f87171':'#4ade80'}}>{highRisk}</div><div className="stat-detail">{highRisk>0?'need attention':'all clear'}</div></div>
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Mood Distribution</div>
          {total===0?<div style={{color:'var(--muted)',fontSize:13}}>No sessions yet!</div>:
            Object.entries(dist).sort((a,b)=>b[1]-a[1]).map(([m,v])=><MoodBar key={m} mood={m} value={(v/total)*100}/>)}
        </div>
        <div className="card">
          <div className="card-title">Recent Alerts</div>
          {alerts.length===0?<div style={{color:'var(--muted)',fontSize:13}}>✅ All clear!</div>:
            alerts.slice(0,3).map((a,i)=>(
              <div key={i} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'9px 0',borderBottom:'1px solid var(--border)'}}>
                <div><div style={{fontSize:13,fontWeight:500}}>{a.employee_name}</div><div style={{fontSize:11,color:'var(--muted)'}}>{a.consecutive_stress} stress sessions</div></div>
                <span style={{background:a.alert_level==='high'?'rgba(248,113,113,0.1)':'rgba(251,146,60,0.1)',color:a.alert_level==='high'?'#f87171':'#fb923c',padding:'3px 9px',borderRadius:6,fontSize:11,fontWeight:600}}>{a.alert_level.toUpperCase()}</span>
              </div>
            ))
          }
        </div>
      </div>
      {health&&<div style={{marginTop:16,display:'flex',alignItems:'center',gap:8,fontSize:12,color:'var(--muted)'}}>
        <span style={{width:6,height:6,borderRadius:'50%',background:'#4ade80',display:'inline-block'}}/>
        API healthy · {health.total_employees} employees · {health.timestamp}
      </div>}
    </div>
  );
}

// ── App Shell ─────────────────────────────────────────────────
function App() {
  const [page,setPage]           = React.useState('dashboard');
  const [employees,setEmployees] = React.useState([]);
  const [menuOpen,setMenuOpen]   = React.useState(false);

  async function loadEmployees() {
    try {
      const res=await fetch(`${API}/employees`);
      const d=await res.json();
      setEmployees(d.employees||[]);
    } catch(e){}
  }
  React.useEffect(()=>{loadEmployees();},[]);

  const nav=[
    {id:'dashboard',icon:'◈',label:'Overview'},
    {id:'analyze',  icon:'⚡',label:'Analyze Mood'},
    {id:'employees',icon:'◎',label:'Employees'},
    {id:'history',  icon:'◷',label:'Mood History'},
    {id:'alerts',   icon:'⚠',label:'HR Alerts'},
  ];

  function navTo(id) { setPage(id); setMenuOpen(false); }

  return (
    <div className="shell">
      {/* Mobile top bar */}
      <div className="topbar">
        <button className="hamburger" onClick={()=>setMenuOpen(o=>!o)}>☰</button>
        <span className="topbar-title">AI Task Optimizer</span>
        <span style={{width:40}}/>
      </div>

      {/* Overlay */}
      <div className={`overlay ${menuOpen?'show':''}`} onClick={()=>setMenuOpen(false)}/>

      {/* Sidebar */}
      <nav className={`sidebar ${menuOpen?'open':''}`}>
        <div className="logo">
          <div className="logo-title">AI Task<br/>Optimizer</div>
          <div className="logo-sub">Emotion Intelligence</div>
        </div>
        {nav.map(n=>(
          <div key={n.id} className={`nav-item ${page===n.id?'active':''}`} onClick={()=>navTo(n.id)}>
            <span className="nav-icon">{n.icon}</span>{n.label}
          </div>
        ))}
      </nav>

      {/* Main */}
      <main className="main">
        {page==='dashboard'&&<DashboardPage employees={employees}/>}
        {page==='analyze'  &&<AnalyzePage   employees={employees}/>}
        {page==='employees'&&<EmployeesPage employees={employees} onRefresh={loadEmployees}/>}
        {page==='history'  &&<HistoryPage   employees={employees}/>}
        {page==='alerts'   &&<AlertsPage/>}
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
"""

FOOT = "\n</script>\n</body>\n</html>"

def generate(api_url: str = API_URL) -> str:
    return HEAD + SCRIPT.replace('__API_URL__', api_url) + FOOT

if __name__ == '__main__':
    html = generate()
    out  = os.path.join(OUTPUTS_DIR, 'dashboard.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✅ Dashboard generated: {out}')
    webbrowser.open(f'http://localhost:{API_PORT}/')
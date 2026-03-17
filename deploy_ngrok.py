# deploy_ngrok.py
# ─────────────────────────────────────────────────────────────
# Deploys AI-Powered Task Optimizer publicly via ngrok
# Run: python deploy_ngrok.py
# ─────────────────────────────────────────────────────────────

import os, sys, time, threading, asyncio, json, webbrowser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Step 1: Check pyngrok installed ───────────────────────────
try:
    from pyngrok import ngrok, conf
except ImportError:
    print('Installing pyngrok...')
    os.system(f'{sys.executable} -m pip install pyngrok -q')
    from pyngrok import ngrok, conf

import uvicorn
import nest_asyncio
nest_asyncio.apply()

# ══════════════════════════════════════════════════════════════
NGROK_TOKEN = '3AtBcELifV1Banp5TMmOmAwrucA_6cqF67rU4i3dHuqKV8E4E'   
# ══════════════════════════════════════════════════════════════

from src.config import API_PORT, OUTPUTS_DIR, BASE_DIR


def generate_dashboard(public_url: str):
    """Regenerate dashboard.html with the public ngrok URL."""
    print(f'\n  Generating dashboard with URL: {public_url}')
    # Import the generator from module6
    sys.path.insert(0, os.path.join(BASE_DIR, 'src'))
    from module6_frontend import generate
    html = generate(api_url=public_url)
    out  = os.path.join(OUTPUTS_DIR, 'dashboard.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  ✅ Dashboard saved: {out}')
    return out


def save_public_url(public_url: str):
    """Save public URL to fusion config for future reference."""
    config_path = os.path.join(BASE_DIR, 'models', 'fusion', 'api_config.json')
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    config = {
        'public_url' : public_url,
        'local_url'  : f'http://localhost:{API_PORT}',
        'dashboard'  : f'{public_url}/',
        'docs'       : f'{public_url}/docs',
        'updated_at' : __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f'  ✅ URL saved: {config_path}')


def start_server():
    """Run uvicorn in a background thread."""
    from src.module5_api import app
    config = uvicorn.Config(
        app,
        host      = '0.0.0.0',
        port      = API_PORT,
        log_level = 'warning',
    )
    server = uvicorn.Server(config)
    loop   = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server.serve())


def wait_for_server(timeout: int = 30) -> bool:
    """Poll localhost until API is up."""
    import requests
    for _ in range(timeout):
        try:
            r = requests.get(f'http://localhost:{API_PORT}/health', timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main():
    print('=' * 55)
    print('  AI-Powered Task Optimizer — ngrok Deployment')
    print('=' * 55)

    # ── Validate token ─────────────────────────────────────────
    if NGROK_TOKEN == 'YOUR_NEW_TOKEN_HERE':
        print('\n❌ Please paste your ngrok token in deploy_ngrok.py')
        print('   NGROK_TOKEN = "YOUR_NEW_TOKEN_HERE"  ← change this line')
        print('\n   Get your token at: https://dashboard.ngrok.com')
        sys.exit(1)

    # ── Kill any existing ngrok/uvicorn ────────────────────────
    print('\n  Cleaning up old processes...')
    try:
        ngrok.kill()
    except Exception:
        pass
    time.sleep(1)

    # ── Start API server in background thread ──────────────────
    print('  Starting API server...')
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()

    # ── Wait for server to be ready ────────────────────────────
    print('  Waiting for API to be ready', end='')
    ready = wait_for_server(timeout=40)
    print()
    if not ready:
        print('❌ API server failed to start. Check for errors above.')
        sys.exit(1)
    print('  ✅ API server is UP on localhost:8000')

    # ── Start ngrok tunnel ─────────────────────────────────────
    print('\n  Starting ngrok tunnel...')
    try:
        ngrok.set_auth_token(NGROK_TOKEN)
        tunnel     = ngrok.connect(API_PORT, bind_tls=True)
        public_url = tunnel.public_url
        print(f'  ✅ ngrok tunnel active!')
    except Exception as e:
        print(f'❌ ngrok failed: {e}')
        print('   Make sure your token is correct and you have internet.')
        sys.exit(1)

    # ── Generate dashboard with public URL ─────────────────────
    generate_dashboard(public_url)
    save_public_url(public_url)

    # ── Print summary ──────────────────────────────────────────
    print('\n' + '=' * 55)
    print('  🚀 DEPLOYMENT COMPLETE!')
    print('=' * 55)
    print(f'\n  🌍 Public URL   : {public_url}')
    print(f'  📊 Dashboard    : {public_url}/')
    print(f'  📖 API Docs     : {public_url}/docs')
    print(f'  ❤️  Health Check : {public_url}/health')
    print(f'\n  💻 Local URL    : http://localhost:{API_PORT}')
    print(f'\n  Share the Public URL with anyone!')
    print(f'  It works as long as this script is running.')
    print('\n  Press Ctrl+C to stop.\n')
    print('=' * 55)

    # ── Open dashboard in browser ──────────────────────────────
    time.sleep(1)
    webbrowser.open(f'{public_url}/')

    # ── Keep alive ─────────────────────────────────────────────
    try:
        while True:
            time.sleep(5)
            # Check tunnel is still alive
            tunnels = ngrok.get_tunnels()
            if not tunnels:
                print('\n⚠️  ngrok tunnel dropped! Reconnecting...')
                tunnel     = ngrok.connect(API_PORT, bind_tls=True)
                public_url = tunnel.public_url
                generate_dashboard(public_url)
                save_public_url(public_url)
                print(f'  ✅ Reconnected: {public_url}')
    except KeyboardInterrupt:
        print('\n\n  Shutting down...')
        ngrok.kill()
        print('  ✅ ngrok stopped. Goodbye!')


if __name__ == '__main__':
    main()

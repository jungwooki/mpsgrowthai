#!/bin/zsh
set -e
cd "${0:A:h}"
# A copied virtual environment may refer to another computer. Use a local cache.
python_bin=""
for candidate in python3.12 "$HOME/.local/bin/python3.12" /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; assert sys.version_info[:2] == (3, 12)' >/dev/null 2>&1; then
    python_bin="$candidate"
    break
  fi
done
if [[ -z "$python_bin" ]]; then
  print 'Python 3.12가 필요합니다. 설치 후 다시 실행해 주세요.'
  exit 1
fi
runtime_dir="${MPS_GROWTH_RUNTIME_DIR:-$HOME/Library/Caches/mps-growth/venv-py312}"
if [[ ! -x "$runtime_dir/bin/python" ]] || ! "$runtime_dir/bin/python" -c 'import sys; assert sys.version_info[:2] == (3, 12)' >/dev/null 2>&1; then
  "$python_bin" -m venv "$runtime_dir"
fi
requirements_hash=$(shasum -a 256 requirements.txt | cut -d ' ' -f 1)
if [[ ! -f "$runtime_dir/.requirements.sha256" ]] || [[ "$(cat "$runtime_dir/.requirements.sha256")" != "$requirements_hash" ]]; then
  "$runtime_dir/bin/python" -m pip install -r requirements.txt
  print -r -- "$requirements_hash" > "$runtime_dir/.requirements.sha256"
fi
if [[ ! -f .env ]]; then cp .env.example .env; fi
app_port="${PORT:-8093}"
print "MPS Growth 시작: http://127.0.0.1:$app_port"
print '이 창을 열어두세요. 종료: Control+C'
if [[ "${GROWTH_NO_BROWSER:-0}" != 1 ]]; then
  (sleep 2; open "http://127.0.0.1:$app_port") &
fi
exec "$runtime_dir/bin/python" -m uvicorn server:app --host 127.0.0.1 --port "$app_port"

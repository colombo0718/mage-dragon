"""跑 3 場 codex vs codex、每場後 reset。"""
import subprocess, urllib.request, time, json

for i in range(1, 4):
    print(f"\n{'='*60}\n  ROUND {i}/3 — codex(A) vs codex(B)\n{'='*60}")
    r = subprocess.run(
        ["python", "match_v2.py", "--a", "codex", "--b", "codex", "--max-turns", "10"],
        cwd="C:/Users/USER/mage-dragon")

    print(f"\n--- Round {i} 結束、reset 中…")
    try:
        req = urllib.request.Request("http://localhost:8080/reset", method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(resp.read().decode())
    except Exception as e:
        print(f"reset error: {e}")
    time.sleep(4)

print("\n=== 三場結束、檢查 matches/ 看戰報 ===")

# /// script
# requires-python = ">=3.10"
# dependencies = ["faster-whisper>=1.0", "requests", "imageio-ffmpeg>=0.5", "numpy"]
# ///
"""Sesi kelime kelime zamanlı yazıya döker.

    uv run dokum.py <proje klasörü> [--model small|medium] [--dil tr]

- Proje klasöründeki ilk ses dosyasını (mp3, wav, m4a…) dinler.
- ELEVENLABS_API_KEY tanımlıysa (ortamda ya da proje klasöründeki .env'de) ElevenLabs ile döker,
  yoksa bilgisayarda ücretsiz Whisper ile (ilk seferde ~500 MB model iner).
- Klasörde senaryo.txt varsa kelimeler senaryoya göre düzeltilir (zamanlar korunur).
Çıktı: kelimeler.json [{w, s, e}] ve okunması kolay dokum.txt.
"""
import argparse, difflib, json, os, re, sys
from pathlib import Path

SES_UZANTI = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus", ".mp4", ".mov"}


def ses_bul(proje: Path) -> Path:
    adaylar = sorted(p for p in proje.iterdir() if p.suffix.lower() in SES_UZANTI
                     and not p.name.startswith(("muzik", "video", ".")))
    if not adaylar:
        sys.exit(f"HATA: {proje} içinde ses dosyası yok (mp3, wav, m4a…).")
    return adaylar[0]


def anahtar(proje: Path):
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    env = proje / ".env"
    if env.exists():
        for satir in env.read_text(encoding="utf-8").splitlines():
            if satir.strip().startswith("ELEVENLABS_API_KEY="):
                return satir.split("=", 1)[1].strip().strip('"\'')
    return None


def elevenlabs(ses: Path, key: str):
    import requests
    with open(ses, "rb") as f:
        r = requests.post("https://api.elevenlabs.io/v1/speech-to-text",
                          headers={"xi-api-key": key},
                          data={"model_id": "scribe_v1", "timestamps_granularity": "word"},
                          files={"file": (ses.name, f)}, timeout=300)
    if r.status_code != 200:
        print(f"ElevenLabs hata verdi ({r.status_code}): {r.text[:200]}\nÜcretsiz yerel dökümle devam ediliyor.")
        return None
    return [{"w": w["text"].strip(), "s": w["start"], "e": w["end"]}
            for w in r.json().get("words", []) if w.get("type") == "word" and w["text"].strip()]


def sesi_oku(ses: Path):
    """Sesi 16 kHz mono diziye çevirir (paketle gelen ffmpeg ile; sistemde ffmpeg gerekmez)."""
    import subprocess, numpy as np, imageio_ffmpeg
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-i", str(ses),
                        "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def whisper(ses: Path, model: str, dil: str):
    from faster_whisper import WhisperModel
    print(f"Whisper '{model}' modeli yükleniyor (ilk seferde iner, birkaç dakika sürebilir)…", flush=True)
    m = WhisperModel(model, device="cpu", compute_type="int8")
    parcalar, _ = m.transcribe(sesi_oku(ses), language=dil, word_timestamps=True, beam_size=5)
    out = []
    for p in parcalar:
        for w in p.words or []:
            if w.word.strip():
                out.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
        print(f"  {p.start:5.1f} sn  {p.text.strip()}", flush=True)
    return out


def norm(w):
    return re.sub(r"[^\wçğıöşüâîû]", "", w.lower().replace("İ", "i").replace("I", "ı"))


def senaryoya_hizala(kel, senaryo: str):
    """Döküm kelimelerini senaryodaki doğru yazımla değiştirir; zamanlar dökümden gelir."""
    hedef = senaryo.split()
    a, b = [norm(k["w"]) for k in kel], [norm(w) for w in hedef]
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                out.append({**kel[i], "w": hedef[j]})
        elif op in ("replace", "insert"):
            if j2 == j1:
                continue
            if i2 > i1:
                s, e = kel[i1]["s"], kel[i2 - 1]["e"]
            else:  # dökümde hiç yok: komşu kelimelerin arasına sıkıştır
                s = out[-1]["e"] if out else (kel[i1]["s"] if i1 < len(kel) else 0)
                e = kel[i1]["s"] if i1 < len(kel) else s + 0.3 * (j2 - j1)
                e = max(e, s + 0.05)
            adim = (e - s) / (j2 - j1)
            for k, j in enumerate(range(j1, j2)):
                out.append({"w": hedef[j], "s": round(s + k * adim, 3), "e": round(s + (k + 1) * adim, 3)})
        # delete: senaryoda olmayan kelime (ör. "ııı") atlanır
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proje")
    ap.add_argument("--model", default="small")
    ap.add_argument("--dil", default="tr")
    ap.add_argument("--yerel", action="store_true", help="ElevenLabs anahtarı olsa da bilgisayarda dök")
    a = ap.parse_args()
    proje = Path(a.proje).expanduser().resolve()
    ses = ses_bul(proje)
    print(f"Ses: {ses.name}")

    kel = None
    key = None if a.yerel else anahtar(proje)
    if key:
        print("ElevenLabs ile dökülüyor…")
        kel = elevenlabs(ses, key)
    if kel is None:
        kel = whisper(ses, a.model, a.dil)
    if not kel:
        sys.exit("HATA: seste konuşma bulunamadı.")

    sen = proje / "senaryo.txt"
    if sen.exists() and sen.read_text(encoding="utf-8").strip():
        kel = senaryoya_hizala(kel, sen.read_text(encoding="utf-8"))
        print("Yazım senaryo.txt'ye göre düzeltildi.")

    # kelime bitişi: bir sonrakinin başını geçmesin
    for i, k in enumerate(kel):
        if i + 1 < len(kel):
            k["e"] = round(min(max(k["e"], k["s"] + 0.05), kel[i + 1]["s"]), 3)

    (proje / "kelimeler.json").write_text(json.dumps(kel, ensure_ascii=False, indent=0), encoding="utf-8")
    # okunur döküm: cümle cümle, başlangıç saniyesiyle
    satirlar, cur = [], []
    for k in kel:
        cur.append(k)
        if re.search(r"[.?!…]$", k["w"]):
            satirlar.append(cur); cur = []
    if cur:
        satirlar.append(cur)
    txt = "\n".join(f"[{c[0]['s']:6.2f} – {c[-1]['e']:6.2f}] " + " ".join(f"{k['w']}" for k in c) for c in satirlar)
    zaman = "\n".join("  " + " · ".join(f"{k['w']} {k['s']:.2f}" for k in c) for c in satirlar)
    (proje / "dokum.txt").write_text(txt + "\n\nKelime başlangıçları (sn):\n" + zaman + "\n", encoding="utf-8")
    print("\n" + txt)
    print(f"\nTamam: {len(kel)} kelime → kelimeler.json, dokum.txt")


if __name__ == "__main__":
    main()

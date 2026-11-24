# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.40", "imageio-ffmpeg>=0.5", "pillow>=10"]
# ///
"""Sahneleri kodla çizip altyazılı dikey video (1080x1920) çıkarır.

    uv run render.py <proje klasörü> --onizleme     → onizleme.jpg (her sahneden kare)
    uv run render.py <proje klasörü>                 → video.mp4

Proje klasöründe: ses dosyası, kelimeler.json (dokum.py), sahneler.json (Claude yazar),
isteğe bağlı ozel.js (özel sahneler) ve muzik.mp3 (alta kısık müzik).
"""
import argparse, asyncio, base64, json, math, random, re, shutil, struct, subprocess, sys, tempfile, wave
from pathlib import Path

import imageio_ffmpeg

FPS = 30
MOTOR = Path(__file__).resolve().parent / "motor.html"
FF = imageio_ffmpeg.get_ffmpeg_exe()
SES_UZANTI = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus", ".mp4", ".mov"}


def ses_bul(proje):
    a = sorted(p for p in proje.iterdir() if p.suffix.lower() in SES_UZANTI and not p.name.startswith(("muzik", "video", ".")))
    if not a:
        sys.exit("HATA: ses dosyası yok.")
    return a[0]


def sure_olc(yol):
    r = subprocess.run([FF, "-hide_banner", "-nostdin", "-i", str(yol)], capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        sys.exit(f"HATA: {yol.name} süresi okunamadı.")
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])


def whoosh_yaz(yol, sr=48000, sure=0.55):
    """Kodla üretilmiş yumuşak geçiş sesi: süzgeçten geçen gürültü, kesim frekansı yükselip iner."""
    random.seed(7)
    n = int(sr * sure)
    lp = 0.0
    lp2 = 0.0
    out = []
    for i in range(n):
        u = i / n
        env = math.sin(math.pi * u) ** 2
        fc = 300 + 3500 * math.sin(math.pi * u) ** 1.5
        a = 1 - math.exp(-2 * math.pi * fc / sr)
        lp += a * (random.uniform(-1, 1) - lp)
        lp2 += a * (lp - lp2)
        out.append(int(max(-1, min(1, lp2 * env * 1.4)) * 32767))
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(struct.pack(f"<{n}h", *out))


async def tarayici_ac(p):
    for deneme in ({"channel": "chrome"}, {}):
        try:
            return await p.chromium.launch(args=["--allow-file-access-from-files"], **deneme)
        except Exception:
            pass
    print("Tarayıcı motoru indiriliyor (bir kerelik, ~150 MB)…", flush=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    return await p.chromium.launch(args=["--allow-file-access-from-files"])


async def kareleri_ciz(veri, isler, hedef, ozel, paralel=3):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        tr = await tarayici_ac(p)
        sayac = {"n": 0}
        toplam = len(isler)

        async def calis(parca):
            s = await tr.new_page(viewport={"width": 1080, "height": 1920})
            hatalar = []
            s.on("pageerror", lambda e: hatalar.append(str(e)))
            await s.goto(MOTOR.as_uri())
            if ozel:
                await s.add_script_tag(content=ozel)
            bilgi = await s.evaluate("v=>init(v)", veri)
            if bilgi["bilinmeyen"]:
                raise SystemExit(f"HATA: sahneler.json'da bilinmeyen tür: {bilgi['bilinmeyen']}")
            for ad, f in parca:
                url = await s.evaluate(f"(()=>{{draw({f}/{FPS});return C.toDataURL('image/jpeg',0.93)}})()")
                (hedef / f"{ad:05d}.jpg").write_bytes(base64.b64decode(url.split(",", 1)[1]))
                sayac["n"] += 1
                if sayac["n"] % 150 == 0:
                    print(f"  kare {sayac['n']}/{toplam}", flush=True)
            if hatalar:
                raise SystemExit("HATA: çizimde hata: " + " | ".join(hatalar[:3]))

        await asyncio.gather(*[calis(isler[i::paralel]) for i in range(paralel)])
        await tr.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proje")
    ap.add_argument("--onizleme", action="store_true")
    ap.add_argument("--anlar", help="önizleme için virgüllü saniyeler (ör. 3,7.5)")
    ap.add_argument("--cikti", default="video.mp4")
    a = ap.parse_args()
    proje = Path(a.proje).expanduser().resolve()
    for g in ("kelimeler.json", "sahneler.json"):
        if not (proje / g).exists():
            sys.exit(f"HATA: {g} yok.")
    ses = ses_bul(proje)
    ses_sure = sure_olc(ses)
    sure = round(ses_sure + 1.2, 2)
    sahneler = json.loads((proje / "sahneler.json").read_text(encoding="utf-8"))
    veri = {"kelimeler": json.loads((proje / "kelimeler.json").read_text(encoding="utf-8")),
            "sahneler": sahneler, "sure": sure}
    ozel = (proje / "ozel.js").read_text(encoding="utf-8") if (proje / "ozel.js").exists() else None
    liste = sahneler["sahneler"] if isinstance(sahneler, dict) else sahneler

    if a.onizleme:
        from PIL import Image, ImageDraw
        if a.anlar:
            anlar = [float(x) for x in a.anlar.split(",")]
        else:
            anlar = []
            for sc in liste:
                bit = min(sc["bit"], ses_sure)
                anlar.append(round(sc["bas"] + (bit - sc["bas"]) * 0.75, 2))
        tmp = Path(tempfile.mkdtemp())
        asyncio.run(kareleri_ciz(veri, [(i, round(t * FPS)) for i, t in enumerate(anlar)], tmp, ozel))
        kol = 5
        sat = math.ceil(len(anlar) / kol)
        m = Image.new("RGB", (270 * kol, 500 * sat), "black")
        d = ImageDraw.Draw(m)
        for i, t in enumerate(anlar):
            m.paste(Image.open(tmp / f"{i:05d}.jpg").resize((270, 480)), ((i % kol) * 270, (i // kol) * 500))
            d.text(((i % kol) * 270 + 8, (i // kol) * 500 + 482), f"{t:.1f} sn", fill="white")
        m.save(proje / "onizleme.jpg", quality=88)
        shutil.rmtree(tmp)
        print(f"Önizleme: {proje / 'onizleme.jpg'}  ({len(anlar)} kare: {', '.join(f'{t:.1f}' for t in anlar)})")
        return

    tmp = Path(tempfile.mkdtemp())
    n = int(sure * FPS)
    print(f"{n} kare çiziliyor…", flush=True)
    asyncio.run(kareleri_ciz(veri, [(f, f) for f in range(n)], tmp, ozel))

    # ses: konuşma + geçiş sesleri + (varsa) kısık müzik
    whoosh = tmp / "whoosh.wav"
    whoosh_yaz(whoosh)
    gir = ["-i", str(ses)]
    fil = "[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11[v];"
    karis = "[v]"
    k = 2  # 0: kareler, 1: konuşma
    muzik = next((p for p in sorted(proje.iterdir()) if p.name.lower().startswith("muzik") and p.suffix.lower() in SES_UZANTI), None)
    if muzik:
        gir += ["-stream_loop", "-1", "-i", str(muzik)]
        fil += (f"[{k}:a]atrim=0:{sure},asetpts=PTS-STARTPTS,aresample=48000,loudnorm=I=-33:TP=-8,"
                f"afade=t=in:d=1.5,afade=t=out:st={max(sure - 2, 0)}:d=2[m];")
        karis += "[m]"
        k += 1
    for sc in liste[1:]:
        ms = max(int((sc["bas"] - 0.15) * 1000), 0)
        gir += ["-i", str(whoosh)]
        fil += f"[{k}:a]aresample=48000,volume=0.25,adelay={ms}|{ms}[w{k}];"
        karis += f"[w{k}]"
        k += 1
    fil += f"{karis}amix=inputs={k - 1}:normalize=0:duration=first,apad,atrim=0:{sure},loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    cikti = proje / a.cikti
    r = subprocess.run([FF, "-y", "-nostdin", "-v", "error", "-framerate", str(FPS), "-i", str(tmp / "%05d.jpg"), *gir,
                        "-filter_complex", fil, "-map", "0:v", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", str(cikti)],
                       capture_output=True, text=True, errors="replace")
    shutil.rmtree(tmp)
    if r.returncode:
        sys.exit("HATA: video birleştirilemedi:\n" + r.stderr[-1500:])
    print(f"Video hazır: {cikti}  ({sure_olc(cikti):.1f} sn, {cikti.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()

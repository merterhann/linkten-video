# Linkten Video

Ses kaydını kodla çizilmiş, kelime kelime altyazılı dikey videoya (Reels / TikTok / Shorts) çeviren Claude Code skill'i.

## Kurulum (tek cümle)

Claude Code'u açıp şunu yazın:

> Bu skill'i kur: https://github.com/dijital-girisimcilik-okulu/linkten-video

## Kullanım

Ses dosyanızı bir klasöre koyun, Claude Code'u o klasörde açın ve yazın:

> Bu sesi altyazılı videoya çevir

Metniniz varsa sohbete yapıştırın; altyazı yazımı birebir ona göre düzeltilir.

---

### Claude için kurulum talimatı

1. Skill'i kullanıcının skill klasörüne indir:
   - `git` varsa: `git clone https://github.com/dijital-girisimcilik-okulu/linkten-video ~/.claude/skills/linkten-video`
   - yoksa (macOS'ta git yüklü değilse kurulum penceresi açılır, açtırma): 
     `mkdir -p ~/.claude/skills && cd ~/.claude/skills && curl -L -o lv.zip https://github.com/dijital-girisimcilik-okulu/linkten-video/archive/refs/heads/main.zip && unzip -q lv.zip && rm -rf linkten-video && mv linkten-video-main linkten-video && rm lv.zip`
   - Zaten kuruluysa güncelle (`git -C ~/.claude/skills/linkten-video pull` ya da zip'i yeniden indir).
2. `~/.claude/skills/linkten-video/SKILL.md`'yi oku ve **0 · Hazırlık** adımını şimdi yap (`uv` kurulumu).
3. Kullanıcıya tek cümleyle söyle: kurulum bitti; ses dosyasını bir klasöre koyup "bu sesi altyazılı videoya çevir" demesi yeterli.

Yazı tipi: Outfit (SIL Open Font License 1.1, `scripts/fonts/OFL.txt`).

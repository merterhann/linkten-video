---
name: linkten-video
description: Bir ses kaydını (seslendirme, ElevenLabs sesi, podcast parçası) tamamen kodla çizilmiş, kelime kelime altyazılı dikey sosyal medya videosuna (Reels/TikTok/Shorts, 1080x1920) çevirir. Kullanıcı "bu sesi videoya çevir", "altyazılı video yap", "Linkten Video", "sesten Reels" dediğinde ya da klasöre ses atıp video istediğinde kullan.
---

# Linkten Video

Ses kaydından, hazır görüntü kullanmadan, tamamen kodla çizilmiş altyazılı dikey video yapar:
koyu zemin, üstte dev anahtar kelime, ortada konuyu anlatan animasyon, altta kelime kelime
yanan altyazı, sahne geçişlerinde yumuşak ses.

**Kullanıcı büyük ihtimalle Claude Code'u ilk kez kullanıyor.** Ona teknik terim söyleme,
komut yazdırma, soru yağdırma. Her adımda tek kısa cümleyle ne yaptığını söyle ("Sesi yazıya
döküyorum…"), işi baştan sona sen bitir. Kullanıcıyla onun dilinde konuş (genelde Türkçe).

Betikler bu skill'in `scripts/` klasöründedir. Aşağıda `$SKILL` bu klasörü (SKILL.md'nin
bulunduğu klasör), `$PROJE` kullanıcının ses dosyasının durduğu klasörü gösterir. Kabuk
değişkenleri bir komuttan ötekine taşınmaz: her komutta **tam yolu** yaz. Yollar boşluk ve
Türkçe harf içerebilir: her zaman tırnak içinde yaz.

## 0 · Hazırlık (yalnız ilk seferde)

Tek gereken araç `uv`'dur (Python'u ve gereken her şeyi kendisi kurar). `uv --version` çalışmıyorsa kur:

- macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Kurulumdan sonra bu oturumda `uv` bulunamazsa tam yolunu kullan: macOS/Linux `~/.local/bin/uv`,
Windows `%USERPROFILE%\.local\bin\uv.exe` (Git Bash'te `~/.local/bin/uv.exe`). Başka bir şey
(ffmpeg, Python, Chrome) kurmana gerek yok; betikler ilk çalışmada eksiklerini kendisi indirir
(ilk sefer birkaç dakika sürebilir, kullanıcıya bunu söyle).

## 1 · Proje klasörü

- Ses dosyası (mp3, wav, m4a…) hangi klasördeyse proje klasörü odur. Ses başka yerdeyse
  (İndirilenler gibi) çalışma klasöründe adı konuya uygun yeni bir klasör aç ve sesi oraya kopyala.
- Klasörde **yalnız bir ses dosyası** olsun (alta müzik istenirse adı `muzik.mp3` olur).
- Kullanıcının metni/senaryosu varsa (sohbete yapıştırdıysa ya da dosyası varsa) `senaryo.txt`
  olarak klasöre koy: döküm yazımı bire bir bu metne göre düzeltilir. Yoksa sorun değil.

## 2 · Sesi yazıya dök

```bash
uv run "$SKILL/scripts/dokum.py" "$PROJE"
```

Çıktı: `kelimeler.json` ve `dokum.txt` (cümleler + her kelimenin başlangıç saniyesi).
`kelimeler.json` düz bir listedir: `[{"w": "Yoğun", "s": 0.0, "e": 0.46}, …]`
(`w` kelime, `s` başlangıç, `e` bitiş saniyesi).

**`dokum.txt`'yi baştan sona oku ve düzelt; bu adımı atlama.** Bilgisayardaki döküm Türkçede
sık hata yapar (ör. "pizanlayın" → planlayın, "Kızgara'da" → ızgarada, "şevkatli" → şefkatli,
ek hataları: "üretimi" → üretime). Altyazıda hata en çok göze batan şeydir. Cümleyi anlamından
düzelt; soru cümlesinin sonunda `?` olsun. Düzeltmeyi `kelimeler.json`'da yalnız `w` alanında
yap; `s`/`e` saniyelerine dokunma, kelime ekleme/silme. Senaryo verildiyse bu iş zaten yapılmıştır,
yine de göz at. Kullanıcı metin vermediyse metin isteme, kendin düzelt.

Not: Kullanıcının ElevenLabs API anahtarı varsa ve daha isabetli döküm isterse `$PROJE/.env`
içine `ELEVENLABS_API_KEY=...` yazılır; betik otomatik ElevenLabs'i kullanır (çok az kredi harcar).
Varsayılan yol ücretsizdir; anahtarı kendiliğinden isteme.

## 3 · Sahne planı: `sahneler.json`

Konuşmayı anlamına göre sahnelere böl ve `$PROJE/sahneler.json` yaz. Bu adım videonun
kalitesini belirler; asıl yaratıcı iş burada.

```json
{
  "sahneler": [
    {"bas": 0,   "bit": 5.0,  "tur": "dalga",     "kelime": [[0, "KAYGI"], [3.5, "ELLER"]], "ayar": {"sakinles": 3.6}},
    {"bas": 5.0, "bit": 12.1, "tur": "karsitlik", "kelime": [[5.0, "SANDIĞIMIZ"], [9.4, "TAM TERSİ"]],
     "ayar": {"ust": "kaygı", "alt": "yaratıcılık", "ok": 6.2, "ciz": 7.3, "degis": 9.6, "ciz2": 11.0}},
    {"bas": 12.1, "bit": 16, "tur": "yutma", "kelime": [[12.1, "YARATICILIK"]],
     "ayar": {"buyuk": "yaratıcılık", "kucuk": "kaygı", "an": 12.9}}
  ]
}
```

Kurallar:
- **Sahne = genelde bir cümle**, 2,5–6 saniye. Sahneler boşluksuz art arda gelir
  (bir sahnenin `bit`'i sonrakinin `bas`'ı). İlki `0`'da başlar; sonuncusu videonun sonuna kendiliğinden uzar.
- Sahne sınırını bir cümlenin ilk kelimesinin saniyesinden ~0,15 sn önceye koy.
- **`kelime`**: üstte duran dev anahtar kelime(ler), `[saniye, "METİN"]`. BÜYÜK HARF, 1–2 kelime,
  o anda söylenen fikrin özü. İkinci kelime verilirse o saniyede birincinin **yerine geçer**.
  Bir sahnede en çok 2; hiç istemiyorsan `"kelime": []` (ya da alanı yazma). Türkçe büyük harfe
  dikkat: i → İ, ı → I.
- Animasyondaki her an (`ok`, `ciz`, `an`, `maddeler`'deki saniyeler…) **o kelimenin söylendiği
  saniyeye** denk gelsin (`dokum.txt`'ten bak). Görüntü sesle aynı anda değişmeli.
- Çeşitlilik: aynı türü art arda kullanma. Anlamı en iyi gösteren türü seç.
- Kısa sorular ya da vurucu kapanış cümlesi için `soru` türü çok etkili (ekranın ortasında dev yazı).

### Sahne türleri

| tur | ne gösterir | ayar |
|--|--|--|
| `dalga` | dağınık, gergin çizgi yumuşak dalgaya döner (kaos → sakinlik, stres → huzur) | `sakinles`: sakinleşme anı |
| `karsitlik` | üstte A, ok, altta B; B'nin üstü çizilir, sonra yer değiştirirler (yanılgı → gerçek, A mı B mi) | `ust`, `alt` (metin); `ok`, `ciz`, `degis`, `ciz2` (anlar, istemediğini koyma) |
| `yutma` | büyüyen çember titreyen küçük noktayı yutar (bir şey ötekini bastırır) | `buyuk`, `kucuk` (metin); `an` |
| `liste` | kart içinde tik alarak gelen maddeler (adımlar, öneriler) | `maddeler`: `[[an, "metin"], …]` en çok 4 |
| `emoji` | 1–3 dev emoji zıplayarak gelir, altında kısa yazı (somut nesne/eylem: yemek, para, telefon…) | `ogeler`: `[[an, "🍳", "pişir"], …]` |
| `sayi` | dev sayaç sayarak yükselir (istatistik, yüzde, para) | `den`, `e`, `onek`, `sonek`, `an`: `[başla, bitir]`, `yazi`. Türkçede yüzde başa gelir: `"onek": "%"` |
| `metin` | ortada dev cümle, `*yıldızlı*` kelimeler vurgu renginde (alıntı, ana fikir) | `yazi`, `an` |
| `soru` | o sahnede söylenen sözler ortada dev yazıyla kelime kelime gelir; altyazı gizlenir | yok |
| `halkalar` | merkezden yayılan dalgalar (etki, yayılma, harekete geç) | `yazi`, `yazi_an` |
| `dongu` | dönen kesik çizgili çember, nokta "kaçış" anında kopup çıkar (kısır döngüden çıkmak) | `yazi`, `kacis` |
| `nabiz` | kalp atışı çizgisi; hızlıysa kırmızı, yavaşladıkça yeşil (panik, heyecan, sakinleşme) | `hiz`: `[baş, son]` saniyedeki atım (1 sakin … 3,2 panik; sabit için ikisi aynı), `degisim`: `[başla, bitir]` hızın değiştiği aralık (yoksa sahne boyunca), `yazi`, `yazi_an` |
| `nefes` | yavaşça büyüyüp küçülen parlayan çember (nefes, sakinlik, şefkat) | `yazi` (yoksa "nefes al / nefes ver") |
| `bloklar` | bloklar sırayla yerine oturup piramit kurar (3+2+1); altta bir yazının üstü çizilir (inşa etmek, birikim) | `anlar`: her saniye bir blok, en çok 6; isteğe bağlı `ciz_yazi`, `yazi_an`, `ciz_an` |
| `ozel` | kütüphanede uygun tür yoksa kendi çizdiğin sahne (aşağıda) | `fonksiyon` |

Renkleri değiştirmek için en üste `"renkler": {"zemin1": "#13261D", "zemin2": "#0B1711",
"zemin3": "#050907", "yazi": "#EFE9DD", "vurgu": "#F2B35B", "sakin": "#7FC8A0", "gergin": "#E0786A"}`
(yalnız değişeni yazman yeter). Kullanıcı istemedikçe varsayılanı kullan.

### Özel sahne (`ozel.js`)

Konu somut bir şey anlatıyorsa (ızgara, tahta, grafik, harita) ve kütüphanede karşılığı yoksa
`$PROJE/ozel.js` yaz:

```js
window.OZEL = window.OZEL || {};
OZEL.izgara = (t, a, sc, A) => {        // t: saniye, a: görünürlük 0–1, sc: sahne, A: araçlar
  const {X, CX, CY, eo, lin, stroke} = A; const R = A.R();
  const d = eo(lin(t, sc.bas, sc.bas + 0.7));          // 0 → 1 çizilme
  X.beginPath(); X.roundRect(CX - 300, CY - 150, 600 * d, 300, 40);
  stroke(R.yazi, 6); X.stroke();
};
```
ve sahnede `{"tur": "ozel", "ayar": {"fonksiyon": "izgara"}}`. `X` 1080x1920 tuvalin 2D
çizim bağlamıdır; animasyonun alanı ortası (`CX=540, CY=900`), yaklaşık y 600–1250 arası.
Üstteki kelime (y≈470) ve altyazı (y≈1490) motor tarafından çizilir, o bölgelere girme.
Araçlar: `cl, lin, eo, eio, back, mix, hexa, rnd, stroke, label, fitFont, pill`. Her şey
yalnız `t`'ye bağlı olsun (rastgelelik için `rnd(i)`), yoksa kareler titrer.

## 4 · Önizle, bak, düzelt

```bash
uv run "$SKILL/scripts/render.py" "$PROJE" --onizleme
```

`$PROJE/onizleme.jpg`'yi **mutlaka aç ve bak**: her sahnenin dörtte üçündeki an, altında
saniyesiyle. Sahnenin başına ya da ilk anahtar kelimesine bakmak için `--anlar 3.2,7.5`. Kontrol et:
- Yazılar okunuyor mu, taşan/üst üste binen var mı?
- Animasyon o cümlenin anlamını anlatıyor mu?
- Anahtar kelimeler doğru ve Türkçe harfleri düzgün mü?

Sorun varsa `sahneler.json`'u düzeltip önizlemeyi tekrarla.

## 5 · Videoyu çıkar

```bash
uv run "$SKILL/scripts/render.py" "$PROJE"
```

Çıktı `$PROJE/video.mp4` (1080x1920, 30 fps, ses seviyesi sosyal medyaya göre ayarlı). Bir
dakikalık video normal bir bilgisayarda 1–3 dakika sürer. Klasörde `muzik.mp3` varsa alta kısık
çalar; yoksa yalnız konuşma ve geçiş sesleri olur.

Bitince kullanıcıya kısa söyle: videonun yeri, süresi ve tek cümleyle neleri değiştirebileceği
("altyazıyı büyüt", "rengi mavi yap", "şu sahnede emoji olsun", "alta müzik ekle: muzik.mp3'ü
klasöre at" gibi). Klasörü açmayı teklif et (macOS `open "$PROJE"`, Windows `explorer`).

## Revize

Kullanıcı düz cümleyle ister ("ikinci sahne sıkıcı", "kelimeler çok büyük"):
- İçerik/sahne değişikliği → `sahneler.json` (ya da `ozel.js`) → önizleme → video.
- Renk → `renkler`.
- Yazım → `kelimeler.json`'da `w`.
- Tasarımın kendisi (yazı boyutu, konum, yazı tipi) → bu skill'in `scripts/motor.html`'si; değiştirmeden
  önce kopyala ya da yalnız istenen değeri değiştir.

## Sık takılmalar

- **`uv` bulunamadı** → 0. adımdaki tam yolu kullan ya da kullanıcıya Claude Code'u kapatıp açmasını söyle.
- **İlk döküm uzun sürüyor** → model iniyor (~500 MB), normal; bir kere olur.
- **Tarayıcı açılamadı** → betik kendi tarayıcısını indirir; internet bağlantısını kontrol et.
- **Bilgisayar yavaş** → `render.py` 3 kare paralel çizer; yine de ağırsa diğer programları kapat.

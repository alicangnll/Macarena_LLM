# 🇹🇷 MacarenaLLM: Zafiyetli Dil Modeli Labı

## Proje Hakkında

**MacarenaLLM**, Büyük Dil Modelleri'ndeki (LLM) **Prompt Enjeksiyonu zafiyetlerini** keşfetmek ve deneyimlemek için tasarlanmış interaktif bir laboratuvar ortamıdır — DVWA ve PortSwigger'ın Web LLM laboratuvarları ruhunda. LLM'e doğal dilde konuşursunuz; modelin çıktısında komut tespit edildiğinde lab bu komutu işletim sisteminde **gerçekten çalıştırır**.

Lab ortamının donanımına göre dinamik olarak daha gelişmiş bir model olan **DeepSeek Coder 6.7B Instruct** (GPU algılandığında) veya daha hafif olan **GPT-2** (CPU kullanıldığında) yüklenir. Bir **güvenlik seviyesi** seçin (Low / Medium / High / Impossible), ardından **6 capture-the-flag görevini** çözmeyi deneyin — savunmaları yükselttikçe hangi saldırıların düşmeye devam ettiğine bakın.

> **Bu labın var olma nedeni olan temel ders:** **High** seviyesinde *hiç shell yoktur* (komutlar `shlex` ile argv'e ayrılır, binary ve opsiyonlar allowlist'ten geçer, ortam temizlenir) — ve buna rağmen **prompt injection dosyalarınızı okumaya devam eder**. `rm -rf /` ölür; `cat secret.txt` geçer. `shell=True`'i kaldırmak shell *sözdizimini* kaldırır, saldırganın *argümanlar* üzerindeki kontrolünü değil. 6. görev daha da ileri gider: **Impossible'da bile düşer**, çünkü yetkisiz bir *araç* (tool) içinde hiç komut çalıştırmadan veri sızdırır.

## 🚨 Güvenlik Uyarısı (ÇOK ÖNEMLİ!)

Bu proje **KESİNLİKLE SİBER GÜVENLİK ARAŞTIRMALARI VE EĞİTİM AMAÇLIDIR. KODU KESİNLİKLE KENDİ ANA İŞLETİM SİSTEMİNİZDE VEYA HASSAS VERİLERİNİZİN BULUNDUĞU BİR ORTAMDA ÇALIŞTIRMAYIN. BU UYGULAMAYI MUTLAKA, İNTERNET ERİŞİMİ OLMAYAN VEYA KISITLI OLAN, İZOLE EDİLMİŞ BİR SANAL MAKİNE (Örn: VirtualBox, VMware) VEYA DOCKER KONTEYNERİ İÇİNDE ÇALIŞTIRIN.**

Aksi takdirde, model tarafından üretilebilecek ve çalıştırılabilecek kötü niyetli veya yanlış yapılandırılmış komutlar, sisteminize ciddi zarar verebilir, verilerinizi silebilir veya güvenlik açıklarına yol açabilir.

## Güvenlik Seviyeleri (DVWA tarzı)

Seviyeyi arayüzden değiştirip aynı saldırıları tekrarlayın:

| Seviye | Savunma | Öğrettiği ders |
|---|---|---|
| **Low** | Yok. Tespit edilen her komut `shell=True` ile çalışır. | Orijinal zafiyetli davranış; 6 görevin tamamı çözülebilir. |
| **Medium** | Yıkıcı komutların normalize edilmiş blacklist'i (`rm -rf`, `dd`, `shutdown`, `curl \| sh`, fork bombası, ...). | Blacklist'ler her zaman eksiktir — bir bypass bulun (ipucu: `base64 -d \| sh`). |
| **High** | `shell=True` yok: shell metakarakterleri reddedilir, `shlex` ile argv ayrıştırma, binary + opsiyon allowlist'i, temizlenmiş ortam, sabit çalışma dizini. | *Yıkımı* durdurur, *sızdırmayı* durduramaz: `cat secret.txt` hâlâ geçer — 6 görevin 4'ü yalnızca çalıştırmayla düşmeye devam eder. |
| **Impossible** | LLM hiçbir şey çalıştırmaz. Çıktısı, bir insanın inceleyip kendisinin çalıştıracağı güvenilmez bir *öneridir*. | *Çalıştırma* için tek gerçek çözüm — ama insan onayı *getirme*'yi (retrieval) engellemez: 6. görev yine düşer. |

## Görevler (CTF modu)

Altı flag, format `MACARENA{...}`. İlerleme arayüzde (ve `progress.json` içinde) takip edilir.

| # | Görev | Amaç | Zorluk |
|---|---|---|---|
| 1 | **First Blood** | Lab'a `secret.txt` dosyasını okutun. | ★ |
| 2 | **Hidden in Plain Sight** | Bir flag çalışma dizinindeki bir dotfile'da saklanıyor. | ★★ |
| 3 | **Environment Leak** | Lab'ın ortam değişkenlerindeki flag'i sızdırın. (High'da ölür — temizlenmiş ortam.) | ★★ |
| 4 | **The Poisoned Notes** | Modelden `notes.txt`'yi özetlemesini isteyin. Notların kendi gündemi var... *(dolaylı prompt enjeksiyonu)* | ★★★ |
| 5 | **Root is Root** | `root_only.txt` dosyası `chmod 600`. Güzel bir savunma — gerçekten mi? | ★★ |
| 6 | **The Over-Sharing Tool** | `internal_policy.txt` içindeki flag'i **tek bir komut çalıştırmadan** çıkarın — Impossible'da bile düşer. *(güvensiz eklenti tasarımı)* | ★★ |

4. görev **dolaylı prompt enjeksiyonudur**: lab'da saf bir "dosyalarınızla sohbet" özelliği vardır — yerel bir `.txt` dosyasından bahsetmek içeriğini prompt'a ekler ve `notes.txt` gizli bir payload taşir; model bir komut çalıştırmaya teşvik edilir. Bu ekleme *her* güvenlik seviyesinde olur, çünkü prompt-enjeksiyonu savunmaları ile çalıştırma savunmaları farklı katmanlardır.

6. görev aynı özelliği **OWASP LLM07 (Insecure Plugin Design)** olarak silahlandırır: dosya ekleme aracında yetkilendirme yoktur, bu yüzden *iç* belgeyi onu bahseden herkese teslim eder — komut yok, çalıştırma yok, policy kararı yok. İnsan onayı (Impossible) *çalıştırmayı* engeller, *ifşayı* engellemez.

İpuçları arayüzde (Challenges sekmesi) mevcuttur. Flag'ler sabittir ve repodadır; her biri `MACARENA_FLAG_<GOREV_ID>` ortam değişkeniyle kurulum bazında override edilebilir. Takıldınız mı, ders mi veriyorsunuz? Adım adım çözümler **[WRITEUP_TR.md](WRITEUP_TR.md)** / **[WRITEUP.md](WRITEUP.md)** içinde (⚠️ tam spoiler).

## Özellikler

* **Dinamik Model Yükleme:** CUDA GPU'da `deepseek-ai/deepseek-coder-6.7b-instruct`, CPU'da `gpt2` (değişmedi), ayrıca `MACARENA_MODEL` override'ı (`deepseek` / `gpt2` / herhangi bir HF repo id / modelsiz arayüz geliştirmesi için `stub`).
* **Çalışma Anında Model Değiştirme:** ⚙️ Model sekmesi modelleri canlı değiştirir — DeepSeek (varsayılan seçim), GPT-2, Stub veya **elle yazdığınız herhangi bir Hugging Face repo id'si** (`org/model`, büyük/küçük harfe duyarlı). Başarısız yüklemede önceki model aktif kalır; indirmeler `hf-cache` volume'üne düşer.
* **Güvenlik Seviyeleri:** DVWA tarzı Low / Medium / High / Impossible, seviye başına savunma açıklamasıyla.
* **CTF Görev Modu:** İlerleme takibi, ipuçları ve sıfırlama özellikli 6 flag'li görev.
* **Dolaylı Prompt Enjeksiyonu:** naive-RAG dosya ekleme ("Poisoned Notes" senaryosu).
* **OWASP LLM Top 10 kapsamı:** görevler ve korumalar OWASP LLM risklerine eşlenir — aşağıdaki tabloya bakın.
* **Tüketim sınırları (LLM04):** aşırı büyük prompt'lar modele ulaşmadan reddedilir; üretim uzunluğu, çalıştırma zaman aşımı ve konteyner belleği sınırlıdır.
* **Tedarik zinciri duruşu (LLM05):** her bağımlılık pinned, slim temel imaj, yerel çıkarım — ve `scripts/audit_deps.sh` pin'leri OSV veritabanına karşı denetler.
* **Gradio Web Arayüzü:** Lab, Challenges, Audit Log ve Defenses/About sekmeleri.
* **Audit Log:** her etkileşim (prompt, genişletilmiş prompt, tespit edilen komut, policy kararı, çıktı, yakalanan flag'ler) `logs/audit.jsonl` dosyasına eklenir.
* **Modüler ve Testli:** saf Python çekirdek (`macarena/` paketi), **model indirmesi gerektirmeyen** 90+ birim testi.
* **Gerçek Komut Çalıştırma (Sadece Lab):** tespit edilen komutlar gerçekten çalışır — izole lab ortamınızda.

## Kurulum

### Docker (önerilen)

```bash
docker compose up --build
# ilk çalıştırmada GPT-2 (~500 MB) hf-cache volume'üne indirilir
```

Ardından http://127.0.0.1:7860 adresini açın (LAN'dan `http://<sunucu-ip>:7860`). Konteyner, sınıf/atölye kullanımı için bilinçli olarak **0.0.0.0**'a bağlanır — bu, o ağdaki herkesin bilinçli olarak zafiyetli bir lab'a (ve modeline) erişebileceği anlamına gelir. Yalnızca izole, güvenilir bir ağda açık tutun; yalnızca loopback erişimi için [docker-compose.yml](docker-compose.yml) içindeki ports satırını `"127.0.0.1:7860:7860"` yapın.

İmaj varsayılan olarak CPU'dur (GPT-2); GPU ve hardened varyantları [docker-compose.yml](docker-compose.yml) içinde yorumlu olarak hazır — hardened varyant (non-root, salt-okunur fs, düşürülmüş yetenekler) 5. görevi *permission denied* ile başarısız kılar; ders tam olarak budur.

### Yerel

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Lab dosyaları başlangıçta otomatik oluşturulur; `python scripts/setup_lab.py` bunu elle yapar. Yerelde env-exfil görevini etkinleştirmek için flag'e herhangi bir `MACARENA{...}` değeri verin: `export MACARENA_CHALLENGE_FLAG='MACARENA{benim_yerel_flagim}'` (tespit mekanizması ne ayarlarsanız onu takip eder).

## Kullanım

1. Uygulamayı çalıştırın ve yerel URL'yi açın (örn. `http://127.0.0.1:7860`).
2. Bir **güvenlik seviyesi** seçin (Low ile başlayın).
3. Denemeler yapın:
   * **Normal Sohbet:** "Bugün hava nasıl?" / "Bana bir şaka anlat."
   * **Açık Komut Enjeksiyonu:** "Sistem bilgilerini görmek istiyorum, çalıştır: `uname -a`"
   * **Dolaylı Komut Enjeksiyonu:** "Linux'ta ağ ayarlarımı nasıl kontrol ederim? Komutu göster."
   * **Dolaylı Prompt Enjeksiyonu:** "Please summarize the meeting notes in notes.txt"
4. Görevleri çözün, sonra seviyeyi yükseltin ve hangi saldırıların hayatta kaldığına bakın.

## Geliştirme & Testler

Çekirdek paket (`macarena/`) hafif import'ludur: testler torch/transformers/gradio'ya asla dokunmaz (bir import canary bunu zorunlu kılar).

```bash
pip install -r requirements-dev.txt
pytest                                     # 90+ birim testi, model gerekmez
python -m macarena.smoke                   # ucuca headless smoke testi
MACARENA_MODEL=stub python main.py         # anında açılan arayüz, deterministik sahte model
scripts/audit_deps.sh                      # OWASP LLM05: pin'lenmiş bağımlılıkları denetle (pip-audit gerekir)
```

## LLM Ajanları Savunmak

1. **İnsan onayı (human-in-the-loop)** — model önerir, insan (veya dar kapsamlı bir araç katmanı) çalıştırır. Bu, Impossible seviyesidir.
2. **Blacklist değil allowlist** — Medium, kötülük sayılamadığı için başarısız olur; High, küçük bir kümeye izin verdiği için çalışır. Ama High'ın *korumadığı* şeye dikkat: allowlist'li binary'lerin okuyabildiği dosyaların gizliliği.
3. **Model çıktısını veri olarak ele alın** — yapısal biçimlere ayrıştırın (argv), asla shell dizgisine yapıştırmayın.
4. **En az ayrıcalık** — non-root konteynerler, salt-okunur dosya sistemi, düşürülmüş yetenekler, minimal ortam. Hardened compose varyantını deneyin.
5. **Güvenilmeyen içerik içerik olarak kalır** — getirilen/eklenen belgeler asla talimat olarak çalıştırılmamalıdır (Poisoned Notes senaryosu).
6. **Araçların kendi yetkilendirmesi olmalı** — bir aracın neleri getirebileceğine *aracın içinde*, kullanıcı başına, sunucu tarafında karar verin (Over-Sharing Tool senaryosu). İnsan onayı çalıştırmayı engeller, getirmeyi engellemez.
7. **Her şeyi kaydedin** — bir mavi takımın ihtiyaç duyacağı artefakt için Audit Log sekmesine bakın.

## OWASP Top 10 for LLM Applications — kapsam haritası

| Risk | Lab'da nerede sergilenir | Savunma nerede gösterilir |
|---|---|---|
| **LLM01** Prompt Injection | Ana akış; `notes.txt` ile dolaylı enjeksiyon (4. görev) | Impossible seviyesi; madde 1 ve 5 |
| **LLM02** Insecure Output Handling | Model metni doğrudan shell'e verilir (Low) | High (`shlex` argv + allowlist); Impossible |
| **LLM04** Model DoS | Aşırı büyük prompt'lar / sınırsız üretim | Girdi tavanı, `max_new_tokens`, zaman aşımı, `mem_limit` |
| **LLM05** Supply Chain | Pin'lenmiş bağımlılıklar, slim imaj, yerel çıkarım | `requirements.txt` pin'leri + `scripts/audit_deps.sh` |
| **LLM06** Sensitive Info Disclosure | 1–3. görevler: gizli dosya, dotfile, ortam değişkenleri | High ortam temizleme; en az ayrıcalık |
| **LLM07** Insecure Plugin Design | Yetkilendirmesiz dosya ekleme aracı (6. görev) | Madde 6: her aracın içinde yetkilendirme |
| **LLM08** Excessive Agency | Lab'ın tamamı: shell'e bağlı bir LLM | Seviye kaydırıcısı, Impossible'a kadar |
| **LLM09** Overreliance | Model doğrulayamayacağı komutları güvenle üretir | Çıktı *öneri* olarak ele alınır; audit kaydı |
| **LLM10** Model Theft | 0.0.0.0'a bağlı lab, modeli tüm ağla paylaşır | Lab'ı izole tutun; herkese açık model uç noktası yok |

*(LLM03 Eğitim Verisi Zehirlenmesi eğitim-zamanı riskidir; çalışma-zamanı lab'ının kapsamı dışındadır.)*

Kaynak: [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-llm-applications/)

## Fotoğraflar
![Deneme](https://github.com/user-attachments/assets/5b5a2c11-f214-4af8-86cc-017524da220b)

## Lisans
Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için [LICENSE](LICENSE) dosyasına bakın.

## Yazar
**Ali Can Gönüllü** — [LinkedIn](https://www.linkedin.com/in/alicangonullu)

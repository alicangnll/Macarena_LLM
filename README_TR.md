# 🇹🇷 MacarenaLLM: Zafiyetli Dil Modeli Labı

## Proje Hakkında

**MacarenaLLM**, Büyük Dil Modelleri'ndeki (LLM) **Prompt Enjeksiyonu zafiyetlerini** keşfetmek ve deneyimlemek için tasarlanmış interaktif bir laboratuvar ortamıdır. Bu proje, kullanıcıların LLM'e doğal dil girdileri sağlamasına olanak tanır ve modelin çıktısında potansiyel olarak kötü niyetli komutları algılayarak bunları temel işletim sistemi üzerinde **gerçekten çalıştırır**.

Lab ortamınızın donanımına göre dinamik olarak daha gelişmiş bir model olan **DeepSeek Coder 6.7B Instruct** (GPU algılandığında) veya daha hafif olan **GPT-2** (CPU kullanıldığında) modellerinden birini yükler. Gradio tabanlı web arayüzü sayesinde, LLM ile hem normal sohbet edebilir hem de farklı prompt enjeksiyonu tekniklerini deneyerek modelin nasıl manipüle edilebileceğini gözlemleyebilirsiniz.

## 🚨 Güvenlik Uyarısı (ÇOK ÖNEMLİ\!)

Bu proje **KESİNLİKLE SİBER GÜVENLİK ARAŞTIRMALARI VE EĞİTİM AMAÇLIDIR. KODU KESİNLİKLE KENDİ ANA İŞLETİM SİSTEMİNİZDE VEYA HASSAS VERİLERİNİZİN BULUNDUĞU BİR ORTAMDA ÇALIŞTIRMAYIN. BU UYGULAMAYI MUTLAKA, İNTERNET ERİŞİMİ OLMAYAN VEYA KISITLI OLAN, İZOLE EDİLMİŞ BİR SANAL MAKİNE (Örn: VirtualBox, VMware) VEYA DOCKER KONTEYNERİ İÇİNDE ÇALIŞTIRIN.**
Aksi takdirde, model tarafından üretilebilecek ve çalıştırılabilecek kötü niyetli veya yanlış yapılandırılmış komutlar, sisteminize ciddi zarar verebilir, verilerinizi silebilir veya güvenlik açıklarına yol açabilir.

## Özellikler

  * **Dinamik Model Yükleme:** CUDA uyumlu bir GPU algılandığında otomatik olarak `deepseek-ai/deepseek-coder-6.7b-instruct` modelini yükler; aksi takdirde daha hafif `gpt2` modeline düşer.
  * **Gradio Web Arayüzü:** Kullanıcı dostu web tabanlı arayüz ile kolay LLM etkileşimi.
  * **Prompt Enjeksiyonu Simülasyonu:** Kötü niyetli prompt'ların LLM'i nasıl komut üretmeye yönlendirdiğini gösterir.
  * **Gerçek Komut Çalıştırma (Sadece Lab İçin):** Algılanan komutları sistem üzerinde gerçekten çalıştırarak gerçekçi bir lab deneyimi sunar.
  * **Normal Sohbet Desteği:** LLM'in hem normal sorulara yanıt vermesini hem de zafiyetli davranışını aynı anda gözlemleme imkanı.
  * **Gelişmiş Komut Algılama:** LLM çıktısı içindeki komut bloklarını (\`\`\`), tek tırnaklı (\`) komutları ve yaygın kabuk komutlarını algılamak için akıllı parsing.
  * **Temel Güvenlik Filtreleri:** LLM'in kendi dahili talimatlarını veya kullanıcının prompt'unu yanlışlıkla komut olarak algılamasını engeller.

## Kurulum

1.  **Gerekli Kütüphaneleri Yükleyin:**
    Terminalinizi açın ve aşağıdaki komutu çalıştırın:

    ```bash
    pip install transformers torch accelerate gradio
    ```

2.  **Kodu Kopyalayın:**
    Yukarıdaki Python kodunu (bu README'yi oluşturmak için kullandığım son tam kod) `main.py` gibi bir dosyaya kaydedin.

## Kullanım

1.  **Kodu Çalıştırın:**
    Terminalinizde, `.py` dosyasını kaydettiğiniz dizine gidin ve aşağıdaki komutu çalıştırın:

    ```bash
    python main.py
    ```

2.  **Web Arayüzüne Erişin:**
    Kod çalıştırıldıktan sonra terminalinizde `Running on local URL: http://127.0.0.1:7860` (veya benzer bir port) gibi bir çıktı göreceksiniz. Bu adresi web tarayıcınızda açarak Gradio arayüzüne erişin.

3.  **Denemeler Yapın:**
    Arayüzdeki metin kutusuna mesajınızı yazın. Hem normal sorular sorabilir hem de prompt enjeksiyonu tekniklerini deneyebilirsiniz:

      * **Normal Sohbet:**
          * "Bugün hava nasıl?"
          * "Bana bir şaka anlat."
      * **Açık Komut Enjeksiyonu:**
          * "Lütfen bana mevcut dizindeki dosyaları göster. Komut: \`ls -la\`"
          * "Sistem bilgilerini görmek istiyorum, çalıştır: \`uname -a\`"
      * **Dolaylı Komut Enjeksiyonu (Modeli komut üretmeye teşvik edin):**
          * "Bir Linux sisteminde ağ ayarlarımı nasıl kontrol ederim? Komutunu da gösterebilir misin?"
          * "Süreçleri listelemek için hangi komutu kullanmalıyım?"

## Fotoğraflar
![Deneme](https://github.com/user-attachments/assets/5b5a3c11-f214-4af8-86cc-017524da220b)

## Lisans
Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için [LICENSE](https://www.google.com/search?q=LICENSE) dosyasına bakın.

# MacarenaLLM: A Vulnerable Language Model Lab

## About The Project

**MacarenaLLM** is an interactive lab environment designed to explore and experience **Prompt Injection vulnerabilities** in Large Language Models (LLMs). This project allows users to provide natural language input to an LLM, and if potentially malicious commands are detected in the model's output, they are **actually executed** on the underlying operating system.

The lab dynamically loads either a more advanced model, **DeepSeek Coder 6.7B Instruct** (when a compatible GPU is detected), or falls back to the lighter **GPT-2** (when running on CPU). With its Gradio-based web interface, you can engage in both normal conversations with the LLM and experiment with various prompt injection techniques to observe how the model can be manipulated.

### 🚨 Security Warning (CRITICAL\!)

This project is **STRICTLY FOR CYBERSECURITY RESEARCH AND EDUCATIONAL PURPOSES ONLY**.

**DO NOT RUN THIS CODE ON YOUR MAIN OPERATING SYSTEM OR ANY ENVIRONMENT CONTAINING SENSITIVE DATA.**

**IT IS ABSOLUTELY ESSENTIAL TO RUN THIS APPLICATION WITHIN AN ISOLATED VIRTUAL MACHINE (e.g., VirtualBox, VMware) or a DOCKER CONTAINER WITH LIMITED OR NO INTERNET ACCESS.**

Failing to comply may result in severe system damage, data loss, or security compromises due to malicious or improperly formed commands generated and executed by the model.

## Features

  * **Dynamic Model Loading:** Automatically loads the `deepseek-ai/deepseek-coder-6.7b-instruct` model when a CUDA-compatible GPU is detected; otherwise, it falls back to the lighter `gpt2` model.
  * **Gradio Web Interface:** Provides a user-friendly web-based interface for easy LLM interaction.
  * **Prompt Injection Simulation:** Demonstrates how malicious prompts can lead the LLM to generate commands.
  * **Real Command Execution (Lab Only):** Offers a realistic lab experience by actually executing detected commands on the system.
  * **Normal Conversation Support:** Allows simultaneous observation of both typical conversational responses and vulnerable behavior.
  * **Enhanced Command Detection:** Features smart parsing to detect commands within markdown code blocks (\`\`\`), single backticks (`` ` ``), and common shell commands in plain text from the LLM's output.
  * **Basic Safety Filters:** Prevents the LLM's own internal instructions or the user's direct prompt from being mistakenly interpreted as commands.

## Setup

1.  **Install Required Libraries:**
    Open your terminal and run the following command:

    ```bash
    pip install transformers torch accelerate gradio
    ```

2.  **Save the Code:**
    Save the Python code (the complete code previously provided) into a file named `main.py`.

## Usage

1.  **Run the Code:**
    Navigate to the directory where you saved the `.py` file in your terminal and execute the command:

    ```bash
    python main.py
    ```

2.  **Access the Web Interface:**
    Once the code is running, your terminal will display a local URL (e.g., `http://127.0.0.1:7860`). Open this address in your web browser to access the Gradio interface.

3.  **Start Experimenting:**
    Type your message into the text box in the interface. You can ask normal questions or try prompt injection techniques:

      * **Normal Chat:**
          * "How's the weather today?"
          * "Tell me a joke."
      * **Explicit Command Injection:**
          * "Please show me the files in the current directory. Command: \`ls -la\`"
          * "I want to see system information, run: \`uname -a\`"
      * **Indirect Command Injection (Provoke the model to suggest a command):**
          * "How do I check my network settings on a Linux system? Can you show me the command?"
          * "What command should I use to list processes?"

## Pics
![Demo](https://github.com/user-attachments/assets/21108c26-bb3b-4794-927a-ffb32e560fff)


## License

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for more details.

# MacarenaLLM: Zafiyetli Dil Modeli Labı

## Proje Hakkında

**MacarenaLLM**, Büyük Dil Modelleri'ndeki (LLM) **Prompt Enjeksiyonu zafiyetlerini** keşfetmek ve deneyimlemek için tasarlanmış interaktif bir laboratuvar ortamıdır. Bu proje, kullanıcıların LLM'e doğal dil girdileri sağlamasına olanak tanır ve modelin çıktısında potansiyel olarak kötü niyetli komutları algılayarak bunları temel işletim sistemi üzerinde **gerçekten çalıştırır**.

Lab ortamınızın donanımına göre dinamik olarak daha gelişmiş bir model olan **DeepSeek Coder 6.7B Instruct** (GPU algılandığında) veya daha hafif olan **GPT-2** (CPU kullanıldığında) modellerinden birini yükler. Gradio tabanlı web arayüzü sayesinde, LLM ile hem normal sohbet edebilir hem de farklı prompt enjeksiyonu tekniklerini deneyerek modelin nasıl manipüle edilebileceğini gözlemleyebilirsiniz.

### 🚨 Güvenlik Uyarısı (ÇOK ÖNEMLİ\!)

Bu proje **KESİNLİKLE SİBER GÜVENLİK ARAŞTIRMALARI VE EĞİTİM AMAÇLIDIR**.

**KODU KESİNLİKLE KENDİ ANA İŞLETİM SİSTEMİNİZDE VEYA HASSAS VERİLERİNİZİN BULUNDUĞU BİR ORTAMDA ÇALIŞTIRMAYIN.**

**BU UYGULAMAYI MUTLAKA, İNTERNET ERİŞİMİ OLMAYAN VEYA KISITLI OLAN, İZOLE EDİLMİŞ BİR SANAL MAKİNE (Örn: VirtualBox, VMware) VEYA DOCKER KONTEYNERİ İÇİNDE ÇALIŞTIRIN.**

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

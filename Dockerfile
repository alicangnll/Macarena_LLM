# Temel Görüntü: Python 3.9'un daha hafif bir versiyonu olan slim-buster'ı kullanın
# transformers ve torch gibi kütüphaneler için Python'ın belirli bir sürümüne ihtiyaç duyulabilir.
FROM python:3.9-slim-buster

# Çalışma dizinini ayarlayın
WORKDIR /app

# Gerekli sistem bağımlılıklarını yükleyin (eğer komutlar için gerekliyse)
# Örneğin, iproute2 (ip addr için), net-tools (netstat için) vb.
# Bu adım, yürütülen komutlara göre ayarlanmalıdır.
RUN apt-get update && apt-get install -y \
    procps \
    iproute2 \
    net-tools \
    # Diğer gerekli araçlar (örneğin, ifconfig için net-tools)
    # python3-dev veya build-essential gibi paketler, bazı python kütüphaneleri derlenirken gerekebilir
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyalayın
# requirements.txt dosyasını oluşturacağız
COPY requirements.txt .

# Python bağımlılıklarını yükleyin
# --no-cache-dir: pip'in paketleri önbelleğe almasını engeller, bu da görüntü boyutunu azaltır
# --upgrade pip: pip'i en son sürüme günceller
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyalayın
COPY main.py .

# Gradio'nun varsayılan portu olan 7860'ı açık bırakın
EXPOSE 7860

# Uygulamayı başlatma komutu
# Modelin yüklenmesi zaman alacağından, başlangıçta biraz beklemek faydalı olabilir, ancak doğrudan çalıştırın.
# Python uygulamasını çalıştırın
CMD ["python", "main.py"]
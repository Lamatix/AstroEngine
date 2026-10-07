import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def generate_astrology_interpretation(self, radix_data: dict, client_name: str = "Danışan") -> str:
        """
        Swiss Ephemeris'ten gelen ham radiks / doğum haritası verilerini 
        kapsamlı, derinlemesine ve uzun bir astrolojik rapora dönüştüren ajan metodudur.
        """
        prompt = f"""
        Sen kıdemli, sezgisel ve Master düzeyinde bir astrolog ve yaşam koçusun. 
        Aşağıda {client_name} için hesaplanmış matematiksel doğum haritası (radiks, yükselen ve gezegen konumları) verilmiştir. 

        Lütfen kısa kesme; her bir bileşeni derinlemesine ele alarak kapsamlı, sayfa dolusu profesyonel bir analiz raporu hazırla. Raporun şu ana bölümlerden oluşsun:
        1. **Genel Karakter Analizi ve Yükselen Burç:** Yükselen burcun ve yöneticisinin getirdiği dış dünya maskesi, fiziksel duruş ve yaşam yolu.
        2. **Gezegen Yerleşimleri ve Derin Psikolojik Portre:** Güneş, Ay ve diğer iç/dış gezegenlerin burç ve derece bazlı bireysel psikolojiye etkileri (duygusal dünya, zihinsel süreçler, motivasyonlar).
        3. **Güçlü Yönler ve Potansiyel Tuzaklar:** Kişinin hayatta parlayacağı alanlar ve testlerden geçeceği kadersel döngüler.
        4. **Gelecek Dönem Enerjileri ve Yaşam Rehberliği:** Bu haritanın kişiye sunduğu genel yaşam tavsiyeleri ve vizyoner rehberlik.

        Üslubun son derece profesyonel, akıcı, etkileyici, detaylı ve rehber niteliğinde olsun.

        Doğum Haritası Verileri:
        {radix_data}
        """

        try:
            response = self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "Sen kıdemli ve derinlemesine analizler yapan profesyonel bir astroloji ajanısın. Asla kısa kesmezsin, her detayı açıkularsın."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3500  # Uzun ve detaylı çıktı alabilmek için artırıldı
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM Servis Hatası: {str(e)}")

# Global servis örneği
llm_service = LLMService()
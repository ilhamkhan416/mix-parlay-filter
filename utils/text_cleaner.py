import re
from unidecode import unidecode

def clean_team_name(name: str) -> str:
    if not name:
        return ""
    
    # 1. Konversi aksen asing ke ASCII biasa (misal: München -> Munchen)
    text = unidecode(name).lower()
    
    # 2. Hapus noise umum nama klub/liga dalam berbagai bahasa
    noise_pattern = r'\b(fc|cf|ac|as|sc|cd|sv|vfb|vfl|tsv|united|city|town|club|real|sporting|1\.)\b'
    text = re.sub(noise_pattern, '', text)
    
    # 3. Hapus karakter khusus & spasi ganda
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

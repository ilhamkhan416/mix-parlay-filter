import re
from unidecode import unidecode

def clean_team_name(name: str) -> str:
    if not name:
        return ""
    
    # 1. Hilangkan aksen (misal: München -> Munchen)
    text = unidecode(str(name)).lower()
    
    # 2. Hapus awalan angka handicap/odds jika terikut (misal: "1.5 bayern" -> "bayern")
    text = re.sub(r'^\d+(\.\d+)?\s*', '', text)
    
    # 3. Hapus kata noise klub & singkatan dalam berbagai bahasa
    noise_pattern = r'\b(fc|cf|ac|as|sc|cd|sv|vfb|vfl|tsv|united|utd|city|town|club|real|sporting|1\.|vs|v)\b'
    text = re.sub(noise_pattern, '', text)
    
    # 4. Hapus karakter non-alfanumerik
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

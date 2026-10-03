import re
from unidecode import unidecode

def clean_team_name(name: str) -> str:
    if not name:
        return ""
    
    # 1. Hilangkan aksen (misal: München -> Munchen)
    text = unidecode(str(name)).lower()
    
    # 2. Hapus angka pasaran/handicap di awal jika terikut (misal: "1.5 Bayern" -> "Bayern")
    text = re.sub(r'^\d+(\.\d+)?\s+', '', text)
    
    # 3. Hapus karakter khusus selain huruf, angka, dan spasi
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # 4. Normalisasi spasi ganda
    return re.sub(r'\s+', ' ', text).strip()

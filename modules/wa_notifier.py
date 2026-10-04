import os
import requests

def send_whatsapp_parlay_picks(picks: list):
    """
    Mengirimkan notifikasi daftar tim pilihan (+EV Mix Parlay) ke WhatsApp via Fonnte
    dengan rincian Form 5 Laga, H2H, dan Alasan Pemilihan.
    """
    token = os.getenv("FONNTE_TOKEN")
    target_number = os.getenv("WA_TARGET_NUMBER")

    # Keamanan jika variabel environment belum diset di GitHub Secrets
    if not token or not target_number:
        print("⚠️ Notifikasi WA dilewati: FONNTE_TOKEN atau WA_TARGET_NUMBER belum dikonfigurasi di GitHub Secrets.")
        return

    # Susun isi pesan WhatsApp
    if not picks:
        message = (
            "🎯 *HIGH PROBABILITY MIX PARLAY*\n"
            "───────────────\n"
            "⚠️ *Info:* Tidak ada pertandingan yang memenuhi kriteria ketat +EV hari ini."
        )
    else:
        message = f"🎯 *TOP {len(picks)} HIGH PROBABILITY PARLAY PICKS*\n"
        message += "───────────────\n\n"
        
        for i, pick in enumerate(picks, 1):
            match_name = pick.get('match', '-')
            selected_team = pick.get('pick', 'Team')
            pick_type = pick.get('pick_type', 'Home Win')
            odds = pick.get('selected_odds', '-')
            est_prob = pick.get('estimated_real_prob', '-')
            ev_val = pick.get('expected_value', '-')
            league = pick.get('league', 'Unknown League')
            
            # Kunci-kunci baru dari filter_engine.py
            form_history = pick.get('form_history', '-')
            h2h_list = pick.get('h2h_history', [])
            rationale = pick.get('rationale', 'Statistik gabungan stabil')

            # Format teks H2H ringkas (maksimal 3 laga H2H terakhir agar pesan tidak terlalu panjang)
            h2h_str = ", ".join(h2h_list[:3]) if h2h_list else "Tidak ada data H2H"

            message += f"*{i}. {match_name}*\n"
            message += f"   🏆 *Liga:* {league}\n"
            message += f"   👉 *PASANG:* *{selected_team}* ({pick_type})\n"
            message += f"   • Odds: `{odds}` | Est. Win: `{est_prob}` | EV: `{ev_val}`\n"
            message += f"   📈 *Form 5 Laga:* `{form_history}`\n"
            message += f"   ⚔️ *H2H Terakhir:* {h2h_str}\n"
            message += f"   💡 *Alasan Dipick:* {rationale}\n\n"

        message += "📌 *Rekomendasi:* Kombinasikan 2 hingga 3 tim pilihan di atas untuk 1 paket tiket Mix Parlay."

    # Payload request ke Fonnte API
    payload = {
        'target': target_number,
        'message': message,
        'countryCode': '62', # Kode negara Indonesia
    }
    
    headers = {
        'Authorization': token
    }

    try:
        response = requests.post("https://api.fonnte.com/send", data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            print(f"✅ Notifikasi {len(picks)} tim pilihan (Lengkap H2H & Alasan) berhasil dikirim ke WhatsApp!")
        else:
            print(f"❌ Gagal mengirim notifikasi WA (Status {response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Error saat menghubungkan ke Fonnte API: {e}")

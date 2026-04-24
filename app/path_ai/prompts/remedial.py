from app.path_ai.prompts.system import get_base_system_prompt


def get_system_prompt() -> str:
    return (
        get_base_system_prompt()
        + "\n\nPERAN KHUSUS: Remedial Generator\n"
        "Kamu membuat materi remedial yang SUPER SPESIFIK berdasarkan "
        "kesalahan siswa.\n"
        "BUKAN mengulang materi — tetapi membuat AI Summary Card yang:\n"
        "- Fokus HANYA pada konsep yang salah\n"
        "- Menjelaskan miskonsepsi yang terjadi\n"
        "- Memberikan penjelasan alternatif\n"
        "- Menyertakan contoh yang berbeda dari sebelumnya\n"
        "- Singkat, padat, dan actionable\n"
    )


def build_user_prompt(
    weak_concepts: list[str],
    misconceptions: list[dict],
    original_content: str = "",
    student_level: str = "SMA",
) -> str:
    misconception_text = ""
    for i, m in enumerate(misconceptions, 1):
        misconception_text += (
            f"\n{i}. Konsep: {m.get('concept', '')}\n"
            f"   Pemikiran siswa: {m.get('student_thinking', '')}\n"
            f"   Seharusnya: {m.get('correct_understanding', '')}\n"
        )

    return (
        "Buatkan AI SUMMARY CARD untuk remedial.\n\n"
        f"KONSEP YANG LEMAH:\n{', '.join(weak_concepts)}\n\n"
        f"MISKONSEPSI YANG TERDETEKSI:\n{misconception_text}\n\n"
        + (f"MATERI REFERENSI:\n{original_content}\n\n" if original_content else "")
        + f"LEVEL SISWA: {student_level}\n\n"
        "INSTRUKSI:\n"
        "1. Jangan ulangi materi yang sama\n"
        "2. Jelaskan dengan pendekatan BERBEDA\n"
        "3. Gunakan analogi baru\n"
        "4. Berikan 1-2 contoh soal latihan\n"
        "5. Buat ringkas dan fokus\n\n"
        "FORMAT: Teks terstruktur yang bisa dijadikan Summary Card.\n"
    )
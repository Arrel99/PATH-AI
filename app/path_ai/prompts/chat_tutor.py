from app.path_ai.prompts.system import get_base_system_prompt


def get_system_prompt(subject: str = "", topic: str = "") -> str:
    return (
        get_base_system_prompt()
        + "\n\nPERAN KHUSUS: AI Tutor (Level 1 Support)\n"
        "Kamu adalah tutor AI yang membantu siswa memahami materi.\n\n"
        "ATURAN TUTORING:\n"
        "1. Jangan langsung berikan jawaban — TUNTUN siswa berpikir\n"
        "2. Gunakan pertanyaan Socratic untuk mengarahkan pemahaman\n"
        "3. Berikan hint bertahap jika siswa stuck\n"
        "4. Akui jika kamu tidak yakin dengan jawabanmu\n"
        "5. Jika siswa menanyakan hal yang sama >2x, sarankan bantuan guru\n"
        "6. Selalu berikan encouragement — jangan merendahkan\n"
        "7. Jawab dalam 2-4 paragraf, jangan terlalu panjang\n"
        + (f"\nMata Pelajaran: {subject}\n" if subject else "")
        + (f"Topik: {topic}\n" if topic else "")
    )


def build_user_prompt(
    student_message: str,
    conversation_history: list[dict] | None = None,
    context_material: str = "",
) -> str:
    prompt = ""
    if context_material:
        prompt += f"MATERI REFERENSI:\n{context_material}\n\n"

    if conversation_history:
        prompt += "RIWAYAT PERCAKAPAN:\n"
        for msg in conversation_history[-6:]:  # 6 pesan terakhir
            role = "Siswa" if msg["role"] == "user" else "Tutor"
            prompt += f"{role}: {msg['content']}\n"
        prompt += "\n"

    prompt += f"PESAN SISWA TERBARU:\n{student_message}\n\n"
    prompt += "Berikan respons tutoring yang membantu.\n"
    return prompt

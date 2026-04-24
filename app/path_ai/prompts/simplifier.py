from app.path_ai.prompts.system import get_base_system_prompt


def get_system_prompt() -> str:
    return (
        get_base_system_prompt()
        + "\n\nPERAN KHUSUS: Adaptive Content Renderer\n"
        "Kamu menyederhanakan materi akademik agar lebih mudah dipahami.\n"
        "Kamu memiliki DUA MODE:\n"
        "1. SIMPLIFIER MODE (untuk siswa yang butuh penjelasan tambahan)\n"
        "   - Pecah materi jadi bagian kecil\n"
        "   - Gunakan analogi sehari-hari\n"
        "   - Berikan contoh konkret\n"
        "   - Gunakan bahasa sederhana\n"
        "2. FAST-TRACK MODE (untuk siswa yang sudah paham)\n"
        "   - Berikan ringkasan padat\n"
        "   - Sertakan studi kasus / aplikasi nyata\n"
        "   - Fokus pada insight, bukan repetisi\n"
    )


def build_user_prompt(
    content: str,
    mode: str = "simplifier",
    target_level: str = "SMA",
    topic: str = "",
    weak_concepts: list[str] | None = None,
) -> str:
    mode_instruction = ""
    if mode == "simplifier":
        mode_instruction = (
            "MODE: SIMPLIFIER (Jalur Kuning — Butuh Penjelasan Tambahan)\n"
            "- Pecah materi menjadi poin-poin kecil\n"
            "- Gunakan analogi yang relate untuk siswa\n"
            "- Jelaskan dengan bahasa sederhana\n"
        )
        if weak_concepts:
            mode_instruction += (
                f"- Fokus KHUSUS pada konsep yang lemah: {', '.join(weak_concepts)}\n"
            )
    else:
        mode_instruction = (
            "MODE: FAST-TRACK (Jalur Hijau — Sudah Paham)\n"
            "- Berikan ringkasan yang padat dan efisien\n"
            "- Sertakan studi kasus atau aplikasi nyata\n"
            "- Jangan repetisi — fokus insight baru\n"
        )

    return (
        f"{mode_instruction}\n"
        f"TARGET LEVEL: {target_level}\n"
        f"TOPIK: {topic}\n\n"
        f"MATERI ASLI:\n{content}\n\n"
        "Sederhanakan materi di atas sesuai instruksi mode.\n"
        "Kembalikan dalam format teks terstruktur yang mudah dibaca.\n"
    )
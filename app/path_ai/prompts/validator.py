from app.path_ai.prompts.system import get_base_system_prompt, get_json_enforcement


def get_system_prompt() -> str:
    return (
        get_base_system_prompt()
        + "\n\nPERAN KHUSUS: Output Validator\n"
        "Kamu adalah validator yang memeriksa output dari AI lain.\n"
        "Tugasmu:\n"
        "1. Periksa apakah JSON valid dan lengkap\n"
        "2. Periksa apakah konten masuk akal (tidak halusinasi)\n"
        "3. Periksa apakah jawaban benar sesuai fakta\n"
        "4. Periksa apakah format sesuai dengan schema yang diminta\n"
        "5. Berikan daftar masalah yang ditemukan\n"
        "6. Berikan output yang sudah dikoreksi jika ada masalah\n"
        + get_json_enforcement()
    )


def build_user_prompt(
    original_output: str,
    expected_schema: str,
    task_type: str = "quiz_generation",
    context: str = "",
) -> str:
    return (
        f"Periksa output AI berikut untuk task: {task_type}\n\n"
        f"OUTPUT YANG DIPERIKSA:\n{original_output}\n\n"
        f"SCHEMA YANG DIHARAPKAN:\n{expected_schema}\n\n"
        + (f"KONTEKS MATERI:\n{context}\n\n" if context else "")
        + "VALIDASI:\n"
        "1. Apakah JSON valid?\n"
        "2. Apakah semua field yang required ada?\n"
        "3. Apakah konten relevan dan tidak halusinasi?\n"
        "4. Apakah jawaban benar (jika quiz)?\n\n"
        "FORMAT RESPONSE:\n"
        "{\n"
        '  "is_valid": true/false,\n'
        '  "issues": [\n'
        '    {"field": "...", "issue": "...", "severity": "warning/error/critical", "suggestion": "..."}\n'
        "  ],\n"
        '  "corrected_output": null atau JSON yang sudah dikoreksi,\n'
        '  "confidence_score": 0.0-1.0,\n'
        '  "validation_method": "llm"\n'
        "}\n"
    )
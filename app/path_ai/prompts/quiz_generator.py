from app.path_ai.prompts.system import get_base_system_prompt, get_json_enforcement

def get_system_prompt() -> str:
    return (
        get_base_system_prompt()
        + "\n\nPERAN KHUSUS: Quiz Generator\n"
        "Kamu adalah pembuat soal yang ahli. Kamu membuat soal berdasarkan "
        "materi yang diberikan, dengan tingkat kesulitan yang sesuai.\n"
        "Setiap soal HARUS:\n"
        "- Relevan dengan materi\n"
        "- Memiliki jawaban yang jelas dan bisa diverifikasi\n"
        "- Mencakup berbagai level kognitif (ingatan, pemahaman, aplikasi)\n"
        "- Menyertakan penjelasan mengapa jawaban tersebut benar\n"
        + get_json_enforcement()
    )

def build_user_prompt(
    content: str,
    num_questions: int = 5,
    question_type: str = "multiple_choice",
    difficulty: str = "medium",
    topic: str = "",
    language: str = "id",
) -> str:
    return (
        f"Buatkan {num_questions} soal {question_type} dengan tingkat kesulitan "
        f"'{difficulty}' berdasarkan materi berikut.\n\n"
        f"TOPIK: {topic}\n\n"
        f"MATERI:\n{content}\n\n"
        f"FORMAT JSON YANG DIHARAPKAN:\n"
        "{\n"
        '  "title": "Judul Quiz",\n'
        '  "subject": "Mata Pelajaran",\n'
        '  "topic": "Topik",\n'
        '  "total_questions": <jumlah>,\n'
        '  "questions": [\n'
        "    {\n"
        '      "question_id": 1,\n'
        '      "question": "Pertanyaan...",\n'
        f'      "question_type": "{question_type}",\n'
        '      "options": [\n'
        '        {"label": "A", "text": "...", "is_correct": false},\n'
        '        {"label": "B", "text": "...", "is_correct": true},\n'
        '        {"label": "C", "text": "...", "is_correct": false},\n'
        '        {"label": "D", "text": "...", "is_correct": false}\n'
        "      ],\n"
        '      "correct_answer": "B",\n'
        '      "explanation": "Penjelasan...",\n'
        f'      "difficulty": "{difficulty}",\n'
        '      "concept_tag": "nama_konsep"\n'
        "    }\n"
        "  ],\n"
        '  "summary": "Ringkasan materi yang digunakan"\n'
        "}\n"
    )

def build_diagnostic_prompt(
    content: str,
    num_questions: int = 3,
    topic: str = "",
) -> str:
    return (
        f"Buatkan {num_questions} soal DIAGNOSTIK RINGAN untuk mengukur "
        "pemahaman konseptual siswa.\n\n"
        "TUJUAN: Menghasilkan sinyal belajar (hijau/kuning), BUKAN nilai angka.\n"
        "Soal harus:\n"
        "- Konseptual, bukan hafalan\n"
        "- Singkat dan jelas\n"
        "- Mencakup konsep inti topik\n"
        f"- Berjumlah {num_questions} soal\n\n"
        f"TOPIK: {topic}\n\n"
        f"MATERI:\n{content}\n\n"
        "Gunakan format JSON GeneratedQuiz yang sama seperti quiz biasa.\n"
        'Tambahkan "concept_tag" pada setiap soal untuk tracking.\n'
    )
from app.path_ai.prompts.system import get_base_system_prompt, get_json_enforcement


def get_system_prompt() -> str:
    return (
        get_base_system_prompt()
        + "\n\nPERAN KHUSUS: Semantic Grader\n"
        "Kamu adalah penilai jawaban yang cerdas. Kamu tidak hanya menilai "
        "benar/salah, tetapi juga:\n"
        "- Mengidentifikasi MISKONSEPSI dalam jawaban siswa\n"
        "- Menjelaskan MENGAPA jawaban salah\n"
        "- Memberikan feedback berbasis KONSEP, bukan sekadar koreksi\n"
        "- Menilai dengan skala 0-100\n"
        "- Mendeteksi pola kesalahan yang berulang\n"
        + get_json_enforcement()
    )


def build_user_prompt(
    question: str,
    correct_answer: str,
    student_answer: str,
    concept_tag: str = "",
    question_type: str = "multiple_choice",
) -> str:
    return (
        "Nilai jawaban siswa berikut secara SEMANTIK.\n\n"
        f"SOAL: {question}\n"
        f"JAWABAN BENAR: {correct_answer}\n"
        f"JAWABAN SISWA: {student_answer}\n"
        f"KONSEP: {concept_tag}\n"
        f"TIPE SOAL: {question_type}\n\n"
        "FORMAT JSON:\n"
        "{\n"
        '  "is_correct": true/false,\n'
        '  "score": 0-100,\n'
        '  "explanation": "Penjelasan detail...",\n'
        '  "misconceptions": [\n'
        "    {\n"
        '      "concept": "Nama konsep",\n'
        '      "student_thinking": "Apa yang kemungkinan dipikirkan siswa",\n'
        '      "correct_understanding": "Pemahaman yang benar",\n'
        '      "severity": "low/medium/high"\n'
        "    }\n"
        "  ],\n"
        '  "concept_feedback": "Saran belajar berbasis konsep..."\n'
        "}\n"
    )


def build_batch_grading_prompt(
    questions_and_answers: list[dict],
) -> str:
    qa_text = ""
    for i, qa in enumerate(questions_and_answers, 1):
        qa_text += (
            f"\n--- SOAL {i} ---\n"
            f"Soal: {qa['question']}\n"
            f"Jawaban Benar: {qa['correct_answer']}\n"
            f"Jawaban Siswa: {qa['student_answer']}\n"
            f"Konsep: {qa.get('concept_tag', '')}\n"
        )

    return (
        "Nilai SEMUA jawaban siswa berikut secara semantik.\n"
        f"{qa_text}\n\n"
        "Kembalikan JSON array berisi objek grading untuk setiap soal.\n"
        "Setiap objek harus mengikuti format GradingFeedback.\n"
    )

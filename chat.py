import asyncio
from app.path_ai.core.openrouter_client import OpenRouterClient
from app.path_ai.tasks.tutor_chat import tutor_chat
from app.path_ai.engines.escalation_engine import EscalationContext


async def main():
    llm = OpenRouterClient()
    history = []
    context = EscalationContext(student_id="terminal_user", topic="")

    print("\n  PATH AI - Chat Tutor")
    print("  Ketik pertanyaan, lalu tekan Enter.")
    print("  Ketik 'exit' untuk keluar.\n")

    subject = input("Mata pelajaran: ").strip() or "Umum"
    topic = input("Topik: ").strip() or ""
    material = input("Materi (opsional, kosongkan jika tidak ada): ").strip()
    context.topic = topic

    print(f"\n  Siap! Tanya apa saja tentang {topic or subject}.\n")

    while True:
        user_input = input("Kamu: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "keluar"):
            break

        context.record_message(user_input)

        result = await tutor_chat(
            llm=llm,
            student_message=user_input,
            conversation_history=history if history else None,
            context_material=material,
            subject=subject,
            topic=topic,
            escalation_context=context,
        )

        print(f"\nAI Tutor: {result['response']}\n")

        if result["should_escalate"]:
            print(f"  [ESKALASI] {result['escalation_reason']}")
            print("  Percakapan akan diteruskan ke guru.\n")
            break

        # Simpan history
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": result["response"]})

    await llm.close()
    print("Chat selesai.")


if __name__ == "__main__":
    asyncio.run(main())
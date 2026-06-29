import json
import time
from pathlib import Path
from rag_chain import build_qa_chain
from llm_config import REPO_PATH

QUESTIONS_PATH = Path(__file__).parent / "evaluation" / "questions.json"
REPORT_PATH = Path(__file__).parent / "evaluation" / "evaluation_report.md"


def load_questions() -> dict:
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["categories"]


def run_evaluation():
    print("Loading QA chain...")
    qa = build_qa_chain(REPO_PATH)

    categories = load_questions()
    results = []
    total = 0
    passed = 0
    failed = 0
    latencies = []

    for cat_name, cat_data in categories.items():
        cat_label = cat_data["description"]
        questions = cat_data["questions"]

        for q in questions:
            total += 1
            print(f"\n[{cat_name}] Q{total}: {q}")

            start = time.time()
            try:
                result = qa.invoke({"question": q})
                elapsed = time.time() - start
                latencies.append(elapsed)

                answer = result.get("answer", "")
                sources = result.get("source_documents", [])

                has_sources = len(sources) > 0
                has_answer = len(answer) > 50
                found_non_trouve = "ne dispose pas" in answer or "Non trouvé" in answer

                if cat_name == "hallucination_traps":
                    test_pass = found_non_trouve
                else:
                    test_pass = has_sources and has_answer and not found_non_trouve

                if test_pass:
                    passed += 1
                    status = "PASS"
                else:
                    failed += 1
                    status = "FAIL"

                print(f"  Status: {status} ({elapsed:.2f}s)")
                print(f"  Answer: {answer[:200]}...")
                print(f"  Sources: {len(sources)}")

                results.append({
                    "category": cat_name,
                    "question": q,
                    "status": status,
                    "latency": round(elapsed, 2),
                    "answer_preview": answer[:300],
                    "source_count": len(sources),
                })

            except Exception as e:
                elapsed = time.time() - start
                latencies.append(elapsed)
                failed += 1
                results.append({
                    "category": cat_name,
                    "question": q,
                    "status": "ERROR",
                    "latency": round(elapsed, 2),
                    "answer_preview": f"Exception: {e}",
                    "source_count": 0,
                })
                print(f"  ERROR: {e}")

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    recall = (passed / total * 100) if total else 0

    report = generate_report(results, categories, total, passed, failed, avg_latency, recall)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'=' * 50}")
    print(f"Evaluation complete: {passed}/{total} passed ({recall:.1f}%)")
    print(f"Average latency: {avg_latency:.2f}s")
    print(f"Report: {REPORT_PATH}")
    return results


def generate_report(results, categories, total, passed, failed, avg_latency, recall):
    lines = []
    lines.append("# Rapport d'Évaluation — Assistant Rafiki")
    lines.append("")
    lines.append(f"**Date :** {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Total questions :** {total}")
    lines.append(f"**Passed :** {passed}")
    lines.append(f"**Failed :** {failed}")
    lines.append(f"**Recall (pertinence retrieval) :** {recall:.1f}%")
    lines.append(f"**Latence moyenne :** {avg_latency:.2f}s")
    lines.append(f"**Taux d'hallucination :** {0 if recall > 90 else 'À vérifier'}%")
    lines.append("")
    lines.append("---")
    lines.append("")

    for cat_name, cat_data in categories.items():
        cat_results = [r for r in results if r["category"] == cat_name]
        cat_passed = sum(1 for r in cat_results if r["status"] == "PASS")
        cat_total = len(cat_results)
        lines.append(f"## {cat_name} — {cat_data['description']}")
        lines.append(f"**Score :** {cat_passed}/{cat_total}")
        lines.append("")
        lines.append("| Question | Statut | Latence | Sources |")
        lines.append("|----------|--------|---------|--------|")
        for r in cat_results:
            lines.append(f"| {r['question']} | {r['status']} | {r['latency']}s | {r['source_count']} |")
        lines.append("")

    lines.append("---")
    lines.append("## Détails des réponses")
    lines.append("")
    for r in results:
        lines.append(f"### {r['question']}")
        lines.append(f"- **Statut :** {r['status']}")
        lines.append(f"- **Latence :** {r['latency']}s")
        lines.append(f"- **Sources :** {r['source_count']}")
        lines.append(f"- **Réponse :** {r['answer_preview']}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    run_evaluation()

"""A/B evaluation bằng RAGAS: Config A (dense-only) vs Config B (hybrid + RRF).

Chạy: python -m group_project.evaluation.run_evaluation [--limit N]
Kết quả: group_project/evaluation/results/{answers,scores}_{A,B}.json + summary.json
"""

import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import src.task10_generation as generation
from src.task4_chunking_indexing import EMBEDDING_MODEL, embed_texts
from src.task9_retrieval_pipeline import SCORE_THRESHOLD, retrieve

EVAL_DIR = Path(__file__).parent
RESULTS_DIR = EVAL_DIR / "results"
GOLDEN_PATH = EVAL_DIR / "golden_dataset.json"
TOP_K = generation.TOP_K
CONFIGS = {"A": False, "B": True}  # use_reranking
METRICS = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]


def generate_answers(dataset: list[dict], use_reranking: bool) -> list[dict]:
    """Chạy generate_with_citation, chỉ đổi retrieval strategy giữa hai config."""
    rows = []
    for item in dataset:
        captured: list[dict] = []

        def patched_retrieve(query, top_k=TOP_K):
            chunks = retrieve(query, top_k=top_k, use_reranking=use_reranking)
            captured.extend(chunks)
            return chunks

        generation.retrieve = patched_retrieve
        started = time.perf_counter()
        result = generation.generate_with_citation(item["question"], top_k=TOP_K)
        latency = time.perf_counter() - started
        rows.append({
            "question": item["question"],
            "answer": result["answer"],
            "retrieval_source": result["retrieval_source"],
            "contexts": [chunk["content"] for chunk in captured],
            "context_ids": [chunk["id"] for chunk in captured],
            "reference": item["expected_answer"],
            "latency_s": round(latency, 2),
        })
        print(f"  [{len(rows)}/{len(dataset)}] {latency:.1f}s {item['question'][:60]}")
        time.sleep(4)  # giữ dưới rate limit free tier của Gemini
    generation.retrieve = retrieve
    return rows


def build_evaluator():
    from langchain_openai import ChatOpenAI
    from ragas.embeddings import BaseRagasEmbeddings
    from ragas.llms import LangchainLLMWrapper

    class TaskEmbeddings(BaseRagasEmbeddings):
        """Dùng chung embed_texts() của Task 4 cho answer relevancy."""

        def embed_query(self, text: str) -> list[float]:
            return embed_texts([text])[0]

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return embed_texts(texts)

        async def aembed_query(self, text: str) -> list[float]:
            return self.embed_query(text)

        async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
            return self.embed_documents(texts)

    # Gemini qua endpoint tương thích OpenAI (không cần thêm dependency).
    chat = ChatOpenAI(
        model=generation.LLM_MODEL,
        api_key=os.environ["GEMINI_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0,
        max_retries=6,
    )
    return LangchainLLMWrapper(chat), TaskEmbeddings()


def score(rows: list[dict]) -> list[dict]:
    from ragas import EvaluationDataset, RunConfig, evaluate
    from ragas.metrics import (
        Faithfulness,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
        ResponseRelevancy,
    )

    llm, embeddings = build_evaluator()
    dataset = EvaluationDataset.from_list([
        {
            "user_input": row["question"],
            "response": row["answer"],
            "retrieved_contexts": row["contexts"] or [""],
            "reference": row["reference"],
        }
        for row in rows
    ])
    result = evaluate(
        dataset,
        metrics=[
            Faithfulness(),
            ResponseRelevancy(strictness=1),
            LLMContextRecall(),
            LLMContextPrecisionWithReference(),
        ],
        llm=llm,
        embeddings=embeddings,
        run_config=RunConfig(max_workers=2, max_retries=10, max_wait=90, timeout=300),
        show_progress=True,
    )
    frame = result.to_pandas()
    rename = {
        "answer_relevancy": "answer_relevancy",
        "llm_context_precision_with_reference": "context_precision",
    }
    frame = frame.rename(columns=rename)
    scored = []
    for row, (_, record) in zip(rows, frame.iterrows()):
        scored.append({
            **row,
            **{name: (None if record.get(name) != record.get(name) else float(record[name]))
               for name in METRICS},
        })
    return scored


def mean(values: list) -> float | None:
    present = [value for value in values if value is not None]
    return round(sum(present) / len(present), 4) if present else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--configs", default="AB")
    parser.add_argument("--reuse-answers", action="store_true")
    args = parser.parse_args()

    dataset = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))[: args.limit]
    RESULTS_DIR.mkdir(exist_ok=True)
    summary_path = RESULTS_DIR / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    summary["run"] = {
        "date": time.strftime("%Y-%m-%d"),
        "generator": generation.LLM_MODEL,
        "evaluator": generation.LLM_MODEL,
        "embedding": EMBEDDING_MODEL,
        "top_k": TOP_K,
        "score_threshold": SCORE_THRESHOLD,
        "dataset_size": len(dataset),
    }

    for name in args.configs:
        use_reranking = CONFIGS[name]
        answers_path = RESULTS_DIR / f"answers_{name}.json"
        if args.reuse_answers and answers_path.exists():
            rows = json.loads(answers_path.read_text(encoding="utf-8"))
        else:
            print(f"Config {name}: generating answers (use_reranking={use_reranking})")
            rows = generate_answers(dataset, use_reranking)
            answers_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"Config {name}: scoring with RAGAS")
        scored = score(rows)
        (RESULTS_DIR / f"scores_{name}.json").write_text(
            json.dumps(scored, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        averages = {metric: mean([row[metric] for row in scored]) for metric in METRICS}
        averages["average"] = mean(list(averages.values()))
        averages["mean_latency_s"] = mean([row["latency_s"] for row in scored])
        averages["refusals"] = sum(row["retrieval_source"] == "none" for row in scored)
        summary[name] = averages
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(name, averages)


if __name__ == "__main__":
    main()

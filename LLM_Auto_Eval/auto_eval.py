import csv
from datetime import datetime
from typing import Protocol
from langchain_core.language_models.chat_models import BaseChatModel
from .load_elyza_task import ElyzaTasks100
from .evaluation import evaluation

tasks = ElyzaTasks100()


class LLM(Protocol):
    def __call__(self, input_str: str) -> str: ...


class EvaluationCallback(Protocol):
    def __call__(self, result: dict) -> None: ...


def run(
    llm: LLM, eval_llm: BaseChatModel = None, evaluation_callback: EvaluationCallback = None
) -> float:
    now = datetime.now().strftime("%Y%m%d%H%M%S").zfill(14)
    if eval_llm:
        output_file = f"result_eval_{now}.csv"
    else:
        output_file = f"result_{now}.csv"
    fieldnames, row_datas = tasks.get_test_data()
    total_rows = len(row_datas)

    with open(output_file, "w", newline="", encoding="utf-8") as outfile:
        if eval_llm:
            fieldnames = fieldnames + ["result_output", "score"]
        else:
            fieldnames = fieldnames + ["result_output"]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        total_score = 0
        row_count = 0
        for row in row_datas:
            print(f"\n=============status=============")
            print(f"\rProcessing: {row_count+1}/{total_rows} ({((row_count+1)/total_rows*100):.1f}%)")
            input_text = row["input"]
            print("=============input_text=============")
            print(input_text)
            
            output_text = row["output"]
            eval_aspect = row["eval_aspect"]
            result_output = llm(input_text)

            row["result_output"] = result_output
            print("=============result_output=============")
            print(result_output)

            if eval_llm:
                score = evaluation(
                    eval_llm, result_output, input_text, output_text, eval_aspect
                )
    
                print("=============score=============")
                print(score)
                row["score"] = score
                total_score += score
            row_count += 1

            if evaluation_callback:
                evaluation_callback({"row_count": row_count, "total_score": total_score})
            writer.writerow(row)

        average_score = total_score / row_count if row_count else 0
        print("=============average score=============")
        print(average_score)
        return average_score

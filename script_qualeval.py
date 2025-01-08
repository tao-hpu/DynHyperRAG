import re
import json
import jsonlines
import os
os.environ["OPENAI_API_KEY"] = open("openai_api_key.txt").read().strip()
from openai import OpenAI
import argparse


def batch_eval(query_file, result1_file, result2_file, output_file_path, output_score_path):
    client = OpenAI()

    with open(query_file, "r") as f:
        data = f.read()

    queries = re.findall(r"- Question \d+: (.+)", data)

    with open(result1_file, "r") as f:
        answers1 = json.load(f)
    answers1 = [i["result"] for i in answers1]

    with open(result2_file, "r") as f:
        answers2 = json.load(f)
    answers2 = [i["result"] for i in answers2]

    results = []
    for i, (query, answer1, answer2) in enumerate(zip(queries, answers1, answers2)):
        sys_prompt = """
        ---Role---
        You are an expert tasked with evaluating two answers to the same question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.
        """

        prompt = f"""
        You will evaluate two answers to the same question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.

        - **Comprehensiveness**: How much detail does the answer provide to cover all aspects and details of the question?
        - **Diversity**: How varied and rich is the answer in providing different perspectives and insights on the question?
        - **Empowerment**: How well does the answer help the reader understand and make informed judgments about the topic?

        For each criterion, choose the better answer (either Answer 1 or Answer 2) and explain why. Then, select an overall winner based on these three categories.

        Here is the question:
        {query}

        Here are the two answers:

        **Answer 1:**
        {answer1}

        **Answer 2:**
        {answer2}

        Evaluate both answers using the three criteria listed above and provide detailed explanations for each criterion.

        Output your evaluation in the following JSON format:

        {{
            "Comprehensiveness": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Provide explanation here]"
            }},
            "Diversity": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Provide explanation here]"
            }},
            "Empowerment": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Provide explanation here]"
            }},
            "Overall Winner": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Summarize why this answer is the overall winner based on the three criteria]"
            }}
        }}
        """

        # 调用 OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "Comprehensiveness": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The answer that is better in terms of comprehensiveness (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A detailed explanation of why the chosen answer is better in terms of comprehensiveness."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            },
                            "Diversity": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The answer that is better in terms of diversity (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A detailed explanation of why the chosen answer is better in terms of diversity."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            },
                            "Empowerment": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The answer that is better in terms of empowerment (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A detailed explanation of why the chosen answer is better in terms of empowerment."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            },
                            "Overall Winner": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The overall better answer based on all three criteria (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A summary of why the chosen answer is the overall winner."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            }
                        },
                        "required": ["Comprehensiveness", "Diversity", "Empowerment", "Overall Winner"],
                        "additionalProperties": False
                    }
                }
            }
        )
        # 解析结果
        evaluation = response.choices[0].message.content
        print(f"Question {i+1} evaluation completed.\n")
        
        # 保存结果
        results.append({"Question": query, "Answer1": answer1, "Answer2": answer2, "Evaluation": json.loads(evaluation)})

    # 计算四种指标两个答案的得分, 
    answer_scores = {"Comprehensiveness": {"Answer1":0.0,"Answer2":0.0}, "Diversity": {"Answer1":0.0,"Answer2":0.0}, "Empowerment": {"Answer1":0.0,"Answer2":0.0}, "Overall Winner": {"Answer1":0.0,"Answer2":0.0}}
    for result in results:
        evaluation = result["Evaluation"]
        for key in evaluation:
            if evaluation[key]["Winner"] == "Answer 1":
                answer_scores[key]['Answer1'] += 1.0/len(results)
            elif evaluation[key]["Winner"] == "Answer 2":
                answer_scores[key]['Answer2'] += 1.0/len(results)
    
    # 将所有结果写入文件
    with open(output_file_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"All evaluations completed and saved to {output_file_path}")
    
    # 将得分写入文件
    with open(output_score_path, "w") as f:
        json.dump(answer_scores, f, indent=2)
        
    print(f"All scores saved to {output_score_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query_file", type=str, default="datasets/ultradoman/questions/sample_questions.txt")
    parser.add_argument("--result1_file", type=str, default="output_qual/ultradoman/sample/sample_result.json")
    parser.add_argument("--result2_file", type=str, default="others/lightrag/output_qual/ultradoman/sample/sample_result.json")
    parser.add_argument("--output_file_path", type=str, default="output_qual/ultradoman/sample/batch_eval.jsonl")
    parser.add_argument("--output_score_path", type=str, default="output_qual/ultradoman/sample/batch_eval_scores.json")
    args = parser.parse_args()
    batch_eval(args.query_file, args.result1_file, args.result2_file, args.output_file_path, args.output_score_path)

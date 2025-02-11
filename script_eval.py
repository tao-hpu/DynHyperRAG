import json
from sklearn.metrics.pairwise import cosine_similarity
from transformers import GPT2Tokenizer, AutoModel, AutoTokenizer
import torch
import argparse

# 初始化 GPT-2 分词器
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# 分词函数
def gpt2_tokenize(text):
    tokens = tokenizer.tokenize(text.lower())
    return tokens

# 加载 Groundtruth 和预测文件
def load_data(groundtruth_file, predictions_file):
    with open(groundtruth_file, 'r') as gt_file:
        groundtruth = json.load(gt_file)
    with open(predictions_file, 'r') as pred_file:
        predictions = json.load(pred_file)
    return groundtruth, predictions

# 计算 Context Recall (C-Rec)
def compute_c_rec(groundtruth, predictions):
    recalls = []
    for gt, pred in zip(groundtruth, predictions):
        gt_tokens = set(gpt2_tokenize(gt['result']))
        pred_tokens = set(gpt2_tokenize(pred['result']))
        overlap = len(gt_tokens.intersection(pred_tokens))
        recalls.append(overlap / len(gt_tokens) if len(gt_tokens) > 0 else 0)
    return sum(recalls) / len(recalls)

# 计算 Context Entity Recall (C-ERec)
def compute_c_erec(groundtruth, predictions, entity_extractor):
    recalls = []
    for gt, pred in zip(groundtruth, predictions):
        gt_entities = set(entity_extractor(gt['result']))
        pred_entities = set(entity_extractor(pred['result']))
        overlap = len(gt_entities.intersection(pred_entities))
        recalls.append(overlap / len(gt_entities) if len(gt_entities) > 0 else 0)
    return sum(recalls) / len(recalls)

# 简单的实体抽取函数（假设实体是以大写开头的单词）
def simple_entity_extractor(text):
    return [word for word in gpt2_tokenize(text) if word.istitle()]

# 计算 Answer Similarity (A-Sim)
def compute_a_sim(groundtruth, predictions, model, tokenizer):
    similarities = []
    for gt, pred in zip(groundtruth, predictions):
        gt_embedding = get_embedding(model, tokenizer, gt['result'])
        pred_embedding = get_embedding(model, tokenizer, pred['result'])
        similarity = cosine_similarity([gt_embedding], [pred_embedding])[0][0]
        similarities.append(similarity)
    return sum(similarities) / len(similarities)

# 获取句子嵌入
def get_embedding(model, tokenizer, text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().detach().numpy()

# 计算 Answer Correctness (A-Corr)
def compute_a_corr(groundtruth, predictions, model, tokenizer, alpha=0.5):
    a_corrs = []
    for gt, pred in zip(groundtruth, predictions):
        a_sim = compute_a_sim([gt], [pred], model, tokenizer)
        gt_tokens = set(gpt2_tokenize(gt['result']))
        pred_tokens = set(gpt2_tokenize(pred['result']))
        overlap = len(gt_tokens.intersection(pred_tokens))
        recall = overlap / len(gt_tokens) if len(gt_tokens) > 0 else 0
        precision = overlap / len(pred_tokens) if len(pred_tokens) > 0 else 0
        f1 = 2 * recall * precision / (recall + precision) if (recall + precision) > 0 else 0
        a_corrs.append(alpha * a_sim + (1 - alpha) * f1)
    return sum(a_corrs) / len(a_corrs)

# 计算 Answer Relevance (A-Rel)
def compute_a_rel(groundtruth, predictions):
    relevances = []
    for gt, pred in zip(groundtruth, predictions):
        gt_tokens = set(gpt2_tokenize(gt['query']))
        pred_tokens = set(gpt2_tokenize(pred['result']))
        overlap = len(gt_tokens.intersection(pred_tokens))
        relevances.append(overlap / len(gt_tokens) if len(gt_tokens) > 0 else 0)
    return sum(relevances) / len(relevances)

# 主函数
def evaluate_metrics(groundtruth_file, predictions_file, output_score_path):
    groundtruth, predictions = load_data(groundtruth_file, predictions_file)

    # 加载 Sentence-BERT 模型（或其他嵌入模型）
    embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model = AutoModel.from_pretrained(embedding_model_name)
    embed_tokenizer = AutoTokenizer.from_pretrained(embedding_model_name)

    c_rec = compute_c_rec(groundtruth, predictions)
    c_erec = compute_c_erec(groundtruth, predictions, simple_entity_extractor)
    a_sim = compute_a_sim(groundtruth, predictions, model, embed_tokenizer)
    a_corr = compute_a_corr(groundtruth, predictions, model, embed_tokenizer)
    a_rel = compute_a_rel(groundtruth, predictions)

    print(f"Context Recall (C-Rec): {c_rec:.4f}")
    print(f"Context Entity Recall (C-ERec): {c_erec:.4f}")
    print(f"Answer Similarity (A-Sim): {a_sim:.4f}")
    print(f"Answer Correctness (A-Corr): {a_corr:.4f}")
    print(f"Answer Relevance (A-Rel): {a_rel:.4f}")
    
    ## 保存结果
    answer_scores = {
        "Context Recall (C-Rec)": c_rec,
        "Context Entity Recall (C-ERec)": c_erec,
        "Answer Similarity (A-Sim)": a_sim,
        "Answer Correctness (A-Corr)": a_corr,
        "Answer Relevance (A-Rel)": a_rel
    }
    with open(output_score_path, "w") as f:
        json.dump(answer_scores, f, indent=2)
        
    print(f"All scores saved to {output_score_path}")    
    
    

parser = argparse.ArgumentParser()
parser.add_argument("--groundtruth_file", type=str, default="datasets/ultradoman/unique_questions/sample_unique_questions.json")
parser.add_argument("--predictions_file", type=str, default="output_quan/ultradoman/sample/sample_result.json")
parser.add_argument("--output_score_path", type=str, default="output_quan/ultradoman/sample/batch_eval_scores.json")
args = parser.parse_args()

# 调用评估函数
evaluate_metrics(args.groundtruth_file, args.predictions_file, args.output_score_path)

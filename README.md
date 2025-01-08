# HyperGraphRAG

## Dependence
```bash
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag
pip install torch==2.3.0
pip install -r requirements.txt
```

## Dataset Preparation

### UltraDomain
The ultradomain dataset used in HyperGraphRAG can be downloaded from [TommyChien/UltraDomain](https://huggingface.co/datasets/TommyChien/UltraDomain). to `datasets/ultradomain/agriculture[cs,legal,mix].json`.

For UltraDomain dataset, we extract unique contexts from the dataset.
```bash
python script_context.py
```
For quantitative analysis, we collect questions and groundtruths from the dataset.
```bash
python script_question.py
```
For qualitative analysis, we generate questions from the contexts.
```bash
python script_genquestion.py --cls agriculture
python script_genquestion.py --cls legal
python script_genquestion.py --cls cs
python script_genquestion.py --cls mix
```

### Hypertension
The hypertension dataset used in HyperGraphRAG can be downloaded from [2024 ESC Guidelines forthemanagement of elevated blood pressure andhypertension](https://academic.oup.com/eurheartj/article/45/38/3912/7741010?login=false) to `Hypertension.pdf`.

For Hypertension dataset, we extract unique contexts from the PDF.
```bash
python script_pdf2txt.py
```
For quantitative analysis, we collect questions and groundtruths from the real doctors, which can be downloaded from [here](https://academic.oup.com/eurheartj/article/45/38/3912/7741010?login=false) to `datasets/ultradoman/unique_questions/hypertension_unique_questions.json`.

For qualitative analysis, we generate questions from the contexts.
```bash
python script_genquestion.py --cls hypertension
```

## HyperGraphRAG Process

### Agriculture
For the extracted contexts, we insert them into the HyperGraphRAG system.
```bash
nohup python script_insert.py --cls agriculture >> result_agriculture_insert.log 2>&1 &
```

#### Quantitative Evaluation
For the queries collected, we will query HyperGraphRAG.
```bash
nohup python script_quanquery.py --cls agriculture >> result_agriculture_quanquery.log 2>&1 &
```
Evaluate HyperGraphRAG
```bash
nohup python script_quaneval.py --groundtruth_file datasets/ultradoman/unique_questions/agriculture_unique_questions.json --predictions_file output_quan/ultradoman/agriculture/agriculture_result.json --output_score_path output_quan/ultradoman/agriculture/batch_eval_scores.json >> result_agriculture_quaneval_hypergraphrag.log 2>&1 &
```
Evaluate LightRAG
```bash
nohup python script_quaneval.py --groundtruth_file datasets/ultradoman/unique_questions/agriculture_unique_questions.json --predictions_file others/lightrag/output_quan/ultradoman/agriculture/agriculture_result.json --output_score_path output_quan/ultradoman/agriculture/batch_eval_scores_lightrag.json >> result_agriculture_quaneval_lightrag.log 2>&1 &
```

#### Qualitative Evaluation 
For the queries generated, we will extract them and query HyperGraphRAG.
```bash
nohup python script_qualquery.py --cls agriculture >> result_agriculture_qualquery.log 2>&1 &
```
Evaluate HyperGraphRAG vs LightRAG
```bash
nohup python script_qualeval.py --query_file datasets/ultradoman/questions/agriculture_questions.txt --result1_file output/ultradoman/agriculture/agriculture_result.json --result2_file others/lightrag/output/ultradoman/agriculture/agriculture_result.json --output_file_path output/ultradoman/agriculture --output_score_path output/ultradoman/agriculture >> result_agriculture_qualeval_hypergraphrag_vs_lightrag.log 2>&1 &
```



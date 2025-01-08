import json
from PyPDF2 import PdfReader
import os

def pdf_to_json_segments(pdf_path, output_json_path):
    """
    使用 PyPDF2 提取 PDF 内容，移除换行符，按段分割成字符串列表，并保存为 JSON 文件。
    """
    # 读取 PDF 文件
    reader = PdfReader(pdf_path)
    segments = []

    print("开始提取 PDF 内容...")
    for i, page in enumerate(reader.pages):
        print(f"正在提取第 {i + 1} 页...")
        page_text = page.extract_text()
        if page_text:
            # 替换换行符为单个空格，并将每页文本保存为一个段落字符串
            page_text = page_text.replace("\n", " ")
            segments.append(page_text.strip())
        else:
            print(f"第 {i + 1} 页无文本内容，跳过。")

    # 保存为 JSON 文件
    if not os.path.exists(output_json_path):
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(segments, json_file, ensure_ascii=False, indent=4)
    
    print(f"提取完成！结果已保存到 {output_json_path}")

# 使用示例
pdf_path = "Hypertension.pdf"  # PDF 文件路径
output_txt_path = "datasets/ultradoman/unique_contexts/hypertension_unique_contexts.json"  # 输出 TXT 文件路径

pdf_to_json_segments(pdf_path, output_txt_path)
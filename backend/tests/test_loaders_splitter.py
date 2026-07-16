"""文档加载与切块。"""

from pathlib import Path

from app.rag.loaders import load_file_to_documents
from app.rag.splitter import split_documents


def test_load_markdown_file(tmp_path: Path):
    p = tmp_path / "demo.md"
    p.write_text("# 商品\n\n支持七天无理由退货。\n续航 7 天。", encoding="utf-8")
    docs = load_file_to_documents(p, "demo.md")
    assert len(docs) >= 1
    assert "七天无理由" in docs[0].page_content
    assert docs[0].metadata.get("filename") == "demo.md"


def test_load_txt_gbk(tmp_path: Path):
    p = tmp_path / "gbk.txt"
    p.write_bytes("中文商品说明".encode("gbk"))
    docs = load_file_to_documents(p, "gbk.txt")
    assert "商品" in docs[0].page_content


def test_load_csv(tmp_path: Path):
    p = tmp_path / "sku.csv"
    p.write_text("name,price\n手表,1299\n耳机,699\n", encoding="utf-8")
    docs = load_file_to_documents(p, "sku.csv")
    assert len(docs) >= 1
    assert "手表" in docs[0].page_content or "1299" in docs[0].page_content


def test_split_documents_produces_chunks(tmp_path: Path):
    p = tmp_path / "long.md"
    content = "这是一段商品说明。" * 80
    p.write_text(content, encoding="utf-8")
    docs = load_file_to_documents(p, "long.md")
    chunks = split_documents(docs)
    assert len(chunks) >= 2

"""本地哈希向量。"""

from app.rag.embeddings import LocalHashEmbeddings


def test_embedding_dimension_and_normalization():
    emb = LocalHashEmbeddings(dim=64)
    vec = emb.embed_query("星辰智能手表 游泳")
    assert len(vec) == 64
    # L2 范数应接近 1
    norm = sum(v * v for v in vec) ** 0.5
    assert 0.99 <= norm <= 1.01


def test_embedding_is_deterministic():
    emb = LocalHashEmbeddings(dim=32)
    a = emb.embed_query("云朵降噪耳机")
    b = emb.embed_query("云朵降噪耳机")
    assert a == b


def test_embed_documents_batch():
    emb = LocalHashEmbeddings(dim=16)
    docs = emb.embed_documents(["商品A", "商品B"])
    assert len(docs) == 2
    assert len(docs[0]) == 16
    assert docs[0] != docs[1]


def test_empty_and_english_text():
    emb = LocalHashEmbeddings(dim=16)
    empty = emb.embed_query("")
    eng = emb.embed_query("SKU-WATCH-PRO-2026")
    assert len(empty) == 16
    assert len(eng) == 16

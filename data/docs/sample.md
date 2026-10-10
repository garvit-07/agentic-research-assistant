# Retrieval-Augmented Generation (RAG) — quick notes

RAG combines a retriever with a generator. The retriever finds passages relevant to a
question in an external knowledge base; the language model then answers using those
passages as context. This reduces hallucination and lets answers reflect private or
recent data without retraining the model.

## RAG vs fine-tuning
- RAG is best when knowledge changes often or must be cited.
- Fine-tuning is best for changing style, format, or teaching a narrow skill.
- Many production systems use both: fine-tune for behaviour, RAG for facts.

## Common failure modes
1. Poor chunking splits an answer across chunks.
2. Weak embeddings retrieve irrelevant passages.
3. The generator ignores the retrieved context.
Mitigations: overlap between chunks, hybrid search, re-ranking, and a reviewer step
that checks the answer against the evidence.

class PromptBuilder:
    """
    Builds the system/user prompt sent to the LLM. Deliberately generic -
    this app doesn't know or care what topic a user's documents are
    about, so the prompt only describes the *rule* (answer from the
    given context, don't invent facts), never a specific domain.
    """

    @staticmethod
    def build(question: str, context: str | None = None):

        if context:
            system_prompt = """
You are a helpful assistant that answers questions using only the
user's own uploaded documents.

IMPORTANT RULES:
1. Answer ONLY using the provided context documents.
2. If the answer cannot be found in the context, say so plainly - do not
   guess or use outside knowledge.
3. Be concise but thorough.
4. If multiple documents have relevant information, combine them.
5. Do not invent or assume information that isn't in the context.

Context documents are provided below. Only use information from these documents.
"""

            user_prompt = f"""
Question: {question}

Relevant Documents:
{context}

Please answer the question based ONLY on the documents above.
"""

        else:
            system_prompt = """
You are a helpful assistant that answers questions using only the
user's own uploaded documents. If no relevant document content is
available, say so honestly instead of guessing.
"""
            user_prompt = question

        return system_prompt, user_prompt

from app.services.prompt_builder import PromptBuilder


def test_build_prompt_with_context():

    question = "What is OCR?"

    context = """
    OCR is Optical Character Recognition.
    """

    system_prompt, user_prompt = PromptBuilder.build(
        question,
        context,
    )

    assert isinstance(system_prompt, str)
    assert isinstance(user_prompt, str)

    assert "provided context" in system_prompt
    
    assert "OCR" in user_prompt
    assert question in user_prompt
    


def test_build_prompt_without_context():

    question = "Who created Python?"

    system_prompt, user_prompt = PromptBuilder.build(
        question,
        None,
    )

    assert isinstance(system_prompt, str)
    assert isinstance(user_prompt, str)

    assert "helpful assistant" in system_prompt
    assert user_prompt == question
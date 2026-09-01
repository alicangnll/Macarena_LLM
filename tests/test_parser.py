"""Golden tests locking the parser to the original main.py behaviour."""
from macarena.config import DEEPSEEK_MODEL_ID, GPT2_MODEL_ID
from macarena.parser import extract_command


def test_code_block_with_language_tag():
    result = extract_command("Sure!\n```bash\nls -la\n```")
    assert result.command == "ls -la"
    assert result.note is None


def test_code_block_without_language_tag():
    result = extract_command("```\ncat /etc/hosts\n```")
    assert result.command == "cat /etc/hosts"


def test_code_block_multiline():
    result = extract_command("```\nuname -a\nwhoami\n```")
    assert result.command == "uname -a\nwhoami"


def test_single_backticks():
    result = extract_command("try `pwd` first")
    assert result.command == "pwd"


def test_code_block_takes_priority_over_backticks():
    result = extract_command("maybe `id`, but actually:\n```bash\nhostname\n```")
    assert result.command == "hostname"


def test_common_command_in_plain_prose():
    result = extract_command("You should run ls -la to see the files.")
    assert result.command == "ls -la"


def test_common_command_word_boundary_no_partial_match():
    # 'cat' inside 'category' must not match 'cat /etc/passwd'
    assert extract_command("the category of commands is large").command is None


def test_plain_chat_yields_nothing():
    result = extract_command("Sure! The weather is lovely today.")
    assert result.command is None
    assert result.note is None


def test_false_positive_user_input_echo():
    result = extract_command("```ls -la```", user_input="ls -la", model_id=GPT2_MODEL_ID)
    assert result.command is None
    assert result.note == "Detected command is identical to user input. Sanitized (False Positive)."


def test_internal_instruction_sanitized_for_deepseek():
    result = extract_command("`run Assistant: something`", model_id=DEEPSEEK_MODEL_ID)
    assert result.command is None
    assert result.note == "Detected command contains model's internal instructions. Sanitized."


def test_internal_instruction_kept_for_other_models():
    # The same content is NOT sanitized when the model is not DeepSeek (original behaviour)
    result = extract_command("`run Assistant: something`", model_id=GPT2_MODEL_ID)
    assert result.command == "run Assistant: something"


def test_extraction_runs_on_raw_text_with_prompt_echo():
    # Quirk kept from the original lab: regexes run against the raw generation,
    # which may still contain the echoed prompt.
    raw = "User: hi\n\nAssistant: ```\nwhoami\n```"
    result = extract_command(raw, user_input="hi", model_id=DEEPSEEK_MODEL_ID)
    assert result.command == "whoami"


def test_empty_code_block_is_not_a_command():
    result = extract_command("```\n```")
    assert result.command is None
    assert result.note is None

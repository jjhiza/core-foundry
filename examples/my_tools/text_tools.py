from corefoundry.core import registry


@registry.register(
    description="Convert text to uppercase",
    input_schema={
        "properties": {"text": {"type": "string", "description": "input text"}},
        "required": ["text"],
    },
)
def to_uppercase(text: str) -> str:
    return text.upper()


@registry.register(
    description="Count words in text",
    input_schema={"properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def count_words(text: str) -> int:
    return len(text.split())

from corefoundry.core import registry


def test_register_and_get_callable(tmp_path, monkeypatch):
    # define a tool function inline and register it
    @registry.register(
        name="__test_echo",
        description="Echo tool",
        input_schema={"properties": {"msg": {"type": "string"}}, "required": ["msg"]},
    )
    def echo(msg: str):
        return f"echo:{msg}"

    func = registry.get_callable("__test_echo")
    assert func("hello") == "echo:hello"

def pytest_unwrap(fn):
    unwrap = getattr(fn, "_get_wrapped_function", None)
    if unwrap is not None:
        return unwrap()
    return fn.__pytest_wrapped__.obj

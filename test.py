def decorator(func):
    def wrapper():
        return func()
    return wrapper


def test_func():
    return 1+1

decorator(test_func)
        
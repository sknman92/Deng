def add():
    return 1+2


def test_dec(func):
    def wrapper():
        return func()
    
    return wrapper


@test_dec
result = add()
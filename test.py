def decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result + 1
    return wrapper

@decorator
def test_func(x):
    return x+1

test_func(x=3)



        
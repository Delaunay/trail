
def print_stack(msg='--'):
    import inspect
    stack = inspect.stack()
    stack.reverse()
    print(msg)
    for s in stack:
        print('   ', f'{s.filename.split("/")[-1]:>20}:', s.function)

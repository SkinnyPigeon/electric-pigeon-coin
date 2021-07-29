def unlimited_arguments(*args, **keyword_args):
    print(keyword_args)
    for argument in args:
        print(argument)


unlimited_arguments(1, 2, 3, 4, 5, name='Euan', age=36)
unlimited_arguments(*[1, 2, 3, 4, 5])
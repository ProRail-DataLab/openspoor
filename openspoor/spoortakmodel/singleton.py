class Singleton(object):
    """ helper class to implement the singleton pattern """
    _instances = {}

    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            class_._instances[class_] = super(Singleton, class_).__new__(class_)
        return class_._instances[class_]

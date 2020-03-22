from Speech2Text import Speech2Text, RecognizerSource


class Theta(object):
    __slots__ = ['s2t']

    def __init__(self):
        self.s2t = Speech2Text(RecognizerSource.GOOGLE, filter=True)

    def listen(self):
        self.s2t.active_listen()


def main():
    import speech_recognition as sr
    print(sr.__version__)
    theta = Theta()
    theta.listen()


if __name__ == "__main__":
    main()

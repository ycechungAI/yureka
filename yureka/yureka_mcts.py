from .engine import UCIMCTSEngine
from .utils import print_flush

if __name__ == '__main__':
    print_flush('Yureka!')
    UCIMCTSEngine().listen()

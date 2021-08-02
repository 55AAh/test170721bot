from multiprocessing import Process
from signal import signal, SIGTERM


def rs(n):
    def sc():
        print(f"Caught SIGTERM in {n}")
    signal(SIGTERM, sc)


def main():
    for i in range(5):
        Process(target=pt, args=("Process " + str(i + 1),)).start()
    rs("Main")
    input("Waiting...")


def pt(i):
    rs(str(i))


if __name__ == '__main__':
    main()

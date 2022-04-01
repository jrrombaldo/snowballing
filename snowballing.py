import rispy
from snowballing import threading


if __name__ == "__main__":
    papers = rispy.load(open("test.ris"), skip_unknown_tags=False)
    threading.start_threadpoll(papers)
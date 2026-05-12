import sys
from .app import NexLoadApp

def main():
    app = NexLoadApp()
    sys.exit(app.run(sys.argv))

if __name__ == "__main__":
    main()

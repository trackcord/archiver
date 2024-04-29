import config
from tools import Archiver

if __name__ == "__main__":
    try:
        Archiver().run(config.Worker.token, log_handler=None)
    except KeyboardInterrupt:
        Archiver().close()

import logging
from pathlib import Path


def init_logger(filename=None, logdir=None):
    if not filename:
        filename = Path(__file__).stem
    else:
        filename = Path(filename).stem
    if not logdir:
        logdir = Path(__file__).parent
    else:
        logdir = Path(logdir).absolute()

    lp = "{}.log".format(str(logdir.joinpath(logdir, filename)))
    try:
        logging.basicConfig(filename=lp,
                            filemode='a',
                            force=True,
                            level=logging.INFO,
                            format='%(asctime)s %(filename)s [%(lineno)s] %(levelname)s: %(message)s')

        formatter = logging.Formatter('%(asctime)s %(filename)s [%(lineno)s] %(levelname)s: %(message)s')
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        logger = logging.getLogger(lp)

        if not logger:
            raise Exception("Logging initialization error.")
        result = logger
    except Exception as err:
        raise SystemExit(err)
    return result

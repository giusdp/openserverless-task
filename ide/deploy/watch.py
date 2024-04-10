SKIPDIR = ["virtualenv", "node_modules", "__pycache__"]

import watchfiles
import asyncio
import os.path
import signal

from .deploy import deploy
from .client import serve

def check_and_deploy(change):
    cur_dir_len = len(os.getcwd())+1
    change_type, path = change
    src = path[cur_dir_len:]
    print(f"{change_type}: {src}")
    # only modified
    if change_type != watchfiles.Change.modified: return
    # no directories
    if os.path.isdir(src): return
    # no missing files
    if not os.path.exists(src): return
    # no generated directories
    for dir in src.split("/")[:-1]:
        if dir in SKIPDIR: return
    # no generated files
    if src.endswith(".zip"): return
    # now you can deploy
    deploy(src)

async def redeploy():
    print("redeploy")
    iterator = watchfiles.awatch("packages", recursive=True)
    try:
        async for changes in iterator:
            for change in changes:
                check_and_deploy(change)
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    except:
        print("Exception")

def watch():
    loop = asyncio.get_event_loop()
    task1 = loop.create_task(redeploy())
    #task = asyncio.ensure_future(redeploy())
    task2 = loop.create_task(serve())
    def end_loop():
        print("Ending task.")
        task1.cancel()
        task2.cancel()
    loop.add_signal_handler(signal.SIGTERM, end_loop)

    try:
        loop.run_until_complete(task1)
    except asyncio.CancelledError:
        pass
    finally:
        loop.stop()
        loop.close()

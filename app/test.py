import asynciogit
import time
async def B(b):
    print("HI this is B")
    await asyncio.sleep(5)
    return
def b_call_back(fut):
    print("OIJK")

loop = asyncio.new_event_loop()
fut = loop.create_task(B(3))
fut.add_done_callback(b_call_back)
loop.run_until_complete(fut)


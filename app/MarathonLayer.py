import aiohttp
from aiohttp import web
import asyncio
import json


async def MarathonGet(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            body = await response.json()
            status = response.status
            return (body,status)


async def MarathonPost(url, json_data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_data) as response:
            body = await response.json()
            status = response.status
            return (body, status)

async def MarathonDelte(url, json_data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_data) as response:
            body = await response.json()
            status = response.status
            return (body, status)

async def main(url):
    result = await MarathonGet(url)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main("http://0.0.0.0:8080"))

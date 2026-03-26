from ruzclient.client import RuzClient
import asyncio

client = RuzClient()


async def main():
    async with client:
        response = await client.get("/api/v1/healthz")
        print(response)

        response = await client.protected()
        print(response)

        response = await client.public()
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
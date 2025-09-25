import asyncio
from dotenv import load_dotenv
from src.alm.pipeline.offline import whole_pipeline

load_dotenv()


async def main():
    await whole_pipeline()


if __name__ == "__main__":
    asyncio.run(main())

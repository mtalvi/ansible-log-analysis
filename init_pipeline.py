import asyncio
from dotenv import load_dotenv
from src.alm.pipeline.offline import whole_pipeline
from src.alm.utils.phoenix import register_phoenix

load_dotenv()


async def main():
    await whole_pipeline()


if __name__ == "__main__":
    register_phoenix()
    asyncio.run(main())

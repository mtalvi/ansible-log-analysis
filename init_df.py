import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from alm.pipeline.find_categories import (
    only_generate_step_by_step_solutions,
    whole_pipeline,
)


async def main():
    print(os.getenv("DATABASE_URL"))
    await whole_pipeline()


if __name__ == "__main__":
    asyncio.run(main())

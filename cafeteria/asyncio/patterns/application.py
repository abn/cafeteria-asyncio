import asyncio
from abc import abstractmethod
from typing import NoReturn

from cafeteria.asyncio.commons import handle_signals


class AsyncioGracefulApplication:
    @abstractmethod
    async def main(self) -> NoReturn:
        """
        The main method to execute for the application. The application runs until this
        completes or errors out.
        """
        raise NotImplementedError

    def run(self):
        loop = asyncio.get_event_loop()
        handle_signals(loop)
        asyncio.new
        try:
            loop.run_until_complete(self.main())
        except (asyncio.CancelledError, KeyboardInterrupt):
            loop.stop()
        finally:
            loop.close()

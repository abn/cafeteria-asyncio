import asyncio
from abc import abstractmethod

from cafeteria.asyncio.commons import cancel_tasks_on_termination


class AsyncioGracefulApplication:
    @abstractmethod
    async def main(self) -> None:
        """
        The main method to execute for the application. The application runs until this
        completes or errors out.
        """
        raise NotImplementedError

    def run(self):
        loop = asyncio.get_event_loop()
        cancel_tasks_on_termination(loop)

        try:
            loop.run_until_complete(self.main())
        except (asyncio.CancelledError, KeyboardInterrupt):
            loop.stop()
        finally:
            loop.close()

import asyncio
from abc import abstractmethod
from typing import Any

from cafeteria.asyncio.commons import cancel_tasks_on_termination
from cafeteria.logging import LoggedObject


class AsyncioGracefulApplication(LoggedObject):
    @abstractmethod
    async def main(self) -> Any:
        """
        The main method to execute for the application. The application runs until this
        completes or errors out.
        """
        raise NotImplementedError

    async def __main(self) -> Any:
        cancel_tasks_on_termination()
        return await self.main()

    def run(self, debug: bool = False):
        try:
            self.logger.debug("Starting application")
            return asyncio.run(self.__main(), debug=debug)
        except (asyncio.CancelledError, KeyboardInterrupt):
            self.logger.debug("Application halted")

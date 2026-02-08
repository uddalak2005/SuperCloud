
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging


class BaseAgent(ABC):

    def __init__(self,agent_id:str, agent_type:str,memory_limit:int = 100):

        self.agent_id=agent_id
        self.agent_type=agent_type

        self.context:Dict[str, Any]= {}
        self.memory:List[Dict[str,Any]] = []

        self.memory_limit =memory_limit

        # Logger for agent
        self.logger= logging.getLogger(f"agent.{agent_type}.{agent_id}")

    @abstractmethod
    async def get_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:

        try:
            action = await self.get_action(state)

            self.store_memory({
                "state": state,
                "action": action,
                "timestamp": self.current_timestamp()
            })

            return action

        except Exception as e:
            self.logger.exception("Agent execution failed")

            return {
                "action": "error",
                "parameters": {
                    "agent_id": self.agent_id,
                    "message": str(e)
                }
            }

    # CONTEXT MANAGEMENT
    def update_context(self, new_context: Dict[str,Any], overwrite: bool = True):
        if overwrite:
            self.context.update(new_context)
        else:
            for k, v in new_context.items():
                if k not in self.context:
                    self.context[k] = v

    # MEMORY STORAGE
    def store_memory(self, interaction: Dict[str, Any]):
        self.memory.append(interaction)
        if len(self.memory) > self.memory_limit:
            self.memory.pop(0)

    def current_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def metadata(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type
        }

from src.core.repository import BeanieRepository
from src.services.auth.models import User

from beanie.operators import Or

class AuthRepository(BeanieRepository):

    def __init__(self):
        super().__init__(model_cls=User)

    async def find_by_email_or_username(self, username: str) -> User | None:
        clause = Or(User.username == username, User.email == username)
        return await self.get_one(where=clause)
from src.core.repository import BeanieRepository
from src.services.events.models import Event


class EventRepository(BeanieRepository):

    def __init__(self):
        super().__init__(model_cls=Event)
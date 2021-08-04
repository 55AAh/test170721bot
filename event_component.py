from multiprocessing import Event

from serialized_class import component

__all__ = ["EventComponent"]


@component(init_local=True, serialize=True, deserialize=True)
class EventComponent:
    event: Event

    def sc_init_local(self):
        self.event = Event()

    def sc_serialize(self):
        return self.event

    def sc_deserialize(self, event):
        self.event = event

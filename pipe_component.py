from multiprocessing import Pipe
from multiprocessing.connection import Connection as PipeConnection

from serialized_class import component

__all__ = ["DuplexPipeComponent", "ProducerPipeComponent", "ConsumerPipeComponent"]


@component
class _PipeComponent:
    pipe: PipeConnection
    _remote_pipe: PipeConnection

    def sc_serialize(self) -> tuple[PipeConnection, PipeConnection]:
        return self.pipe, self._remote_pipe

    def sc_deserialize(self, pipes: tuple[PipeConnection, PipeConnection]):
        self._remote_pipe, self.pipe = pipes


@component(init_local=True)
class DuplexPipeComponent(_PipeComponent):
    def sc_init_local(self):
        self.pipe, self._remote_pipe = Pipe()


@component(init_local=True)
class ProducerPipeComponent(_PipeComponent):
    def sc_init_local(self):
        receiver, sender = Pipe(duplex=False)
        self.pipe = receiver
        self._remote_pipe = sender


@component(init_local=True)
class ConsumerPipeComponent(_PipeComponent):
    def sc_init_local(self):
        receiver, sender = Pipe(duplex=False)
        self.pipe = sender
        self._remote_pipe = receiver

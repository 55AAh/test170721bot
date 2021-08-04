import sys
import traceback
from inspect import signature, Signature, Parameter

__all__ = ["component"]


def component(init_local=False, init_remote=False, serialize=False, deserialize=False):
    """ Decorator, makes class a serialized component.

    When used with parentheses, one must mention each ``sc_method`` in component by providing custom method name in
    corresponding keyword argument (or True to search for default name). For example:

    ``@component(init_local=True, serialize="my_dump", deserialize="my_load")``

    Default names: ``sc_init_local``, ``sc_init_remote``, ``sc_serialize``, ``sc_deserialize``.

    Call without parentheses is equal to ``serialize = deserialize = True``.
    """

    cls = None
    frames_count = 5
    if isinstance(init_local, type):
        cls, init_local, init_remote, serialize, deserialize = init_local, False, False, True, True
        frames_count += 1

    def d_arg(name, default): return default if isinstance(name, bool) and name else name

    init_local = d_arg(init_local, "sc_init_local")
    init_remote = d_arg(init_remote, "sc_init_remote")
    serialize = d_arg(serialize, "sc_serialize")
    deserialize = d_arg(deserialize, "sc_deserialize")

    def _wrapper(_cls):
        return _assertion_wrapper(_cls, frames_count, init_local, init_remote, serialize, deserialize)

    if cls:
        return _wrapper(cls)
    return _wrapper


def _assertion_wrapper(cls, frames_count, init_local, init_remote, serialize, deserialize):
    try:
        return _decorate_class(cls, init_local, init_remote, serialize, deserialize)
    except AssertionError as e:
        def _exception_hook(t, v, tb):
            lines_count = len(traceback.extract_tb(tb))
            traceback.print_exception(t, v, tb, lines_count - frames_count)
        sys.excepthook = _exception_hook
        raise e


def _decorate_class(cls, init_local, init_remote, serialize, deserialize):
    def get_check_method(name):
        assert (isinstance(name, str) and len(name) > 0) or isinstance(name, bool), \
            f"Method name must be non-empty string or bool!"
        if not name:
            return None
        assert name in cls.__dict__, f"Required method '{name}' not found!"
        method = cls.__dict__[name]
        assert callable(method), f"Class attribute '{name}' must be callable method!"
        return method

    def get_check_sig(method, name, params_arg=False, params_ret=False):
        if method is None:
            return None

        sig = signature(method)
        params = list(sig.parameters.items())
        assert len(params) >= 1 and \
               params[0][1].kind in [Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD], \
               f"Method '{name}' must have argument (self)!"

        if params_arg:
            assert len(params) >= 2 and \
                   params[1][1].kind in [Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD], \
                   f"Method '{name}' must have second argument (params)!"
            assert len(params) == 2, f"Method '{name}' must have only two arguments (self, params)!"
        else:
            assert len(params) == 1, f"Method '{name}' must have only one argument (self)!"

        if not params_ret:
            assert sig.return_annotation is Signature.empty or sig.return_annotation is None, \
                f"Method '{name}' should not return anything!"

        return sig

    def check_serde_both():
        if serialize or deserialize:
            assert serialize, f"Serialize is required by deserialize!"
            assert deserialize, f"Deserialize is required by serialize!"
            assert list(method_deserialize_signature.parameters.values())[1].annotation == \
                   method_serialize_signature.return_annotation, \
                   f"Deserialize method '{deserialize}' must accept type of serialize method '{serialize}'!"

    method_init_local = get_check_method(init_local)
    method_init_remote = get_check_method(init_remote)
    method_serialize = get_check_method(serialize)
    method_deserialize = get_check_method(deserialize)

    get_check_sig(method_init_local, init_local)
    get_check_sig(method_init_remote, init_remote)
    method_serialize_signature = get_check_sig(method_serialize, serialize, params_ret=True)
    method_deserialize_signature = get_check_sig(method_deserialize, deserialize, params_arg=True)

    check_serde_both()

    class Wrapper(cls, _SerializedComponentsBase):
        if method_init_local:
            def __scw_rec_init_local__(self):
                method_init_local(self)
                super().__scw_rec_init_local__()

        if method_init_remote:
            def __scw_rec_init_remote__(self):
                method_init_remote(self)
                super().__scw_rec_init_remote__()

        if method_serialize and method_deserialize:
            def __scw_rec_serialize__(self):
                p = method_serialize(self)
                sp = super().__scw_rec_serialize__()
                return p, sp

            def __scw_rec_deserialize__(self, p):
                p, sp = p
                method_deserialize(self, p)
                super().__scw_rec_deserialize__(sp)

    cls_qname = cls.__module__ + "." + cls.__name__
    Wrapper.__name__ = Wrapper.__qualname__ = cls_qname
    return Wrapper


class _SerializedComponentsBase:
    def serialize(self):
        s_data = self.__scw_rec_serialize__()
        return _SerializedClass(self.__class__, s_data)

    def __init__(self):
        self.__scw_init_proxy__()
        super().__init__()

    def __scw_init_proxy__(self):
        self.__scw_rec_init_local__()

    def __scw_rec_init_local__(self):
        pass

    def __scw_rec_init_remote__(self):
        pass

    def __scw_rec_serialize__(self):
        return ()

    def __scw_rec_deserialize__(self, s_data):
        assert s_data == (), "serialized data unpacked incorrectly!"


class _SerializedClass:
    def __init__(self, base_class, s_data):
        self._base_class = base_class
        self._s_data = s_data

    def __call__(self):
        s_data = self._s_data

        class Initializer(self._base_class):
            def __scw_init_proxy__(self):
                self.__scw_rec_init_remote__()
                self.__scw_rec_deserialize__(s_data)

        base_class_qname = self._base_class.__module__ + "." + self._base_class.__name__
        Initializer.__name__ = Initializer.__qualname__ = base_class_qname
        return Initializer()

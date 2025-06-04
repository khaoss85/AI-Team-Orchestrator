try:
    from pydantic.fields import PydanticUndefined as Undefined  # type: ignore
    import pydantic.fields as _fields
    setattr(_fields, 'Undefined', Undefined)
except Exception:
    pass

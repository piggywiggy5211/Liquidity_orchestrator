from pydantic import ConfigDict, BaseModel


class Base(BaseModel):
    model_config = ConfigDict(frozen=True)


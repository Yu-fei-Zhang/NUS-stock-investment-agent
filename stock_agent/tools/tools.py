from langchain.tools import tool
from pydantic import BaseModel, Field
class FieldInfo(BaseModel):
    a :int = Field(description="第1个参数")
    b :int = Field(description="第2个参数")
@tool(name_or_callable="add_two_number",description="two number add",args_schema=FieldInfo,return_direct=True)
def add_number(a:int,b:int)->int:
    """两个整数相加"""
    return a + b
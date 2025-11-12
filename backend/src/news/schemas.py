from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str


class NewsSummaryRequestSchema(BaseModel):
    content: str
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class FinamRequest:
    """
    Представление запросу к Finam API
    """
    method: str # "POST"
    url: str # "https://api.finam.ru/v1/accounts/1899011"
    body: Optional[Dict[str, Any]] # {"name": "dshjdjs"}


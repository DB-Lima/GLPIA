import json
import logging
from datetime import datetime, timezone


class FormatoJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        dados = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "nivel": record.levelname,
            "evento": record.getMessage(),
            **getattr(record, "dados", {}),
        }
        return json.dumps(dados, ensure_ascii=False, default=str)


def obter_logger(nome: str = "glpia") -> logging.Logger:
    logger = logging.getLogger(nome)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(FormatoJson())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

import builtins
import sys
from typing import Any


def safe_print(*args: Any, **kwargs: Any) -> None:
    try:
        builtins.print(*args, **kwargs)
    except UnicodeEncodeError:
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        stream = kwargs.get("file", sys.stdout)
        text = sep.join(str(arg) for arg in args) + end
        stream.write(text.encode("ascii", errors="backslashreplace").decode("ascii"))


import re
from urllib.parse import urlparse
from typing import Callable, Dict, List, Tuple, Optional, Pattern
from log import get_logger

# Configure logging
logger = get_logger(__name__)


class Router:
    def __init__(self) -> None:
        self.routes: List[Tuple[Pattern[str], str, Callable, List[str]]] = []

    def route(self, pattern: str, method: str = "GET") -> Callable:
        """
        Decorator to register a route with a specific pattern and method.
        The pattern can contain placeholders in the format {placeholder}.
        """

        param_names = []
        regex_parts = []

        for part in pattern.split("/"):
            if not part:
                regex_parts.append(r"")
                continue

            placeholders = re.findall(r"{([^}]+)}", part)

            if placeholders:
                regex_part = part

                for placeholder in placeholders:
                    param_names.append(placeholder)
                    regex_part = regex_part.replace(f"{{{placeholder}}}", r"(.*)")

                regex_parts.append(regex_part)
            else:
                regex_parts.append(re.escape(part))

        regex_pattern = "/".join(regex_parts) + r"$"
        logger.debug(
            f"Generated regex pattern: {regex_pattern} with params: {param_names}"
        )
        compiled_regex = re.compile(regex_pattern)
        logger.debug(f"Compiled regex: {compiled_regex}")
        logger.debug(f"Registered route: {pattern} with regex: {regex_pattern}")

        def decorator(func: Callable) -> Callable:
            self.routes.append((compiled_regex, method.upper(), func, param_names))
            return func

        return decorator

    def match(
        self, url: str, request_method: str = "GET"
    ) -> Tuple[Optional[Callable], Dict[str, str]]:
        parsed_url = urlparse(url)
        path = parsed_url.path
        logger.debug(f"Matching URL: {url} with path: {path}")
        logger.debug(f"Routes: {self.routes}")
        for regex, method, func, param_names in self.routes:
            match = regex.match(path)
            logger.debug(f"Trying regex: {regex} on path: {path}")
            if match:
                if method != request_method:
                    logger.debug(
                        f"Method mismatch: {method} != {request_method}, skipping route."
                    )
                    continue
                params = {
                    name: match.group(i + 1) for i, name in enumerate(param_names)
                }
                logger.debug(
                    f"Match found: {func.__name__} {method} with params: {params}"
                )
                return func, params

        logger.warning(f"No match found for URL: {url}")
        return None, {}

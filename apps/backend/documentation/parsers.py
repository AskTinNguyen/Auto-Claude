"""
Code Parsers for Documentation Generation
==========================================

Parsers for extracting functions, classes, and documentation from source code.

Features:
- Python AST parsing for functions, classes, methods, and docstrings
- TypeScript regex-based parsing for functions, classes, interfaces, and JSDoc
- Extracts signatures, parameters, return types, and existing documentation
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Information about a function or method."""

    name: str
    signature: str
    params: list[str]
    return_type: str | None
    docstring: str | None
    line_number: int
    is_method: bool = False
    is_async: bool = False


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    bases: list[str]
    docstring: str | None
    line_number: int
    methods: list[FunctionInfo]


class PythonParser:
    """
    Parser for Python source code using AST.

    Extracts functions, classes, methods, and their docstrings for documentation
    generation.
    """

    def __init__(self, file_path: Path):
        """
        Initialize the Python parser.

        Args:
            file_path: Path to the Python source file
        """
        self.file_path = file_path
        self.source_code: str | None = None
        self.tree: ast.Module | None = None

    def parse(self) -> dict[str, list]:
        """
        Parse the Python file and extract documentation-relevant information.

        Returns:
            Dictionary with 'functions' and 'classes' keys containing parsed info

        Raises:
            SyntaxError: If the Python file has syntax errors
            FileNotFoundError: If the file does not exist
        """
        # Read source code
        try:
            self.source_code = self.file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.error(f"File not found: {self.file_path}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode file {self.file_path}: {e}")
            return {"functions": [], "classes": []}

        # Parse AST
        try:
            self.tree = ast.parse(self.source_code, filename=str(self.file_path))
        except SyntaxError as e:
            logger.error(f"Syntax error in {self.file_path}: {e}")
            raise

        # Extract information
        functions = []
        classes = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Skip nested functions and methods (they'll be handled in classes)
                if self._is_top_level_function(node):
                    func_info = self._extract_function_info(node)
                    functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node)
                classes.append(class_info)

        return {"functions": functions, "classes": classes}

    def _is_top_level_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if a function is at module level (not a method or nested function)."""
        if not self.tree:
            return False

        # Check if the function is directly in the module's body
        return node in self.tree.body

    def _extract_function_info(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_method: bool = False
    ) -> FunctionInfo:
        """Extract information from a function or method node."""
        # Get function name
        name = node.name

        # Get parameters
        params = []
        for arg in node.args.args:
            param_str = arg.arg
            if arg.annotation:
                param_str += f": {ast.unparse(arg.annotation)}"
            params.append(param_str)

        # Get return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Build signature
        param_str = ", ".join(params)
        signature = f"def {name}({param_str})"
        if return_type:
            signature += f" -> {return_type}"

        # Get docstring
        docstring = ast.get_docstring(node)

        # Check if async
        is_async = isinstance(node, ast.AsyncFunctionDef)

        return FunctionInfo(
            name=name,
            signature=signature,
            params=params,
            return_type=return_type,
            docstring=docstring,
            line_number=node.lineno,
            is_method=is_method,
            is_async=is_async,
        )

    def _extract_class_info(self, node: ast.ClassDef) -> ClassInfo:
        """Extract information from a class node."""
        # Get class name
        name = node.name

        # Get base classes
        bases = []
        for base in node.bases:
            bases.append(ast.unparse(base))

        # Get docstring
        docstring = ast.get_docstring(node)

        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function_info(item, is_method=True)
                methods.append(method_info)

        return ClassInfo(
            name=name,
            bases=bases,
            docstring=docstring,
            line_number=node.lineno,
            methods=methods,
        )


class TypeScriptParser:
    """
    Parser for TypeScript source code using regex patterns.

    Extracts functions, classes, interfaces, and JSDoc comments for documentation
    generation. Uses regex-based parsing as a lightweight alternative to full AST parsing.
    """

    # Regex patterns for TypeScript parsing
    FUNCTION_PATTERN = re.compile(
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(<[^>]+>)?\s*\(([^)]*)\)\s*(?::\s*([^{;]+))?"
    )
    ARROW_FUNCTION_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*([^=]+))?\s*=>"
    )
    CLASS_PATTERN = re.compile(r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?")
    INTERFACE_PATTERN = re.compile(r"(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([^{]+))?")
    METHOD_PATTERN = re.compile(
        r"(?:public|private|protected)?\s*(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{;]+))?"
    )
    JSDOC_PATTERN = re.compile(r"/\*\*(.*?)\*/", re.DOTALL)

    def __init__(self, file_path: Path):
        """
        Initialize the TypeScript parser.

        Args:
            file_path: Path to the TypeScript source file
        """
        self.file_path = file_path
        self.source_code: str | None = None

    def parse(self) -> dict[str, list]:
        """
        Parse the TypeScript file and extract documentation-relevant information.

        Returns:
            Dictionary with 'functions', 'classes', and 'interfaces' keys containing parsed info

        Raises:
            FileNotFoundError: If the file does not exist
        """
        # Read source code
        try:
            self.source_code = self.file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.error(f"File not found: {self.file_path}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode file {self.file_path}: {e}")
            return {"functions": [], "classes": [], "interfaces": []}

        # Extract information
        functions = self._extract_functions()
        classes = self._extract_classes()
        interfaces = self._extract_interfaces()

        return {"functions": functions, "classes": classes, "interfaces": interfaces}

    def _extract_functions(self) -> list[FunctionInfo]:
        """Extract function declarations from TypeScript code."""
        if not self.source_code:
            return []

        functions = []

        # Find all function declarations
        for match in self.FUNCTION_PATTERN.finditer(self.source_code):
            name = match.group(1)
            generics = match.group(2) or ""
            params_str = match.group(3) or ""
            return_type = match.group(4).strip() if match.group(4) else None

            # Parse parameters
            params = [p.strip() for p in params_str.split(",") if p.strip()]

            # Build signature
            signature = f"function {name}{generics}({params_str})"
            if return_type:
                signature += f": {return_type}"

            # Find JSDoc comment before this function
            docstring = self._find_jsdoc_before_line(match.start())

            # Calculate line number
            line_number = self.source_code[: match.start()].count("\n") + 1

            functions.append(
                FunctionInfo(
                    name=name,
                    signature=signature,
                    params=params,
                    return_type=return_type,
                    docstring=docstring,
                    line_number=line_number,
                    is_method=False,
                    is_async="async" in match.group(0),
                )
            )

        # Find arrow functions
        for match in self.ARROW_FUNCTION_PATTERN.finditer(self.source_code):
            name = match.group(1)
            params_str = match.group(2) or ""
            return_type = match.group(3).strip() if match.group(3) else None

            # Parse parameters
            params = [p.strip() for p in params_str.split(",") if p.strip()]

            # Build signature
            signature = f"const {name} = ({params_str})"
            if return_type:
                signature += f": {return_type}"
            signature += " =>"

            # Find JSDoc comment before this function
            docstring = self._find_jsdoc_before_line(match.start())

            # Calculate line number
            line_number = self.source_code[: match.start()].count("\n") + 1

            functions.append(
                FunctionInfo(
                    name=name,
                    signature=signature,
                    params=params,
                    return_type=return_type,
                    docstring=docstring,
                    line_number=line_number,
                    is_method=False,
                    is_async="async" in match.group(0),
                )
            )

        return functions

    def _extract_classes(self) -> list[ClassInfo]:
        """Extract class declarations from TypeScript code."""
        if not self.source_code:
            return []

        classes = []

        for match in self.CLASS_PATTERN.finditer(self.source_code):
            name = match.group(1)
            base = match.group(2)
            bases = [base] if base else []

            # Find JSDoc comment before this class
            docstring = self._find_jsdoc_before_line(match.start())

            # Calculate line number
            line_number = self.source_code[: match.start()].count("\n") + 1

            # Extract methods (simplified - just look for methods in the class body)
            methods = self._extract_methods_from_class(match.end())

            classes.append(
                ClassInfo(
                    name=name,
                    bases=bases,
                    docstring=docstring,
                    line_number=line_number,
                    methods=methods,
                )
            )

        return classes

    def _extract_interfaces(self) -> list[dict]:
        """Extract interface declarations from TypeScript code."""
        if not self.source_code:
            return []

        interfaces = []

        for match in self.INTERFACE_PATTERN.finditer(self.source_code):
            name = match.group(1)
            extends = match.group(2).strip() if match.group(2) else None

            # Find JSDoc comment before this interface
            docstring = self._find_jsdoc_before_line(match.start())

            # Calculate line number
            line_number = self.source_code[: match.start()].count("\n") + 1

            interfaces.append(
                {
                    "name": name,
                    "extends": extends,
                    "docstring": docstring,
                    "line_number": line_number,
                }
            )

        return interfaces

    def _extract_methods_from_class(self, class_start_pos: int) -> list[FunctionInfo]:
        """Extract methods from a class body (simplified)."""
        if not self.source_code:
            return []

        # Find the class body (between { and })
        # This is simplified and may not handle nested braces perfectly
        brace_count = 0
        class_body_start = -1
        class_body_end = -1

        for i in range(class_start_pos, len(self.source_code)):
            if self.source_code[i] == "{":
                if brace_count == 0:
                    class_body_start = i
                brace_count += 1
            elif self.source_code[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    class_body_end = i
                    break

        if class_body_start == -1 or class_body_end == -1:
            return []

        class_body = self.source_code[class_body_start:class_body_end]
        methods = []

        for match in self.METHOD_PATTERN.finditer(class_body):
            name = match.group(1)
            params_str = match.group(2) or ""
            return_type = match.group(3).strip() if match.group(3) else None

            # Parse parameters
            params = [p.strip() for p in params_str.split(",") if p.strip()]

            # Build signature
            signature = f"{name}({params_str})"
            if return_type:
                signature += f": {return_type}"

            # Find JSDoc comment before this method
            docstring = self._find_jsdoc_before_line(class_body_start + match.start())

            # Calculate line number
            line_number = self.source_code[: class_body_start + match.start()].count("\n") + 1

            methods.append(
                FunctionInfo(
                    name=name,
                    signature=signature,
                    params=params,
                    return_type=return_type,
                    docstring=docstring,
                    line_number=line_number,
                    is_method=True,
                    is_async="async" in match.group(0),
                )
            )

        return methods

    def _find_jsdoc_before_line(self, position: int) -> str | None:
        """Find JSDoc comment immediately before a given position."""
        if not self.source_code or position <= 0:
            return None

        # Look backwards for JSDoc comment
        # Get text before the position
        text_before = self.source_code[:position]

        # Find the last JSDoc comment
        matches = list(self.JSDOC_PATTERN.finditer(text_before))
        if not matches:
            return None

        last_match = matches[-1]

        # Check if the comment is close to the position (within 100 chars of whitespace/newlines)
        between_text = text_before[last_match.end() : position]
        if between_text.strip() == "":
            # Clean up the JSDoc content
            doc_content = last_match.group(1)
            # Remove leading * from each line
            lines = doc_content.split("\n")
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith("*"):
                    line = line[1:].strip()
                if line:
                    cleaned_lines.append(line)
            return "\n".join(cleaned_lines) if cleaned_lines else None

        return None

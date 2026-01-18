"""Sample Python file for testing documentation generation."""


class Calculator:
    def __init__(self, precision=2):
        self.precision = precision
        self.history = []

    def add(self, a, b):
        result = round(a + b, self.precision)
        self.history.append(f"{a} + {b} = {result}")
        return result

    def subtract(self, a, b):
        result = round(a - b, self.precision)
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a, b):
        result = round(a * b, self.precision)
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = round(a / b, self.precision)
        self.history.append(f"{a} / {b} = {result}")
        return result

    def get_history(self):
        return self.history.copy()

    def clear_history(self):
        self.history.clear()


def factorial(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input must be a non-negative integer")

    if n == 0 or n == 1:
        return 1

    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def fibonacci(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input must be a non-negative integer")

    if n == 0:
        return 0
    elif n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

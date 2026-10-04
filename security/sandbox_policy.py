"""Sandbox isolation policy limits"""
class SandboxPolicy:
    MAX_TIMEOUT_SECONDS = 30
    MAX_OUTPUT_BYTES = 1024 * 512
    ALLOW_NETWORK = False
    READONLY_PATHS = ["/etc", "/var", "/usr", "/root"]

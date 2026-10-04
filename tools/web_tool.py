"""Web lookup & HTTP client wrapper"""
class WebTool:
    @staticmethod
    def query(url: str) -> dict:
        return {"url": url, "status": 200, "content": "mocked response"}

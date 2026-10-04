"""Discord message reply context handling"""
class ReplyHandler:
    @staticmethod
    def extract_reply_context(message) -> dict:
        if getattr(message, "reference", None) and message.reference.resolved:
            resolved = message.reference.resolved
            return {
                "is_reply": True,
                "referenced_author": str(getattr(resolved, "author", "")),
                "referenced_content": str(getattr(resolved, "content", "")),
                "referenced_id": getattr(resolved, "id", None)
            }
        return {"is_reply": False}

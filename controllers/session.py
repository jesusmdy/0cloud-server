from controllers.database import Database


class SessionController:
    MAX_SESSIONS = 5

    class Utils:
        @staticmethod
        def count_sessions(user_id: str):
            sessions = Database.keys(f"user:{user_id}:session")
            return len(sessions)

    @staticmethod
    def create_session(user_id: str):
        sessions = SessionController.Utils.count_sessions(user_id)
        if sessions >= SessionController.MAX_SESSIONS:
            return False

        session_id = Database.Utils.gen_uuid()
        created_at = Database.Utils.gen_timestamp()

        mapping = {
            "id": session_id,
            "user_id": user_id,
            "created_at": created_at.isoformat(),
        }

        Database.hmset(f"user:{user_id}:session:{session_id}", mapping=mapping)
        return mapping

    @staticmethod
    def get_session(session_id: str, user_id: str):
        session = Database.hgetall(f"user:{user_id}:session:{session_id}")
        if not session:
            return None
        return Database.Utils.to_dict(session)

    @staticmethod
    def destroy(session_id: str, user_id: str):
        session = SessionController.get_session(session_id, user_id)
        if not session:
            return False
        Database.delete(f"user:{user_id}:session:{session_id}")
        return True

from controllers.database import Database


class FolderController:
    
    class Errors:
        FOLDER_NOT_FOUND = 'Folder not found'
        UNAUTHORIZED_ACCESS = 'Unauthorized access to folder'
        MISSING_REQUIRED_FIELD = 'Missing required field'
    
    def get_folder(folder_id: str, user_id: str) -> dict:
        folder = Database.hgetall(f"user:{user_id}:folders:{folder_id}")
        if folder:
            return Database.Utils.to_dict(folder)
        return None
    
    def create_folder(name: str, user_id: str, parent_id: str = None) -> dict:
        """Create a new folder."""
        folder_id = Database.Utils.gen_uuid()
        created_at = Database.Utils.gen_timestamp()
        
        mapping = {
            "id": folder_id,
            "name": name,
            "parent_id": parent_id or "root",
            "created_at": created_at.isoformat(),
            "user_id": user_id
        }
        Database.hmset(f"user:{user_id}:folders:{folder_id}", mapping=mapping)
        return mapping
    
    def get_direct_folder(folder_id: str) -> dict:
        folder = Database.hgetall(folder_id)
        return Database.Utils.to_dict(folder)

    def list_folders(parent_id: str = None, user_id: str = None) -> list:
        folders = Database.keys(f"user:{user_id}:folders:*")

        children_folders = []

        for folder_id in folders:
            folder = FolderController.get_direct_folder(folder_id)
            if (parent_id is None):
                if folder['parent_id'] == "root":
                    children_folders.append(folder_id)
            if folder['parent_id'] == parent_id:
                children_folders.append(folder_id)
        return [
            FolderController.get_direct_folder(folder_id) for folder_id in children_folders
        ]

    def list_all_folders(user_id: str = None) -> list:
        folders = Database.keys(f"user:{user_id}:folders:*")
        return [FolderController.get_direct_folder(folder_id) for folder_id in folders]
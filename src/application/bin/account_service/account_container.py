import json
import os


class AccountContainer:
    _instance = None
    _user_map: dict
    _file_path: str

    def __new__(cls, file_path=None):
        if not cls._instance:
            cls._instance = super(AccountContainer, cls).__new__(cls)
            cls._instance._user_map = {}
            if file_path:
                cls._instance.initialize(file_path)
        return cls._instance

    def initialize(self, file_path):
        """
        Initializes the container with a JSON file path.
        Loads the existing mappings from the file if it exists.
        """
        self._file_path = file_path

        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                try:
                    data = json.load(file)
                    self._user_map = {item["cognito_sub"]: item["nick"] for item in data}
                except (json.JSONDecodeError, KeyError):
                    self._user_map = {}

    def get_nick(self, user_id, default=None):
        """Retrieves the nick for the given user ID."""
        return self._user_map.get(user_id, default)


# Example usage
# if __name__ == "__main__":
#     # Create the singleton instance
#     user_map = AccountContainer()

#     # Initialize it with the JSON file path
#     user_map.initialize("user_map.json")

#     # Example data to add
#     user_map.add_user("8344d822-2011-70e8-ae18-8090e99bc04a", "michal.hornak1+metamasks@qorpo.world")

#     # Retrieve a nick for a user ID
#     nick = user_map.get_nick("8344d822-2011-70e8-ae18-8090e99bc04a")
#     print(f"Nick for user: {nick}")

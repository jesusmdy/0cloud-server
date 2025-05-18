class KeyController:
  class Load:
    def jwt():
      return open("files.key", "rb").read()
    def files():
      return open("files.key", "rb").read()
    def users():
      return open("users.key", "rb").read()
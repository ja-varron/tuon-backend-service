class User:
  def __init__(self, user_id: str, email: str, role: str = 'admin' | 'instructor' | 'student'):
    self.user_id = user_id
    self.email = email
    self.role = role

  def create(self):
    pass

  
class Vector3:
   def __init__(self, x=0, y=0, z=0):
       self.x = x
       self.y = y
       self.z = z

   def __str__(self):
       return "Vector3({}, {}, {})".format(self.x, self.y, self.z)

   def __repr__(self):
       return "Vector3({}, {}, {})".format(self.x, self.y, self.z)

   def __eq__(self, other):
       return self.x == other.x and self.y == other.y and self.z == other.z

   def __add__(self, other):
       return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

   def __sub__(self, other):
       return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

   def __mul__(self, scalar):
       return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

   def __rmul__(self, scalar):
       return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

   def magnitude(self):
       return ((self.x ** 2) + (self.y ** 2) + (self.z ** 2)) ** 0.5

   def normalize(self):
       mag = self.magnitude()
       if mag == 0:
           return Vector3(0, 0, 0)
       return Vector3(self.x / mag, self.y / mag, self.z / mag)

   def dot(self, other):
       return self.x * other.x + self.y * other.y + self.z * other.z

   def cross(self, other):
       return Vector3(
           self.y * other.z - self.z * other.y,
           self.z * other.x - self.x * other.z,
           self.x * other.y - self.y * other.x)

   def project_onto(self, other):
       dot = self.dot(other)
       mag_other = other.magnitude()
       return Vector3(dot * other.x / mag_other, dot * other.y / mag_other, dot * other.z / mag_other)

   def reflect(self, normal):
       dot = self.dot(normal)
       return self - normal * 2 * dot
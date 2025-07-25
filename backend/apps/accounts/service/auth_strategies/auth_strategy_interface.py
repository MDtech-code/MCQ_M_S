from abc import ABC,abstractmethod



class AuthStrategy(ABC):
    @abstractmethod
    def authenticate(self, request, data):
        pass

    @abstractmethod
    def generate_token(self, user):
        pass
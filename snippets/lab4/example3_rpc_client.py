import os
from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define DIRECTORY relative to the current script location
DIRECTORY = os.path.join(CURRENT_DIR, "..", "..", "userTokens")
def save_tokenToPath(token: Token, path: str):
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)
    filename = os.path.join(DIRECTORY, f"{path}.json")
    with open(filename, 'w') as f:
        f.write(serialize(token))

 
    
@staticmethod
def read_tokenFromPath(path: str):
    filename = os.path.join(DIRECTORY, f"{path}.json")
    if not os.path.exists(DIRECTORY):
        raise FileNotFoundError(f"Directory '{DIRECTORY}' does not exist")
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File '{filename}' does not exist in the specified directory")
    with open(filename, 'r') as f:
        return deserialize(f.read())

class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, *args, metadata=None):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, metadata)
            print('# Marshalling', request, 'towards', "%s:%d" % client.remote_address)
            request = serialize(request)
            print('# Sending message:', request.replace('\n', '\n# '))
            client.send(request)
            response = client.receive()
            print('# Received message:', response.replace('\n', '\n# '))
            response = deserialize(response)
            assert isinstance(response, Response)
            print('# Unmarshalled', response, 'from', "%s:%d" % client.remote_address)
            if response.error:
                raise RuntimeError(response.error)
            if name == 'authenticate' and isinstance(response.result, Token):
                self.token = response.result
                
            return response.result
        finally:
            client.close()
            print('# Disconnected from %s:%d' % client.remote_address)


class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)

    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, id: str, token: Token) -> User:
        return self.rpc('get_user', id, metadata=token)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)

class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        return self.rpc('authenticate', credentials, duration)

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)

if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    # Test with user whose role is USER
    try_user = User(
        username='guo jiahao',
        emails={'jiahao.guo@studio.unibo.it'},
        full_name='Jiahao Guo',
        role=Role.USER,
        password='my secret password',
    )

    user_db = RemoteUserDatabase(address(sys.argv[1]))
    user_auth = RemoteAuthenticationService(address(sys.argv[1]))
         
    # Trying to get a user that does not exist should raise a KeyError because the user is not authenticated
    try:
        user_db.get_user('gciatto',None)
    except RuntimeError as e:
        # assert 'User with ID gciatto not found' in str(e)
        print(e)

    # Adding a novel user should work
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        print(f"Error occurred: {str(e)}")

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        print(f"Error occurred: {str(e)}")

    # Authenticating with the correct credentials should work
    try:
        token = user_auth.authenticate(gc_credentials_ok[0])
        save_tokenToPath(token, gc_user.username)
    except RuntimeError as e:
        print(f"Authentication error: {str(e)}")

    # Authenticating with the wrong credentials should raise an exception
    try:
        token = user_auth.authenticate(gc_credentials_wrong)
        save_tokenToPath(token, gc_user.username)
    except RuntimeError as e:
        print(f"Authentication failed: {str(e)}")
    
    # Trying to get a user after authentication now should work
    try:
        user_db.get_user('gciatto',token)
    except RuntimeError as e:
        print(f"Error occurred: {str(e)}")
        
    # Trying to get a user reading from the file should work
    try:
        user_db.get_user('gciatto',read_tokenFromPath(gc_user.username))
    except RuntimeError as e:
        print(f"Error occurred: {str(e)}")
        
     # Trying to add another user whose role is USER
    try:
        user_db.add_user(try_user)
    except RuntimeError as e:
        print(f"Error occurred: {str(e)}")
        
    try:
        user_db.get_user('guo jiahao',None)
    except RuntimeError as e:
        print(f"Error occurred: {str(e)}")
        
    # Authenticating with USER role to get the user details should not work
    try:
        token = user_auth.authenticate(Credentials(try_user.username, try_user.password))
        user_db.get_user('guo jiahao', token)
    except RuntimeError as e:
        print(f"Authentication error: {str(e)}")
        
    # Getting a user that exists should work
    # assert user_db.get_user('gciatto') == gc_user.copy(password=None)

    # # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    # for gc_cred in gc_credentials_ok:
    #     assert user_db.check_password(gc_cred) == True

    # # Checking credentials should fail if the password is wrong
    # assert user_db.check_password(gc_credentials_wrong) == False
    
    # # Try to get a user that already exists but without authentication
    # try:
    #     user_db.get_user('gciatto')
    # except RuntimeError as e:
    #     assert 'You must authenticate first' in str(e)

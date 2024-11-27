
import os
from snippets.lab4.example1_presentation import serialize, deserialize
from .example3_rpc_client import *
import argparse
import sys
@staticmethod
def save_tokenToPath(token :Token, path:str):
    with open(path, 'w') as f:
        f.write(serialize(token))

@staticmethod
def read_tokenFromPath(path : str):
    with open(path, 'r') as f:
        return deserialize(f.read())
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check','authenticate','validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t',type=str ,help='Token')
    parser.add_argument('--path', '-pt', help='Path of token file')
  
    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    user_auth = RemoteAuthenticationService(args.address)

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                if not args.path:
                    raise ValueError("Path to token file is required")
                credentials = Credentials(ids[0], args.password)
                token = user_auth.authenticate(credentials)
                print(token)
                save_tokenToPath(token, args.path)
            case 'validate':
                if not args.token and not args.path:
                    raise ValueError("Token or path is required")
                if args.path and os.path.exists(args.path):
                    token = read_tokenFromPath(args.path)
                elif args.token:
                    token = deserialize(args.token)
                print(user_auth.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)

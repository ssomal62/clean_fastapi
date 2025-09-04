from .container import MainContainer


container = MainContainer()

def get_user_service():
    return container.user_service()

def get_note_service():
    return container.note.note_service()

def get_auth_service():
    return container.auth.auth_service()


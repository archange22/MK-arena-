from config.permissions import can_manage_nova

def can_execute_staff_action(member):
    return can_manage_nova(member)

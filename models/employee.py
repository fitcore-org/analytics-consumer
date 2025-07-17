from dataclasses import dataclass

@dataclass
class Employee:
    id: str
    name: str
    email: str
    cpf: str
    birth_date: object
    phone: str
    role: str
    role_description: str
    active: bool
    hire_date: object
    termination_date: object
    registration_date: object
    profile_url: str
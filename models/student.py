from dataclasses import dataclass

@dataclass
class Student:
    id: str
    name: str
    email: str
    cpf: str
    birth_date: object
    phone: str
    plan_type: str
    plan_description: str
    weight: float
    height: float
    bmi: float
    active: bool
    registration_date: object
    profile_url: str
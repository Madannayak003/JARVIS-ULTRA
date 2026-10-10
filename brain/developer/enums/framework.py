"""
Frameworks
"""

from enum import Enum


class Framework(str, Enum):
    FLASK = "Flask"
    DJANGO = "Django"
    FASTAPI = "FastAPI"
    REACT = "React"
    VUE = "Vue"
    ANGULAR = "Angular"
    NEXTJS = "Next.js"
    EXPRESS = "Express"
    NONE = "None"